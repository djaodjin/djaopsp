# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

import logging
from collections import OrderedDict, namedtuple
from datetime import datetime, timedelta

import monotonic
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connection, connections, transaction
from django.db.models import Max, Sum
from django.db.utils import DEFAULT_DB_ALIAS
from django.http import Http404
from django.utils import six
from django.utils.dateparse import parse_datetime
from django.utils.timezone import utc
from deployutils.apps.django import mixins as deployutils_mixins
from pages.models import PageElement, RelationShip
from pages.mixins import TrailMixin
from rest_framework.generics import get_object_or_404
from survey.models import (Answer, Choice, Campaign, EnumeratedQuestions,
    Metric, Sample, Unit)
from survey.utils import get_account_model

from .models import (Consumption, get_score_weight, _show_query_and_result,
    get_scored_answers)
from .scores import populate_rollup, push_improvement_factors
from .serializers import ConsumptionSerializer


LOGGER = logging.getLogger(__name__)


class AccountMixin(deployutils_mixins.AccountMixin):

    account_queryset = get_account_model().objects.all()
    account_lookup_field = 'slug'
    account_url_kwarg = 'organization'


class PermissionMixin(deployutils_mixins.AccessiblesMixin):

    redirect_roles = ['manager', 'contributor']

    @staticmethod
    def get_roots():
        return PageElement.objects.get_roots().filter(tag__contains='industry')


class ContentCut(object):
    """
    Visitor that cuts down a content tree whenever TAG_PAGEBREAK is encountered.
    """
    TAG_PAGEBREAK = 'pagebreak'

    def __init__(self, tag=TAG_PAGEBREAK, depth=1):
        self.depth = depth
        self.match = tag

    def enter(self, tag):
        depth = self.depth
        self.depth = self.depth + 1
        return not (depth > 1 and tag and self.match in tag)

    def leave(self, attrs, subtrees):
        #pylint:disable=unused-argument
        self.depth = self.depth - 1
        return True


class TransparentCut(object):

    def __init__(self, depth=1):
        self.depth = depth

    def enter(self, tag):
        #pylint:disable=unused-argument
        self.depth = self.depth + 1
        return True

    def leave(self, attrs, subtrees):
        self.depth = self.depth - 1
        # `transparent_to_rollover` is meant to speed up computations
        # when the resulting calculations won't matter to the display.
        # We used to compute decide `transparent_to_rollover` before
        # the recursive call (see commit c421ca5) but it would not
        # catch the elements tagged deep in the tree with no chained
        # presentation.
        tag = attrs.get('tag', "")
        attrs['transparent_to_rollover'] = not (
            tag and settings.TAG_SCORECARD in tag)
        for subtree in six.itervalues(subtrees):
            tag = subtree[0].get('tag', "")
            if tag and settings.TAG_SCORECARD in tag:
                attrs['transparent_to_rollover'] = False
                break
            if not subtree[0].get('transparent_to_rollover', True):
                attrs['transparent_to_rollover'] = False
                break
        return not attrs['transparent_to_rollover']


class BreadcrumbMixin(PermissionMixin, TrailMixin):

    breadcrumb_url = 'summary'
    report_title = 'Best Practices Report'

    enable_report_queries = True

    @property
    def survey(self):
        if not hasattr(self, '_survey'):
            if self.kwargs.get(
                    'path', "").startswith('/sustainability-framework'):
                slug = 'framework'
            else:
                slug = 'assessment'
            self._survey = get_object_or_404(Campaign.objects.all(), slug=slug)
        return self._survey

    @property
    def default_metric_id(self):
        if not hasattr(self, '_default_metric_id'):
            # XXX relies on Metric.slug == Campaign.slug
            self._default_metric_id = Metric.objects.get(
                slug=self.survey.slug).pk
        return self._default_metric_id

    @property
    def breadcrumbs(self):
        if not hasattr(self, '_breadcrumbs'):
            self._breadcrumbs = self.get_breadcrumbs(self.kwargs.get('path'))
        return self._breadcrumbs

    def _start_time(self):
        if not self.enable_report_queries:
            return
        self.start_time = monotonic.monotonic()

    def _report_queries(self, descr=None):
        if not self.enable_report_queries:
            return
        if not hasattr(self, 'start_time'):
            return
        end_time = monotonic.monotonic()
        if descr is None:
            descr = ""
        nb_queries = 0
        duration = timedelta()
        for conn in connections.all():
            nb_queries += len(conn.queries)
            for query in conn.queries:
                convert = datetime.strptime(query['time'], "%S.%f")
                duration += timedelta(
                    0, convert.second, convert.microsecond)
                    # days, seconds, microseconds
        LOGGER.debug("(elapsed: %.2fs) %s: %s for %d SQL queries",
            (end_time - self.start_time), descr, duration, nb_queries)

    @staticmethod
    def get_prefix():
        return None

    def get_breadcrumb_url(self, path):
        organization = self.kwargs.get('organization')
        if organization:
            return reverse("%s_organization" % self.breadcrumb_url,
                args=(organization, path,))
        return reverse(self.breadcrumb_url, args=(path,))

    def build_content_tree(self, roots=None, prefix=None, cut=ContentCut()):
        #pylint:disable=too-many-locals
        """
        Returns a tree from a list of roots.

        code::

            build_content_tree(PageElement<boxes-and-enclosures>)
            {
              "/boxes-and-enclosures": [
                { ... data for node ... },
                {
                  "boxes-and-enclosures/management": [
                  { ... data for node ... },
                  {}],
                  "boxes-and-enclosures/design": [
                  { ... data for node ... },
                  {}],
                }]
            }
        """
        # Implementation Note: The structure of the content in the database
        # is stored in terms of `PageElement` (node) and `Relationship` (edge).
        # We use a breadth-first search algorithm here such as to minimize
        # the number of queries to the database.
        if not prefix:
            prefix = ''
        elif not prefix.startswith("/"):
            prefix = "/" + prefix
        if roots is None:
            roots = self.get_roots()

        results = OrderedDict()
        pks_to_leafs = {}
        for root in roots:
            if isinstance(root, PageElement):
                slug = root.slug
                orig_element_id = root.pk
                title = root.title
                tag = root.tag
            else:
                slug = root.get('slug', root.get('dest_element__slug'))
                orig_element_id = root.get('dest_element__pk')
                title = root.get('dest_element__title')
                tag = root.get('dest_element__tag')
            if prefix.endswith("/" + slug):
                # Workaround because we sometimes pass a prefix and sometimes
                # a path `from_root`.
                base = prefix
            else:
                base = prefix + "/" + slug
            result_node = {
                'path': base,
                'slug': slug,
                'title': title,
                'tag': tag,
                'score_weight': get_score_weight(tag), # XXX missing % calc?
            }
            pks_to_leafs[orig_element_id] = (result_node, OrderedDict())
            results.update({base: pks_to_leafs[orig_element_id]})

        edges = RelationShip.objects.filter(
            orig_element__in=list(roots)).values(
            'orig_element_id', 'dest_element_id', 'rank',
            'dest_element__slug', 'dest_element__title',
            'dest_element__tag').order_by('rank', 'pk')
        while edges:
            next_pks_to_leafs = {}
            total_score_weight = 0
            for edge in edges:
                tag = edge.get('dest_element__tag')
                total_score_weight += get_score_weight(tag)
            normalize_children = ((1.0 - 0.01) < total_score_weight
                and total_score_weight < (1.0 + 0.01))
            for edge in edges:
                slug = edge.get('slug', edge.get('dest_element__slug'))
                orig_element_id = edge.get('orig_element_id')
                dest_element_id = edge.get('dest_element_id')
                title = edge.get('dest_element__title')
                tag = edge.get('dest_element__tag')
                base = pks_to_leafs[orig_element_id][0]['path'] + "/" + slug
                score_weight = get_score_weight(tag)
                result_node = {
                    'path': base,
                    'slug': slug,
                    'title': title,
                    'tag': tag,
                    'score_weight': score_weight,
                }
                if normalize_children:
                    result_node.update({
                        'score_percentage': int(score_weight * 100)})
                pivot = (result_node, OrderedDict())
                pks_to_leafs[orig_element_id][1].update({base: pivot})
                if cut is None or cut.enter(tag):
                    next_pks_to_leafs[dest_element_id] = pivot
            pks_to_leafs = next_pks_to_leafs
            next_pks_to_leafs = {}
            edges = RelationShip.objects.filter(
                orig_element_id__in=pks_to_leafs.keys()).values(
                'orig_element_id', 'dest_element_id', 'rank',
                'dest_element__slug', 'dest_element__title',
                'dest_element__tag').order_by('rank', 'pk')
        return results

    def get_leafs(self, rollup_tree=None, path=None):
        """
        Returns all leafs from a rollup tree.

        The dictionnary indexed by paths is carefully constructed such
        that values are aliases into the rollup tree (not copies). It is
        thus possible to update leafs in the roll up tree by updating values
        in the dictionnary returned by this function.
        """
        if rollup_tree is None:
            rollup_tree = self.build_aggregate_tree()
        if path is None:
            path = ''
        elif not path.startswith("/"):
            path = "/" + path

        if not rollup_tree[1].keys():
            return {path: rollup_tree}

        text = PageElement.objects.filter(
            slug=rollup_tree[0]['slug']).values('text').first()
        if text and text['text']:
            rollup_tree[0].update(text)
        leafs = OrderedDict({})
        for key, level_detail in six.iteritems(rollup_tree[1]):
            leafs.update(self.get_leafs(level_detail, path=key))
        return leafs

    def get_next_rank(self):
        last_rank = EnumeratedQuestions.objects.filter(
            campaign=self.survey).aggregate(Max('rank')).get('rank__max', 0)
        return 0 if last_rank is None else last_rank + 1

    def get_serializer_context(self):
        context = super(BreadcrumbMixin, self).get_serializer_context()
        context.update({'campaign': self.survey})
        return context

    def decorate_leafs(self, leafs):
        for path, vals in six.iteritems(leafs):
            consumption = Consumption.objects.filter(path=path).first()
            if consumption:
                vals[0]['consumption'] \
                    = ConsumptionSerializer(context={'campaign': self.survey
                    }).to_representation(consumption)
            else:
                vals[0]['consumption'] = None
                text = PageElement.objects.filter(
                    slug=vals[0]['slug']).values('text').first()
                if text and text['text']:
                    vals[0].update(text)

    def _build_tree(self, root, path, cut=ContentCut()):
        # hack to remove slug that will be added.
        prefix = '/'.join(path.split('/')[:-1])
        try:
            # Convoluted way to pass a Node or a list of Node as arguments.
            roots = root
            _ = iter(roots)
        except TypeError:
            roots = [root]
        rollup_trees = self._cut_tree(self.build_content_tree(
            roots, prefix=prefix, cut=cut), cut=cut)
        try:
            # We only have one root by definition of the function signature.
            rollup_tree = next(six.itervalues(rollup_trees))
        except StopIteration:
            LOGGER.exception("build_tree([%s], path=%s, cut=%s)"\
                " leaves an empty rollup tree", root, path, cut.__class__)
            rollup_tree = ({'slug': ""}, {})
        leafs = self.get_leafs(rollup_tree)
        self._report_queries("[_build_tree] leafs loaded")
        self.decorate_leafs(leafs)
        self._report_queries("[_build_tree] leafs populated")
        return rollup_tree

    def _cut_tree(self, roots, cut=None):
        """
        Cuts subtrees out of *roots* when they match the *cut* parameter.
        *roots* has a format compatible with the data structure returned
        by `build_content_tree`.

        code::
            {
              "/boxes-and-enclosures": [
                { ... data for node ... },
                {
                  "boxes-and-enclosures/management": [
                  { ... data for node ... },
                  {}],
                  "boxes-and-enclosures/design": [
                  { ... data for node ... },
                  {}],
                }]
            }
        """
        for node_path, node in list(six.iteritems(roots)):
            self._cut_tree(node[1], cut=cut)
            if cut and not cut.leave(node[0], node[1]):
                del roots[node_path]
        return roots

    def decorate_with_breadcrumbs(self, rollup_tree,
                                  icon=None, tag=None, breadcrumbs=None):
        """
        When this method returns each node in the rollup_tree will have
        and icon and breadcumbs attributes. If a node does not have or
        has an empty tag attribute, it will be set to the value of the
        first parent's tag which is meaningful.
        """
        if not rollup_tree:
            # `rollup_tree` will be `None` when a user attempts to print
            # an empty list of improvement.
            return
        title = rollup_tree[0].get('title', "")
        if isinstance(breadcrumbs, list) and title:
            breadcrumbs.append(title)
        elif rollup_tree[0].get('slug', "").startswith('sustainability-'):
            breadcrumbs = []
        icon_candidate = rollup_tree[0].get('text', "")
        if icon_candidate and icon_candidate.endswith('.png'):
            icon = icon_candidate
        tag_candidate = rollup_tree[0].get('tag', "")
        if tag_candidate:
            tag = tag_candidate
        rollup_tree[0].update({
            'breadcrumbs':
                list(breadcrumbs) if breadcrumbs else [title],
            'icon': icon,
            'icon_css': 'grey' if (tag and 'management' in tag) else 'orange'
        })
        for node in six.itervalues(rollup_tree[1]):
            self.decorate_with_breadcrumbs(node, icon=icon, tag=tag,
                breadcrumbs=breadcrumbs)
        if breadcrumbs:
            breadcrumbs.pop()

    def get_breadcrumbs(self, path):
        #pylint:disable=too-many-locals
        trail = self.get_full_element_path(path)
        if not trail:
            return "", []

        from_root = "/" + "/".join([element.slug for element in trail])

        self.icon = None
        for element in trail:
            if element.text.endswith('.png'):
                self.icon = element

        trail_idx = 0
        results = []
        parts = path.split('/')
        if not parts[0]:
            parts.pop(0)
        for idx, part in enumerate(parts):
            node = None
            missing = []
            while trail_idx < len(trail) and trail[trail_idx].slug != part:
                missing += [trail[trail_idx]]
                trail_idx += 1
            if trail_idx >= len(trail):
                raise Http404("Cannot find '%s' in trail '%s'" %
                    (part, " > ".join([elm.title for elm in trail])))
            node = trail[trail_idx]
            trail_idx += 1
            url = "/" + "/".join(parts[:idx + 1])
            if missing and results:
                results[-1][1] += "#%s" % missing[0]
            results += [[node, url]]

        for crumb in results:
            anchor_start = crumb[1].find('#')
            if anchor_start > 0:
                path = crumb[1][:anchor_start]
                anchor = crumb[1][anchor_start + 1:]
            else:
                path = crumb[1]
                anchor = ""
            base_url = self.get_breadcrumb_url(path)
            if anchor:
                base_url += ("?active=%s" % anchor)
            crumb.append(base_url)
                # XXX Do we add the Organization in the path
                # for assessment to summary and back?
        return from_root, results

    def get_context_data(self, **kwargs):
        context = super(BreadcrumbMixin, self).get_context_data(**kwargs)
        from_root, trail = self.breadcrumbs
        parts = from_root.split('/')
        root_prefix = '/'.join(parts[:-1]) if len(parts) > 1 else ""
        path = kwargs.get('path', "")
        context.update({
            'path': path,
            'root_prefix': root_prefix,
            'breadcrumbs': trail,
            'active': self.request.GET.get('active', "")})
        urls = {
            'api_scorecard_disable': reverse(
                'api_scorecard_disable', args=("/",)),
            'api_scorecard_enable': reverse(
                'api_scorecard_enable', args=("/",)),
            'api_best_practices': reverse('api_detail', args=("",)),
            'api_mirror_node': reverse('api_mirror_detail', args=("",)),
            'api_move_node': reverse('api_move_detail', args=("",)),
            'api_columns': reverse('api_column_base'),
            'api_consumptions': reverse('api_consumption_base'),
            'api_weights': reverse('api_score_base'),
            'api_page_elements': reverse('page_elements'),
            'best_practice_base': self.get_breadcrumb_url(
                path)
        }
        active_section = ""
        if self.request.GET.get('active', ""):
            active_section += "?active=%s" % self.request.GET.get('active')
        if 'organization' in context:
            urls.update({
                'api_improvements': reverse('api_improvement_base',
                    args=(context['organization'],)),
                'assess': reverse('envconnect_assess_organization',
                    args=(context['organization'], path)),
                'benchmark': reverse('benchmark_organization',
                    args=(context['organization'], path)),
                'improve': reverse('envconnect_improve_organization',
                    args=(context['organization'], path)),
                'summary': reverse('summary_organization',
                    args=(context['organization'], path)),
            })
        else:
            urls.update({
                'assess': reverse('envconnect_assess', args=(path,)),
                'benchmark': reverse('benchmark', args=(path,)),
                'improve': reverse('envconnect_improve', args=(path,)),
                'summary': reverse('summary', args=(path,)),
            })
        if self.__class__.__name__ == 'DetailView':
            urls.update({'context_base': urls['summary']})
        elif self.__class__.__name__ == 'AssessmentView':
            urls.update({'context_base': urls['assess']})
        elif self.__class__.__name__ == 'ImprovementView':
            urls.update({'context_base': urls['improve']})
        self.update_context_urls(context, urls)
        return context


class ExcludeDemoSample(object):

    def _get_filter_out_testing(self):
        # List of response ids that are only used for demo purposes.
        if self.request.user.username in settings.TESTING_USERNAMES:
            return []
        return settings.TESTING_RESPONSE_IDS


class ReportMixin(ExcludeDemoSample, BreadcrumbMixin, AccountMixin):
    """
    Loads assessment and improvement for an organization.
    """

    @property
    def sample(self):
        return self.assessment_sample

    @property
    def assessment_sample(self):
        if not hasattr(self, '_assessment_sample'):
            self._assessment_sample = Sample.objects.filter(
                extra__isnull=True,
                survey=self.survey,
                account=self.account).order_by('-created_at').first()
        return self._assessment_sample

    def get_or_create_assessment_sample(self):
        # We create the sample if it does not exists.
        with transaction.atomic():
            if self.assessment_sample is None:
                self._assessment_sample = Sample.objects.create(
                    survey=self.survey, account=self.account)

    def get_included_samples(self):
        results = []
        if self.assessment_sample:
            results += [self.assessment_sample]
        return results

    @staticmethod
    def populate_account(accounts, agg_score, agg_key='account_id'):
        """
        Populate the *accounts* dictionnary with scores in *agg_score*.

        *agg_score* is a tuple (account_id, sample_id, is_planned, numerator,
        denominator, last_activity_at, nb_answers, nb_questions)
        """
        is_completed = agg_score.is_completed
        is_planned = agg_score.is_planned
        numerator = agg_score.numerator
        denominator = agg_score.denominator
        created_at = agg_score.last_activity_at
        if created_at:
            if isinstance(created_at, six.string_types):
                created_at = parse_datetime(created_at)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=utc)
        if agg_key == 'last_activity_at':
            account_id = created_at
        else:
            account_id = getattr(agg_score, agg_key)
        nb_answers = getattr(agg_score, 'nb_answers', None)
        if nb_answers is None:
            # Putting the following statement in the default clause will lead
            # to an exception since `getattr(agg_score, 'answer_id')` will be
            # evaluated first.
            nb_answers = 0 if getattr(agg_score, 'answer_id') is None else 1
        nb_questions = getattr(agg_score, 'nb_questions', 1)
        if not account_id in accounts:
            accounts[account_id] = {}
        if is_planned:
            accounts[account_id].update({
                'improvement_numerator': numerator,
                'improvement_denominator': denominator,
                'improvement_completed': is_completed,
            })
            if not 'nb_answers' in accounts[account_id]:
                accounts[account_id].update({
                    'nb_answers': nb_answers})
            if not 'nb_questions' in accounts[account_id]:
                accounts[account_id].update({
                    'nb_questions': nb_questions})
            if not 'created_at' in accounts[account_id]:
                accounts[account_id].update({
                    'created_at': created_at})
        else:
            accounts[account_id].update({
                'nb_answers': nb_answers,
                'nb_questions': nb_questions,
                'assessment_completed': is_completed,
                'created_at': created_at
            })
            if nb_questions == nb_answers:
                accounts[account_id].update({
                    'numerator': numerator,
                    'denominator': denominator})

    @staticmethod
    def _is_sqlite3(db_key=None):
        if db_key is None:
            db_key = DEFAULT_DB_ALIAS
        return connections.databases[db_key]['ENGINE'].endswith('sqlite3')

    def populate_leaf(self, prefix, attrs, answers, agg_key='account_id'):
        """
        Populate all leafs with aggregated scores.
        """
        #pylint:disable=too-many-locals,unused-argument
        agg_scores = """SELECT account_id, sample_id, is_planned,
    SUM(numerator) AS numerator,
    SUM(denominator) AS denominator,
    MAX(last_activity_at) AS last_activity_at,
    COUNT(answer_id) AS nb_answers,
    COUNT(*) AS nb_questions,
    %(bool_agg)s(is_completed) AS is_completed
FROM (%(answers)s) AS answers
GROUP BY account_id, sample_id, is_planned;""" % {
    'answers': answers,
    'bool_agg': 'MAX' if self._is_sqlite3() else 'bool_or',
}
        _show_query_and_result(agg_scores)
        with connection.cursor() as cursor:
            cursor.execute(agg_scores, params=None)
            col_headers = cursor.description
            agg_score_tuple = namedtuple(
                'AggScoreTuple', [col[0] for col in col_headers])
            for agg_score in cursor.fetchall():
                agg_score = agg_score_tuple(*agg_score)
                if not 'accounts' in attrs:
                    attrs['accounts'] = {}
                self.populate_account(
                    attrs['accounts'], agg_score, agg_key=agg_key)

    def decorate_leafs(self, leafs):
        """
        Adds consumptions, implementation rate, number of respondents,
        assessment and improvement answers and opportunity score.

        For each answer the improvement opportunity in the total score is
        case NO / NEEDS_SIGNIFICANT_IMPROVEMENT
          numerator = (3-A) * opportunity + 3 * avg_value / nb_respondents
          denominator = 3 * avg_value / nb_respondents
        case YES / NEEDS_MODERATE_IMPROVEMENT
          numerator = (3-A) * opportunity
          denominator = 0
        """
        #pylint:disable=too-many-locals
        population = Consumption.objects.get_active_by_accounts(
            excludes=self._get_filter_out_testing())
        for prefix, values_tuple in six.iteritems(leafs):
            self.populate_leaf(prefix, values_tuple[0],
                get_scored_answers(population, self.default_metric_id,
                    includes=self.get_included_samples(),
                    prefix=prefix))
        super(ReportMixin, self).decorate_leafs(leafs)

    def get_report_tree(self, node=None, from_root=None, cut=ContentCut()):
        """
        Returns the content tree decorated with assessment and improvement data.
        """
        root = None
        self._start_time()
        if node is None or from_root is None:
            from_root, trail = self.breadcrumbs
            if trail:
                node = trail[-1][0]
        if node:
            self.get_or_create_assessment_sample()
            root = self._build_tree(node, from_root, cut=cut)
            populate_rollup(root, True)
            total_numerator = root[0]['accounts'].get(
                self.account.pk, {}).get('numerator', 0)
            total_denominator = root[0]['accounts'].get(
                self.account.pk, {}).get('denominator', 0)
            push_improvement_factors(root, total_numerator, total_denominator)
        return root

    def _insert_path(self, root, path, depth=1, values=None):
        parts = path.split('/')
        if len(parts) >= depth:
            prefix = '/'.join(parts[:depth])
            if not prefix in root[1]:
                root[1].update({prefix: (OrderedDict({}), OrderedDict({}))})
            if len(parts) == depth and values:
                root[1][prefix].update(values)
                return root
            return self._insert_path(root[1][prefix], path, depth=depth + 1,
                values=values)
        return root

    def _natural_order(self, root):
        candidate_prefix = ""
        paths = list(root[1])
        if paths:
            paths.sort(key=len)
            parts = paths[0].split('/')
            if len(paths) == 1:
                # If there is only one path/key, we prevent skipping
                # a level here.
                candidate_prefix = '/'.join(parts[:-1])
            else:
                candidate_prefix = '/'.join(parts)
                found = False
                while not found:
                    found = True
                    for path in paths:
                        if not path.startswith(candidate_prefix):
                            parts = parts[:-1]
                            candidate_prefix = '/'.join(parts)
                            found = False
                            break

        commonprefix = candidate_prefix
        if commonprefix:
            if commonprefix.endswith('/'):
                commonprefix = commonprefix[:-1]
            orig_element_slug = commonprefix.split('/')[-1]
            edges = [rec['dest_element__slug']
                for rec in RelationShip.objects.filter(
                    orig_element__slug=orig_element_slug).values(
                        'dest_element__slug').order_by('rank', 'pk')]
        else:
            edges = []
        ordered_root = (root[0], OrderedDict({}))
        for edge in edges:
            path = "%s/%s" % (commonprefix, edge)
            if path in root[1]:
                ordered_root[1].update({path: root[1][path]})
        for path, nodes in six.iteritems(ordered_root[1]):
            ordered_root[1][path] = self._natural_order(nodes)
        return ordered_root


    def flatten_answers(self, root, url_prefix, depth=0):
        """
        returns a list from the tree passed as an argument.
        """
        results = []
        for prefix, nodes in six.iteritems(root[1]):
            element = PageElement.objects.get(slug=prefix.split('/')[-1])
            if nodes[1]:
                results += [("heading-%d indent-header-%d" % (depth, depth),
                    "", element, {})]
                results += self.flatten_answers(
                    nodes, url_prefix, depth=depth + 1)
            else:
                results += [("bestpractice-%d indent-header-%d" % (
                    depth, depth), url_prefix + '/' + element.slug,
                    element, nodes[0])]
        return results

    def get_measured_metrics_context(self):
        from_root, trail = self.breadcrumbs
        url_prefix = trail[-1][1] if trail else ""
        root = (OrderedDict({}), OrderedDict({}))
        depth = len(from_root.split('/')) + 1

        env_metrics = Consumption.objects.filter(
            path__startswith=from_root,
            requires_measurements__gt=0)
        for env_metric in env_metrics:
            node = self._insert_path(root, env_metric.path, depth=depth)
            if 'environmental_metrics' not in node[0]:
                node[0].update({'environmental_metrics': [{
                'metric_title': "No data provided.",
                'measured': ""
            }]})
        root = self._natural_order(root)

        env_metric_answers = Answer.objects.filter(
            sample=self.assessment_sample).exclude(
            metric_id__in=(1, 2)).select_related('question')
        for env_metric_answer in env_metric_answers:
            rank = EnumeratedQuestions.objects.filter(
                question=env_metric_answer.question,
                campaign=self.sample.survey).values('rank').get().get(
                    'rank', None)
            if env_metric_answer.metric.unit.system != Unit.SYSTEM_ENUMERATED:
                measured = '%d' % env_metric_answer.measured
            else:
                measured = Choice.objects.get(pk=env_metric_answer.measured)
            node = self._insert_path(root, env_metric_answer.question.path,
                depth=depth)
            if 'environmental_metrics' not in node[0]:
                node[0].update({'environmental_metrics': []})
            else:
                for env_metric in node[0]['environmental_metrics']:
                    if env_metric['metric_title'] == "No data provided.":
                        node[0].update({'environmental_metrics': []})
                        break
            node[0]['environmental_metrics'] += [{
                'metric_title': env_metric_answer.metric.title,
                'measured': measured,
                'location': reverse('api_measures_delete', args=(
                    self.sample.account, self.sample,
                    rank, env_metric_answer.metric.slug))
            }]
        return self.flatten_answers(root, url_prefix)


class ImprovementQuerySetMixin(ReportMixin):
    """
    best practices which are part of an improvement plan for an ``Account``.
    """
    model = Answer

    @property
    def improvement_sample(self):
        if not hasattr(self, '_improvement_sample'):
            self._improvement_sample = Sample.objects.filter(
                extra='is_planned',
                survey=self.survey,
                account=self.account).order_by('-created_at').first()
        return self._improvement_sample

    def get_or_create_improve_sample(self):
        # We create the sample if it does not exists.
        if not self.improvement_sample:
            self._improvement_sample = Sample.objects.create(
                extra='is_planned', survey=self.survey, account=self.account)
        self._sample = self._improvement_sample

    def get_included_samples(self):
        results = super(ImprovementQuerySetMixin, self).get_included_samples()
        if self.improvement_sample:
            results += [self.improvement_sample]
        return results

    def get_queryset(self):
        return self.model.objects.filter(
            sample__extra='is_planned',
            sample__survey=self.survey,
            sample__account=self.account)

    def get_reverse_kwargs(self):
        """
        List of kwargs taken from the url that needs to be passed through
        to ``get_success_url``.
        """
        return ['path', self.interviewee_slug, 'survey']


class BestPracticeMixin(BreadcrumbMixin):
    """
    Mixin that will return the super.template or the `best practice details`
    template if a matching `Consumption` exists.
    """

    def get_template_names(self):
        if not self.best_practice:
            return super(BestPracticeMixin, self).get_template_names()
        return ['envconnect/best_practice.html']

    def get_context_data(self, **kwargs):
        context = super(
            BestPracticeMixin, self).get_context_data(**kwargs)
        breadcrumbs = context.get('breadcrumbs', [])
        if breadcrumbs:
            context.update({
                'is_content_manager': self.manages(
                    breadcrumbs[-1][0].account.slug)})
        if not self.best_practice:
            return context
        context.update({
            'icon': self.icon,
            'best_practice': self.best_practice})
        aliases = self.best_practice.get_parent_paths()
        if len(aliases) > 1:
            alias_breadcrumbs = []
            for alias in aliases:
                if alias and len(alias) > 4:
                    alias_breadcrumbs += [[alias[0], "..."] + alias[-3:-1]]
                elif alias and len(alias) > 1:
                    alias_breadcrumbs += [alias[:-1]]
                else:
                    # XXX This is probably an error in `get_parent_paths`
                    alias_breadcrumbs += [[alias]]
            context.update({'aliases': alias_breadcrumbs})
        organization = self.kwargs.get('organization', None)
        if organization:
            context.update({'organization': organization})
        votes_score = self.best_practice.votes.all().aggregate(
            sum_votes=Sum('vote')).get('sum_votes', 0)
        if votes_score is None:
            votes_score = 0
        context.update({
            'nb_followers': self.best_practice.followers.all().count(),
            'votes_score': votes_score
        })
        if self.request.user.is_authenticated:
            context.update({
                'is_following': self.best_practice.followers.filter(
                    user=self.request.user).exists(),
                'is_voted': self.best_practice.votes.filter(
                    user=self.request.user).exists()
            })
        # Change defaults contextual URL to move back up one level.
        _, trail = self.breadcrumbs
        contextual_path = (
            trail[-2][1] if len(trail) > 1 else self.kwargs.get('path', ""))
        parts = contextual_path.split('#')
        contextual_path = parts[0]
        if len(parts) > 1:
            active_section = "?active=%s" % parts[1]
        else:
            active_section = ""
        if organization:
            urls = {
                'assess': reverse('envconnect_assess_organization',
                    args=(organization, contextual_path)) + active_section,
                'improve': reverse('envconnect_improve_organization',
                    args=(organization, contextual_path)) + active_section
            }
        else:
            urls = {
                'assess': reverse('envconnect_assess',
                    args=(contextual_path,)) + active_section,
                'improve': reverse('envconnect_improve',
                    args=(contextual_path,)) + active_section
            }
        self.update_context_urls(context, urls)
        return context

    @property
    def best_practice(self):
        if not hasattr(self, '_best_practice'):
            try:
                trail = self.get_full_element_path(self.kwargs.get('path'))
                Consumption.objects.get(path="/" + "/".join(
                    [elm.slug for elm in trail]))
                self._best_practice = trail[-1]
            except Consumption.DoesNotExist:
                self._best_practice = None
        return self._best_practice
