# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import json, logging
from collections import OrderedDict

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404
from django.db.models import Sum
from django.utils import six
from deployutils.apps.django import mixins as deployutils_mixins
from pages.models import PageElement, RelationShip
from pages.mixins import TrailMixin
from survey.models import Response, SurveyModel
from survey.utils import get_account_model

from .models import Consumption, Improvement, get_score_weight
from .serializers import PageElementSerializer, ConsumptionSerializer

LOGGER = logging.getLogger(__name__)


class AccountMixin(deployutils_mixins.AccountMixin):

    account_queryset = get_account_model().objects.all()
    account_lookup_field = 'slug'
    account_url_kwarg = 'organization'


class PermissionMixin(deployutils_mixins.AccessiblesMixin):

    def get_roots(self):
        return PageElement.objects.get_roots().filter(tag__contains='industry')

    def get_context_data(self, *args, **kwargs):
        context = super(
            PermissionMixin, self).get_context_data(*args, **kwargs)
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

    def enter(self, root):
        depth = self.depth
        self.depth = self.depth + 1
        return not (depth > 1 and
            root.tag and BreadcrumbMixin.TAG_SYSTEM in root.tag)

    def leave(self, root, subtrees):
        #pylint:disable=unused-argument
        self.depth = self.depth - 1
        return True


class BreadcrumbMixin(PermissionMixin, TrailMixin):

    breadcrumb_url = 'summary'
    TAG_SYSTEM = 'system'

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
        """
        Returns a list of trees from a list of roots, each tree rooted at one
        of those roots.

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
        if prefix is None:
            prefix = ''
        elif not prefix.startswith("/"):
            prefix = "/" + prefix
        if roots is None:
            roots = self.get_roots()
        results = OrderedDict()
        for root in roots:
            if prefix.endswith("/" + root.slug):
                # Workaround because we sometimes pass a prefix and sometimes
                # a path `from_root`.
                base = prefix
            else:
                base = prefix + "/" + root.slug
            subtrees = OrderedDict()
            if cut is None or cut.enter(root):
                for edge in RelationShip.objects.filter(
                        orig_element=root).select_related(
                            'dest_element').order_by('rank', 'pk'):
                    # XXX We use the fact that node ids are naturally
                    # in increasing order. Without order postgres will not
                    # return the icons in a consistent order.
                    subtree = self.build_content_tree(
                        [edge.dest_element], base, cut=cut)
                    for sub in six.itervalues(subtree):
                        sub[0].update({'rank': edge.rank})
                    subtrees.update(subtree)
            result_node = {
                'path': base,
                'slug': root.slug,
                'title': root.title,
                'score_weight': get_score_weight(root),
                'text': root.text,
                'tag': root.tag,
            }
            results.update({base: (
                result_node,
                subtrees if cut is None or cut.leave(
                    result_node, subtrees) else {})})
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

        if len(rollup_tree[1].keys()) == 0:
            return {path: rollup_tree}
        leafs = {}
        for key, level_detail in six.iteritems(rollup_tree[1]):
            leafs.update(self.get_leafs(level_detail, path=key))
        return leafs

    @staticmethod
    def decorate_with_consumptions(leafs):
        for path, vals in six.iteritems(leafs):
            consumption = Consumption.objects.filter(path=path).first()
            if consumption:
                vals[0]['consumption'] \
                    = ConsumptionSerializer().to_representation(consumption)
            else:
                vals[0]['consumption'] = None

    def _build_tree(self, root, path, cut=ContentCut()):
        prefix = '/'.join(path.split('/')[:-1])
        # hack to remove slug that will be added.
        rollup_trees = self.build_content_tree([root], prefix=prefix, cut=cut)
        for rollup_tree in six.itervalues(rollup_trees):
            leafs = self.get_leafs(rollup_tree)
            self.decorate_with_consumptions(leafs)
            return rollup_tree

    def _cut_tree(self, root, path='', depth=5):
        """
        *root* has a format [{... node attribte ...}, {.., subtrees ...}]
        """
        results = OrderedDict()
        if len(path.split('/')) < depth:
            for node_path, node in six.iteritems(root[1]):
                results.update({
                    node_path: self._cut_tree(node, path=node_path)})
        return (root[0], results)

    @property
    def breadcrumbs(self):
        if not hasattr(self, '_breadcrumbs'):
            self._breadcrumbs = self.get_breadcrumbs(self.kwargs.get('path'))
        return self._breadcrumbs

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
                raise Http404("Cannot find '%s' in trail '%s'",
                    part, " > ".join([elm.title for elm in trail]))
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

    def get_context_data(self, *args, **kwargs):
        context = super(BreadcrumbMixin, self).get_context_data(*args, **kwargs)
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

    def to_representation(self, root, prefix=None):
        if prefix is None:
            prefix, _ = self.breadcrumbs
            prefix = '/'.join(prefix.split('/')[:-1])
        results = []
        root_repr = PageElementSerializer(
            context={'prefix': prefix}).to_representation(root[0])
        for node in root[1]:
            results += [self.to_representation(
                node, prefix=prefix + '/' + root[0].slug)]
        return [root_repr, results]


class ReportMixin(BreadcrumbMixin, AccountMixin):

    report_title = 'Best Practices Report'

    @property
    def sample(self):
        if not hasattr(self, '_sample'):
            try:
                self._sample = Response.objects.get(
                    account__slug=self.account, survey__title=self.report_title)
            except Response.DoesNotExist:
                self._sample = None
        return self._sample

    def get_survey(self):
        try:
            return SurveyModel.objects.get(
                account=self.account, title=self.report_title)
        except SurveyModel.DoesNotExist:
            raise Http404("Cannot find SurveyModel(account=%s, title=%s)",
                self.account, self.report_title)


class ImprovementQuerySetMixin(ReportMixin):
    """
    best practices which are part of an improvement plan for an ``Account``.
    """
    model = Improvement

    def get_queryset(self):
        return self.model.objects.filter(account=self.account)

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

    def get_context_data(self, *args, **kwargs):
        context = super(
            BestPracticeMixin, self).get_context_data(*args, **kwargs)
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
