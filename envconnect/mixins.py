# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging
from collections import OrderedDict
from datetime import datetime, timedelta

import monotonic
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connections, transaction
from django.db.models import Max, Sum
from django.http import Http404
from django.utils import six
from deployutils.apps.django import mixins as deployutils_mixins
from pages.models import PageElement, RelationShip
from pages.mixins import TrailMixin
from rest_framework.generics import get_object_or_404
from survey.models import Answer, Sample, Campaign, EnumeratedQuestions
from survey.utils import get_account_model

from .models import Consumption, get_score_weight
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

    def get_context_data(self, **kwargs):
        context = super(
            PermissionMixin, self).get_context_data(**kwargs)
        context.update({
            'is_envconnect_manager': self.manages(settings.APP_NAME)})
        return context


class ContentCut(object):
    """
    Visitor used to cut down a tree whenever BreadcrumbMixin.TAG_SYSTEM
    is encountered.
    """

    def __init__(self, depth=1):
        self.depth = depth

    def enter(self, tag):
        depth = self.depth
        self.depth = self.depth + 1
        return not (depth > 1 and tag and BreadcrumbMixin.TAG_SYSTEM in tag)

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
    TAG_SYSTEM = 'system'
    report_title = 'Best Practices Report'

    enable_report_queries = True

    @property
    def survey(self):
        if not hasattr(self, '_survey'):
            self._survey = get_object_or_404(
                Campaign.objects.all(), title=self.report_title)
        return self._survey

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
                'score_weight': get_score_weight(tag),
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
            for edge in edges:
                slug = edge.get('slug', edge.get('dest_element__slug'))
                orig_element_id = edge.get('orig_element_id')
                dest_element_id = edge.get('dest_element_id')
                title = edge.get('dest_element__title')
                tag = edge.get('dest_element__tag')
                base = pks_to_leafs[orig_element_id][0]['path'] + "/" + slug
                result_node = {
                    'path': base,
                    'slug': slug,
                    'title': title,
                    'tag': tag,
                    'score_weight': get_score_weight(tag),
                }
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
        else:
            text = PageElement.objects.filter(
                slug=rollup_tree[0]['slug']).values('text').first()
            if text and text['text']:
                rollup_tree[0].update(text)
        leafs = {}
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

    def decorate_with_consumptions(self, leafs):
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
        rollup_trees = self._cut_tree(self.build_content_tree(
            [root], prefix=prefix, cut=cut), cut=cut)
        try:
            # We only have one root by definition of the function signature.
            rollup_tree = next(six.itervalues(rollup_trees))
        except StopIteration:
            LOGGER.exception("build_tree([%s], path=%s, cut=%s)"\
                " leaves an empty rollup tree", root, path, cut.__class__)
            rollup_tree = ({'slug': ""}, {})
        leafs = self.get_leafs(rollup_tree)
        self.decorate_with_consumptions(leafs)
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
                # for self-assessment to summary and back?
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
                'summary': reverse('summary_organization',
                    args=(context['organization'], path)) + active_section,
                'benchmark': reverse('benchmark_organization',
                    args=(context['organization'], path)) + active_section,
                'report': reverse('report_organization',
                    args=(context['organization'], path)) + active_section,
                'improve': reverse('envconnect_improve_organization',
                    args=(context['organization'], path)) + active_section
            })
        else:
            urls.update({
                'summary': reverse('summary', args=(path,)) + active_section,
                'benchmark':
                  reverse('benchmark', args=(path,)) + active_section,
                'report': reverse('report', args=(path,)) + active_section,
                'improve':
                  reverse('envconnect_improve', args=(path,))  + active_section
            })
        self.update_context_urls(context, urls)
        return context


class ReportMixin(BreadcrumbMixin, AccountMixin):

    def _get_filter_out_testing(self):
        # List of response ids that are only used for demo purposes.
        if self.request.user.username in settings.TESTING_USERNAMES:
            return []
        return settings.TESTING_RESPONSE_IDS

    @property
    def sample(self):
        if not hasattr(self, '_sample'):
            try:
                self._sample = Sample.objects.get(
                    extra__isnull=True,
                    survey__title=self.report_title,
                    account=self.account)
            except Sample.DoesNotExist:
                self._sample = None
        return self._sample

    def get_or_create_assessment_sample(self):
        # We create the sample if it does not exists.
        with transaction.atomic():
            if self.sample is None:
                self._sample = Sample.objects.create(
                    survey=self.survey, account=self.account)


class ImprovementQuerySetMixin(ReportMixin):
    """
    best practices which are part of an improvement plan for an ``Account``.
    """
    model = Answer

    @property
    def improvement_sample(self):
        if not hasattr(self, '_improvement_sample'):
            try:
                self._improvement_sample = Sample.objects.get(
                    extra='is_planned',
                    survey__title=self.report_title,
                    account=self.account)
            except Sample.DoesNotExist:
                self._improvement_sample = None
        return self._improvement_sample

    def get_or_create_improve_sample(self):
        # We create the sample if it does not exists.
        self._sample, _ = Sample.objects.get_or_create(
            extra='is_planned', survey=self.survey, account=self.account)

    def get_queryset(self):
        return self.model.objects.filter(
            sample__extra='is_planned',
            sample__survey__title=self.report_title,
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
        if not self.best_practice:
            return context
        context.update({
            'icon': self.icon,
            'path': self.kwargs.get('path'),
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
            trail[-2][1] if len(trail) > 1 else self.kwargs('path', ""))
        parts = contextual_path.split('#')
        contextual_path = parts[0]
        if len(parts) > 1:
            active_section = "?active=%s" % parts[1]
        else:
            active_section = ""
        if organization:
            urls = {
                'report': reverse('report_organization',
                    args=(organization, contextual_path)) + active_section,
                'improve': reverse('envconnect_improve_organization',
                    args=(organization, contextual_path)) + active_section
            }
        else:
            urls = {
                'report':
                  reverse('report', args=(contextual_path,)) + active_section,
                'improve': (
                    reverse('envconnect_improve', args=(contextual_path,))
                    + active_section)
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
