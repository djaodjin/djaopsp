# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

from __future__ import absolute_import
from __future__ import unicode_literals

import json, logging
from collections import OrderedDict

from deployutils.crypt import JSONEncoder
from django.conf import settings
from django.db.models import Q
from django.utils import six
from pages.mixins import TrailMixin
from pages.models import PageElement
from rest_framework import generics
from rest_framework.response import Response as HttpResponse
from survey.models import  Campaign, Metric, Sample

from .best_practices import ToggleTagContentAPIView
from ..mixins import ReportMixin, TransparentCut
from ..models import (get_score_weight, get_scored_answers,
    get_historical_scores, Consumption)
from ..serializers import ScoreWeightSerializer
from ..scores import populate_rollup

LOGGER = logging.getLogger(__name__)


class BenchmarkMixin(ReportMixin):

    def get_highlighted_practices(self):
        from_root, trail = self.breadcrumbs
        url_prefix = trail[-1][1] if trail else ""

        flt = Q(answer__sample=self.assessment_sample,
              answer__metric_id=self.default_metric_id,
              answer__measured=Consumption.NOT_APPLICABLE)
        if self.improvement_sample:
            flt = flt | Q(answer__sample=self.improvement_sample,
                answer__metric_id=self.default_metric_id,
                answer__measured=Consumption.NEEDS_SIGNIFICANT_IMPROVEMENT)
        highlighted_practices = Consumption.objects.filter(flt).values(
            'path', 'answer__sample_id', 'answer__measured')

        depth = len(from_root.split('/')) + 1
        root = (OrderedDict({}), OrderedDict({}))
        assessment_sample_pk = (
            self.assessment_sample.id if self.assessment_sample else 0)
        improvement_sample_pk = (
            self.improvement_sample.id if self.improvement_sample else 0)
        for practice in highlighted_practices:
            node = self._insert_path(root, practice['path'], depth=depth)
            if (practice['answer__sample_id'] == assessment_sample_pk and
                practice['answer__measured'] == Consumption.NOT_APPLICABLE):
                node[0].update({'not_applicable': True})
            if practice['answer__sample_id'] == improvement_sample_pk:
                node[0].update({'planned': True})

        # Populate environmental metrics answers
        root = self._get_measured_metrics_context(root, from_root)
        root = self._natural_order(root)
        return self.flatten_answers(root, url_prefix)

    def get_context_data(self, **kwargs):
        context = super(BenchmarkMixin, self).get_context_data(**kwargs)
        context.update({
            'highlighted_practices': self.get_highlighted_practices(),
        })
        return context

    def get_drilldown(self, rollup_tree, prefix):
        accounts = None
        node = rollup_tree[1].get(prefix, None)
        if node:
            accounts = rollup_tree[0].get('accounts', OrderedDict({}))
        elif prefix == 'totals' or rollup_tree[0].get('slug', '') == prefix:
            accounts = rollup_tree[0].get('accounts', OrderedDict({}))
        else:
            for node in six.itervalues(rollup_tree[1]):
                accounts = self.get_drilldown(node, prefix)
                if accounts is not None:
                    break
        # Filter out accounts whose score cannot be computed.
        if accounts is not None:
            all_accounts = accounts
            accounts = OrderedDict({})
            for account_id, account_metrics in six.iteritems(all_accounts):
                normalized_score = account_metrics.get('normalized_score', None)
                if normalized_score is not None:
                    accounts[account_id] = account_metrics

        return accounts

    def get_charts(self, rollup_tree, excludes=None):
        charts = []
        icon_tag = rollup_tree[0].get('tag', "")
        if icon_tag and settings.TAG_SCORECARD in icon_tag:
            if not (excludes and rollup_tree[0].get('slug', "") in excludes):
                charts += [rollup_tree[0]]
        for _, icon_tuple in six.iteritems(rollup_tree[1]):
            sub_charts = self.get_charts(icon_tuple, excludes=excludes)
            charts += sub_charts
        return charts


    def create_distributions(self, rollup_tree, view_account=None):
        #pylint:disable=too-many-statements
        """
        Create a tree with distributions of scores from a rollup tree.
        """
        #pylint:disable=too-many-locals
        denominator = None
        highest_normalized_score = 0
        sum_normalized_scores = 0
        nb_respondents = 0
        nb_implemeted_respondents = 0
        distribution = None
        for account_id_str, account_metrics in six.iteritems(rollup_tree[0].get(
                'accounts', OrderedDict({}))):
            if account_id_str is None: # XXX why is that?
                continue
            account_id = int(account_id_str)
            is_view_account = (view_account and account_id == view_account)

            if is_view_account:
                rollup_tree[0].update(account_metrics)
            normalized_score = account_metrics.get('normalized_score', None)
            if (normalized_score is None
                or account_metrics.get('nb_questions', 0) == 0):
                # `nb_questions == 0` to show correct number of respondents
                # in relation with the `slug = 'totals'` statement
                # in populate_rollup.
                continue

            nb_respondents += 1
            numerator = account_metrics.get('numerator')
            denominator = account_metrics.get('denominator')
            if numerator == denominator:
                nb_implemeted_respondents += 1
            if normalized_score > highest_normalized_score:
                highest_normalized_score = normalized_score
            sum_normalized_scores += normalized_score
            if distribution is None:
                distribution = {
                    'x' : ["0-25%", "25-50%", "50-75%", "75-100%"],
                    'y' : [0 for _ in range(4)],
                    'organization_rate': ""
                }
            if normalized_score < 25:
                distribution['y'][0] += 1
                if is_view_account:
                    distribution['organization_rate'] = distribution['x'][0]
            elif normalized_score < 50:
                distribution['y'][1] += 1
                if is_view_account:
                    distribution['organization_rate'] = distribution['x'][1]
            elif normalized_score < 75:
                distribution['y'][2] += 1
                if is_view_account:
                    distribution['organization_rate'] = distribution['x'][2]
            else:
                assert normalized_score <= 100
                distribution['y'][3] += 1
                if is_view_account:
                    distribution['organization_rate'] = distribution['x'][3]

        for node_metrics in six.itervalues(rollup_tree[1]):
            self.create_distributions(node_metrics, view_account=view_account)

        if distribution is not None:
            if nb_respondents > 0:
                avg_normalized_score = int(
                    sum_normalized_scores / nb_respondents)
                rate = int(100.0 * nb_implemeted_respondents / nb_respondents)
            else:
                avg_normalized_score = 0
                rate = 0
            rollup_tree[0].update({
                'nb_respondents': nb_respondents,
                'rate': rate,
                'opportunity': denominator,
                'highest_normalized_score': highest_normalized_score,
                'avg_normalized_score': avg_normalized_score,
                'distribution': distribution
            })
        if 'accounts' in rollup_tree[0]:
            del rollup_tree[0]['accounts']

    def flatten_distributions(self, distribution_tree, prefix=None):
        """
        Flatten the tree into a list of charts.
        """
        # XXX Almost identical to get_charts. Can we abstract differences?
        if prefix is None:
            prefix = "/"
        if not prefix.startswith("/"):
            prefix = "/" + prefix
        charts = []
        complete = True
        for key, chart in six.iteritems(distribution_tree[1]):
            if key.startswith(prefix) or prefix.startswith(key):
                leaf_charts, leaf_complete = self.flatten_distributions(
                    chart, prefix=prefix)
                charts += leaf_charts
                complete &= leaf_complete
                charts += [chart[0]]
                if 'distribution' in chart[0]:
                    complete &= (chart[0].get(
                        'normalized_score', None) is not None)
        return charts, complete

    @staticmethod
    def get_distributions(numerators, denominators, view_sample=None):
        distribution = {
            'x' : ["0-25%", "25-50%", "50-75%", "75-100%"],
            'y' : [0 for _ in range(4)],
            'normalized_score': 0,  # instead of 'ukn.' to avoid js error.
            'organization_rate': ""
        }
        for sample, numerator in six.iteritems(numerators):
            denominator = denominators.get(sample, 0)
            if denominator != 0:
                normalized_score = int(numerator * 100 / denominator)
            else:
                normalized_score = 0
            if sample == view_sample:
                distribution['normalized_score'] = normalized_score
            if normalized_score < 25:
                distribution['y'][0] += 1
                if sample == view_sample:
                    distribution['organization_rate'] = distribution['x'][0]
            elif normalized_score < 50:
                distribution['y'][1] += 1
                if sample == view_sample:
                    distribution['organization_rate'] = distribution['x'][1]
            elif normalized_score < 75:
                distribution['y'][2] += 1
                if sample == view_sample:
                    distribution['organization_rate'] = distribution['x'][2]
            else:
                assert normalized_score <= 100
                distribution['y'][3] += 1
                if sample == view_sample:
                    distribution['organization_rate'] = distribution['x'][3]
        return distribution

    @staticmethod
    def _get_scored_answers(population, metric_id,
                            includes=None, questions=None, prefix=None):
        #pylint:disable=unused-argument
        return get_scored_answers(population, metric_id,
            includes=includes, prefix=prefix)


    def rollup_scores(self, roots=None, root_prefix=None):
        """
        Returns a tree populated with scores per accounts.
        """
        self._start_time()
        self._report_queries("at rollup_scores entry point")
        rollup_tree = None
        rollups = self._cut_tree(self.build_content_tree(
            roots, prefix=root_prefix, cut=TransparentCut()),
            cut=TransparentCut())

        # Moves up all industry segments which are under a category
        # (ex: /facilities/janitorial-services).
        # If we donot do that, then assessment score will be incomplete
        # in the dashboard, as the aggregator will wait for other sub-segments
        # in the top level category.
        removes = []
        ups = OrderedDict({})
        for root_path, root in six.iteritems(rollups):
            if not 'pagebreak' in root[0].get('tag', ""):
                removes += [root_path]
                ups.update(root[1])
        for root_path in removes:
            del rollups[root_path]
        rollups.update(ups)

        rollup_tree = (OrderedDict({}), rollups)
        self._report_queries("rollup_tree generated")
        if 'title' not in rollup_tree[0]:
            rollup_tree[0].update({
                'slug': "totals",
                'title': "Total Score",
                'tag': [settings.TAG_SCORECARD]})
        leafs = self.get_leafs(rollup_tree=rollup_tree)
        self._report_queries("leafs loaded")
        population = list(Consumption.objects.get_active_by_accounts(
            self.survey, excludes=self._get_filter_out_testing()))
        includes = list(
            Consumption.objects.get_latest_samples_by_accounts(self.survey))
        framework_metric_id = Metric.objects.get(slug='framework').pk
        framework_includes = list(
            Consumption.objects.get_latest_samples_by_accounts(
                Campaign.objects.get(slug='framework')))
        for prefix, values_tuple in six.iteritems(leafs):
            metric_id = self.default_metric_id
            if prefix.startswith('/framework/'):
                metric_id = framework_metric_id
                accounts = {}
                for sample in framework_includes:
                    accounts.update({sample.account_id: {'nb_questions': 1}})
                if not 'accounts' in values_tuple[0]:
                    values_tuple[0]['accounts'] = {}
                values_tuple[0]['accounts'].update(accounts)

            self.populate_leaf(prefix, values_tuple[0],
                self._get_scored_answers(population, metric_id,
                    includes=includes, prefix=prefix))
        self._report_queries("leafs populated")
        populate_rollup(rollup_tree, True)
        self._report_queries("rollup_tree populated")
        return rollup_tree


    def get_rollup_at_path_prefix(self, root_prefix, rollup_tree=None):
        """
        Traverse the `rollup_tree` to find and return the node
        matching `root_prefix`.
        """
        if rollup_tree is None:
            rollup_tree = self.rollup_scores()
        if root_prefix in rollup_tree[1]:
            return rollup_tree[1][root_prefix]
        parts = root_prefix.split('/')
        while parts:
            parts.pop()
            from_root = '/'.join(parts)
            if from_root in rollup_tree[1]:
                return self.get_rollup_at_path_prefix(
                    root_prefix, rollup_tree[1][from_root])
        raise KeyError(root_prefix)


class BenchmarkAPIView(BenchmarkMixin, generics.GenericAPIView):
    """
    .. sourcecode:: http

        GET /api/*organization*/benchmark*path*

    Returns list of *organization*'s scores for all relevant section
    of the best practices based on *path*.

    **Example request**:

    .. sourcecode:: http

        GET /api/steve-shop/benchmark/boxes-and-enclosures/energy-efficiency/

    **Example response**:

    .. sourcecode:: http

        [{
            "slug":"totals",
            "title":"Total Score",
            "nb_answers": 4,
            "nb_questions": 4,
            "nb_respondents": 2,
            "numerator": 12.0,
            "improvement_numerator": 8.0,
            "denominator": 26.0,
            "normalized_score": 46,
            "improvement_score": 30,
            "score_weight": 1.0,
            "highest_normalized_score": 88,
            "avg_normalized_score": 67,
            "created_at":"2017-08-02T20:18:19.089",
            "distribution": {
                "y": [0, 1, 0, 1],
                "x": ["0-25%", "25-50%", "50-75%", "75-100%"],
                "organization_rate":"25-50%"
            }
         },
         {
            "slug":"energy-efficiency-management-basics",
            "title":"Management",
            "text":"/media/envconnect/management-basics.png",
            "tag":"management",
            "score_weight":1.0
         },
         {
            "slug":"process-heating",
            "title":"Process heating",
            "text":"/media/envconnect/process-heating.png",
            "nb_questions": 4,
            "nb_answers": 4,
            "nb_respondents": 2,
            "numerator": 12.0,
            "improvement_numerator": 8.0,
            "denominator": 26.0,
            "normalized_score": 46,
            "improvement_score": 12,
            "highest_normalized_score": 88,
            "avg_normalized_score": 67,
            "created_at": "2017-08-02T20:18:19.089",
            "distribution": {
                "y": [0, 1, 0, 1],
                "x": [ "0-25%", "25-50%", "50-75%", "75-100%"],
                "organization_rate": "25-50%"
            },
            "score_weight": 1.0
         }]
    """

    http_method_names = ['get']

    def get_queryset(self):
        #pylint:disable=too-many-locals
        from_root, trail = self.breadcrumbs
        roots = [trail[-1][0]] if trail else None
        rollup_tree = self.rollup_scores(roots, from_root)
        self.create_distributions(rollup_tree,
            view_account=(self.assessment_sample.account.pk
                if self.assessment_sample else None))
        self.decorate_with_breadcrumbs(rollup_tree)
        charts, complete = self.flatten_distributions(rollup_tree,
            prefix=from_root)

        # Done in BenchmarkBaseView through `_build_tree` > `decorate_leafs`.
        # This code is here otherwise the printable scorecard doesn't show
        # icons.
        for chart in charts:
            text = PageElement.objects.filter(
                slug=chart['slug']).values('text').first()
            if text and text['text']:
                chart.update({'icon': text['text']})

        total_score = None
        parts = from_root.split('/')
        if parts:
            slug = parts[-1]
        # When we remove the following 4 lines ...
            for chart in charts:
                if chart['slug'] == slug:
                    total_score = chart.copy()
                    break
        if not total_score:
            total_score = rollup_tree[0]
        if not total_score:
            total_score = OrderedDict({"nb_respondents": "-"})
        total_score.update({"slug": "totals", "title": "Total Score"})
        # ... and the following 2 lines together, pylint does not blow up...
        if not complete and 'normalized_score' in total_score:
            del total_score['normalized_score']
        charts += [total_score]
        return charts

    def get(self, request, *args, **kwargs): #pylint:disable=unused-argument
        return HttpResponse(self.get_queryset())


class EnableScorecardAPIView(ToggleTagContentAPIView):

    added_tag = 'scorecard'


class DisableScorecardAPIView(ToggleTagContentAPIView):

    removed_tag = 'scorecard'


class ScoreWeightAPIView(TrailMixin, generics.RetrieveUpdateAPIView):

    lookup_field = 'path'
    serializer_class = ScoreWeightSerializer

    def retrieve(self, request, *args, **kwargs):
        trail = self.get_full_element_path(self.kwargs.get('path'))
        return HttpResponse(self.serializer_class().to_representation({
            'weight': get_score_weight(trail[-1].tag)}))

    def update(self, request, *args, **kwargs):#pylint:disable=unused-argument
        partial = kwargs.pop('partial', False)
        serializer = self.serializer_class(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return HttpResponse(serializer.data)

    def perform_update(self, serializer):
        trail = self.get_full_element_path(self.kwargs.get('path'))
        element = trail[-1]
        extra = {}
        try:
            extra = json.loads(element.tag)
        except (TypeError, ValueError):
            pass
        extra.update(serializer.validated_data)
        element.tag = json.dumps(extra, cls=JSONEncoder)
        element.save()


# XXX ReportMixin because we use populate_leafs
class HistoricalScoreAPIView(ReportMixin, generics.RetrieveAPIView):
    """
    .. sourcecode:: http

        GET /api/*organization*/historical*path*

    Returns list of historical *organization*'s scores for all top level
    icons based on *path*. The output format is compatible
    with `HistoricalScoreChart` (see draw-chart.js).

    **Example request**:

    .. sourcecode:: http

        GET /api/steve-shop/benchmark/boxes-and-enclosures/energy-efficiency/

    **Example response**:

    .. sourcecode:: http
        [
            {
                "key": "May 2018",
                "values": [
                    ["Governance & Management", 80],
                    ["Engineering & Design", 78],
                    ["Procurement", 72],
                    ["Construction", 73],
                    ["Office", 74],
                ],
            },
            {
                "key": "Dec 2017",
                "values": [
                    ["Governance & Management", 60],
                    ["Engineering & Design", 67],
                    ["Procurement", 56],
                    ["Construction", 52],
                    ["Office", 59],
                ],
            },
            {
                "key": "Jan 2017",
                "values": [
                    ["Governance & Management", 60],
                    ["Engineering & Design", 67],
                    ["Procurement", 16],
                    ["Construction", 49],
                    ["Office", 40],
                ],
            },
        ]
    """

    @staticmethod
    def flatten_distributions(rollup_tree, accounts, prefix=None):
        """
        A rollup_tree is keyed best practices and we need a structure
        keyed on historical samples here.
        """
        if prefix is None:
            prefix = "/"
        if not prefix.startswith("/"):
            prefix = "/" + prefix

        for node_path, node in six.iteritems(rollup_tree[1]):
            node_key = node[0].get('title', node_path)
            for account_key, account in six.iteritems(node[0].get(
                    'accounts', OrderedDict({}))):
                if account_key not in accounts:
                    accounts[account_key] = OrderedDict({})
                accounts[account_key].update({
                    node_key: account.get('normalized_score', 0)})

    def get(self, request, *args, **kwargs):
        #pylint:disable=unused-argument,too-many-locals
        self._start_time()
        from_root, trail = self.breadcrumbs
        roots = [trail[-1][0]] if trail else None
        self._report_queries("at rollup_scores entry point")
        rollups = self._cut_tree(self.build_content_tree(
            roots, prefix=from_root, cut=TransparentCut()),
            cut=TransparentCut())
        rollup_tree = (OrderedDict({}), rollups)
        self._report_queries("rollup_tree generated")
        leafs = self.get_leafs(rollup_tree=rollup_tree)
        self._report_queries("leafs loaded")
        for prefix, values_tuple in six.iteritems(leafs):
            self.populate_leaf(prefix, values_tuple[0],
                get_historical_scores(
                    includes=Sample.objects.filter(account=self.account),
                    prefix=prefix),
                agg_key='last_activity_at') # Relies on
                                            # `get_historical_scores()`
                                            # to use `Sample.created_at`
        self._report_queries("leafs populated")
        populate_rollup(rollup_tree, True)
        self._report_queries("rollup_tree populated")
        # We populated the historical scores per section.
        # Now we need to transpose them by sample_id.
        accounts = OrderedDict({})
        self.flatten_distributions(
            rollup_tree, accounts, prefix=from_root)
        result = []
        for account_key, account in six.iteritems(accounts):
            result += [{
                "key": account_key.strftime("%b %Y"),
                "values": list(six.iteritems(account))
            }]
        return HttpResponse(result)
