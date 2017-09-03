# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from __future__ import absolute_import
from __future__ import unicode_literals

import json, logging
from datetime import datetime, timedelta

import monotonic
from django.conf import settings
from django.db import connection, connections
from django.utils import six
from pages.mixins import TrailMixin
from pages.models import PageElement
from rest_framework import generics
from rest_framework.response import Response as RestResponse
from survey.models import Answer

from .best_practices import DecimalEncoder, ToggleTagContentAPIView
from ..mixins import ReportMixin
from ..models import Consumption, Improvement, get_score_weight
from ..serializers import ScoreWeightSerializer


LOGGER = logging.getLogger(__name__)


class TransparentCut(object):

    def __init__(self, depth=1):
        self.depth = depth

    def enter(self, root):
        depth = self.depth
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


class BenchmarkMixin(ReportMixin):

    ACCOUNT_ID = 0
    ANSWER_ID = 1
    RESPONSE_ID = 2
    QUESTION_ID = 3
    NUMERATOR = 4
    DENOMINATOR = 5
    QUESTION_PATH = 6
    ANSWER_TEXT = 7
    ANSWER_CREATED_AT = 8

    enable_report_queries = True

    def _report_queries(self, descr=None):
        if not self.enable_report_queries:
            return
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
        LOGGER.debug("%s: %s for %d SQL queries", descr, duration, nb_queries)

    @staticmethod
    def _show_query_and_result(raw_query, show=False):
        if show:
            LOGGER.debug("%s\n", raw_query)
            with connection.cursor() as cursor:
                cursor.execute(raw_query)
                count = 0
                for row in cursor.fetchall():
                    LOGGER.debug(str(row))
                    count += 1
                LOGGER.debug("%d row(s)", count)

    def get_drilldown(self, rollup_tree, prefix):
        accounts = None
        node = rollup_tree[1].get(prefix, None)
        if node:
            accounts = rollup_tree[0].get('accounts', {})
        elif prefix == 'totals' or rollup_tree[0].get('slug', '') == prefix:
            accounts = rollup_tree[0].get('accounts', {})
        else:
            for node in six.itervalues(rollup_tree[1]):
                accounts = self.get_drilldown(node, prefix)
                if accounts is not None:
                    break
        # Filter out accounts whose score cannot be computed.
        if accounts is not None:
            all_accounts = accounts
            accounts = {}
            for account_id, account_metrics in six.iteritems(all_accounts):
                normalized_score = account_metrics.get('normalized_score', None)
                if normalized_score is not None:
                    accounts[account_id] = account_metrics

        return accounts

    def get_charts(self, groups, path=None, text=None, tag=None):
        #pylint:disable=too-many-arguments,too-many-locals
        charts = []
        complete = True
        if path is None:
            path = ""
        for icon_path, icon_tuple in six.iteritems(groups):
            nb_answers = getattr(icon_tuple[0], 'nb_answers', 0)
            nb_questions = getattr(icon_tuple[0], 'nb_questions', 1)
            complete &= (nb_answers == nb_questions)
            icon_tag = icon_tuple[0].get('tag', "")
            icon_text = icon_tuple[0].get('text', "")
            if (icon_tag
                and settings.TAG_SCORECARD in icon_tag):
                _, trail = self.get_breadcrumbs(icon_path)
                if trail:
                    root_elem = trail.pop(0)
                    while trail and trail[0][0].title == root_elem[0].title:
                        trail.pop(0)
                breadcrumbs = [tup[0].title for tup in trail]
                icon = {
                    'slug': icon_tuple[0]['slug'],
                    'breadcrumbs': breadcrumbs,
                    'text': icon_text if text is None else text,
                    'tag': icon_tag if tag is None else tag,
                    'score_weight': icon_tuple[0].get('weight', 1.0),
                    'nb_answers': nb_answers,
                    'nb_questions': getattr(icon_tuple[0], 'nb_questions', 0),
                    'distribution': getattr(icon_tuple[0], 'distribution', {})
                }
                charts += [icon]
            sub_charts, _ = self.get_charts(
                icon_tuple[1], path=icon_path,
                text=icon_text
                    if icon_text and icon_text.endswith('.png') else None,
                tag=icon_tag
                    if icon_text and icon_text.endswith('.png') else None)
            charts += sub_charts
        return charts, complete


    def create_distributions(self, rollup_tree, view_account=None):
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
                'accounts', {})):
            if account_id_str is None: # XXX why is that?
                continue
            account_id = int(account_id_str)

            if account_id == view_account:
                rollup_tree[0].update(account_metrics)
            normalized_score = account_metrics.get('normalized_score', None)
            if (normalized_score is None
                or account_metrics.get('nb_questions', 0) == 0):
                # `nb_questions == 0` to show correct number of respondents
                # in relation with the `slug = 'total-score'` statement
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
                if account_id == view_account:
                    distribution['organization_rate'] = distribution['x'][0]
            elif normalized_score < 50:
                distribution['y'][1] += 1
                if account_id == view_account:
                    distribution['organization_rate'] = distribution['x'][1]
            elif normalized_score < 75:
                distribution['y'][2] += 1
                if account_id == view_account:
                    distribution['organization_rate'] = distribution['x'][2]
            else:
                assert normalized_score <= 100
                distribution['y'][3] += 1
                if account_id == view_account:
                    distribution['organization_rate'] = distribution['x'][3]

        for node_path, node_metrics in six.iteritems(rollup_tree[1]):
            self.create_distributions(node_metrics, view_account=view_account)

        if distribution is not None:
            opportunity = denominator

            if nb_respondents > 0:
                avg_normalized_score = int(
                    sum_normalized_scores / nb_respondents)
                rate = int( 100.0 * nb_implemeted_respondents / nb_respondents)
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
        if prefix is None:
            prefix = "/"
        if not prefix.startswith("/"):
            prefix = "/" + prefix
        if not distribution_tree[1]:
            return [], True
        charts = []
        complete = True
        for key, chart in six.iteritems(distribution_tree[1]):
            if key.startswith(prefix) or prefix.startswith(key):
                leaf_charts, leaf_complete = self.flatten_distributions(
                    chart, prefix=prefix)
                charts += leaf_charts
                complete &= leaf_complete
                # XXX duplicate from `get_charts`
                _, trail = self.get_breadcrumbs(key)
                if trail:
                    root_elem = trail.pop(0)
                    while trail and trail[0][0].title == root_elem[0].title:
                        trail.pop(0)
                breadcrumbs = [tup[0].title for tup in trail]
                chart[0].update({'breadcrumbs': breadcrumbs})
                # XXX end duplicate
                charts += [chart[0]]
                if 'distribution' in chart[0]:
                    complete &= (chart[0].get(
                        'normalized_score', None) is not None)
        return charts, complete

    @staticmethod
    def get_distributions(numerators, denominators, view_response=None):
        distribution = {
            'x' : ["0-25%", "25-50%", "50-75%", "75-100%"],
            'y' : [0 for _ in range(4)],
            'normalized_score': 0,  # instead of 'ukn.' to avoid js error.
            'organization_rate': ""
        }
        for response, numerator in six.iteritems(numerators):
            denominator = denominators.get(response, 0)
            if denominator != 0:
                normalized_score = int(numerator * 100 / denominator)
            else:
                normalized_score = 0
            if response == view_response:
                distribution['normalized_score'] = normalized_score
            if normalized_score < 25:
                distribution['y'][0] += 1
                if response == view_response:
                    distribution['organization_rate'] = distribution['x'][0]
            elif normalized_score < 50:
                distribution['y'][1] += 1
                if response == view_response:
                    distribution['organization_rate'] = distribution['x'][1]
            elif normalized_score < 75:
                distribution['y'][2] += 1
                if response == view_response:
                    distribution['organization_rate'] = distribution['x'][2]
            else:
                assert normalized_score <= 100
                distribution['y'][3] += 1
                if response == view_response:
                    distribution['organization_rate'] = distribution['x'][3]
        return distribution

    def get_opportunities(self):
        """
        Returns a list of question and opportunity associated to each question.
        """
        if True: #pylint:disable=using-constant-test
                 # XXX not sure what we tried to achieve here.
            opportunities = Consumption.objects.with_opportunity()
        else:
            opportunities = []
            with connection.cursor() as cursor:
                cursor.execute(self._get_opportunities_sql())
                opportunities = cursor.fetchall()
        return opportunities

    def get_expected_opportunities(self):
        questions_with_opportunity = Consumption.objects.get_opportunities_sql()

        # All expected questions for each response
        # decorated with ``opportunity``.
        #
        # If we are only looking for all expected questions for each response,
        # then the query can be simplified by using the survey_question table
        # directly.
        expected_opportunities = \
            "SELECT questions_with_opportunity.question_id"\
            " AS question_id, survey_response.id AS response_id,"\
            " survey_response.account_id AS account_id, opportunity,"\
            " questions_with_opportunity.path AS path"\
            " FROM (%(questions_with_opportunity)s)"\
            " AS questions_with_opportunity INNER JOIN survey_response"\
            " ON questions_with_opportunity.survey_id ="\
            " survey_response.survey_id" % {
                'questions_with_opportunity': questions_with_opportunity}
        self._show_query_and_result(expected_opportunities)
        return expected_opportunities

    def get_scored_improvements(self):
        """
        Compute scores specifically related to improvements.
        """
        # All expected answers with their scores.
        # ACCOUNT_ID = 0
        # ANSWER_ID = 1
        # RESPONSE_ID = 2
        # QUESTION_ID = 3
        # NUMERATOR = 4
        # DENOMINATOR = 5
        # QUESTION_PATH = 6
        # ANSWER_TEXT = 7
        scored_improvements = "SELECT expected_opportunities.account_id,"\
            " envconnect_improvement.id, expected_opportunities.response_id,"\
            " expected_opportunities.question_id,"\
            " (opportunity * 3) AS numerator,"\
            " (opportunity * 3) AS denominator,"\
            " expected_opportunities.path AS path"\
            " FROM (%(expected_opportunities)s) AS expected_opportunities"\
            " INNER JOIN envconnect_improvement "\
            " ON envconnect_improvement.consumption_id"\
            "   = expected_opportunities.question_id"\
            " AND envconnect_improvement.account_id"\
            "   = expected_opportunities.account_id" % {
                'expected_opportunities': self.get_expected_opportunities()}
        self._show_query_and_result(scored_improvements)

        scored_improvements_results = []
        with connection.cursor() as cursor:
            cursor.execute(scored_improvements)
            scored_improvements_results = cursor.fetchall()
        return scored_improvements_results

    def get_scored_answers(self):
        # All expected answers with their scores.
        # ACCOUNT_ID = 0
        # ANSWER_ID = 1
        # RESPONSE_ID = 2
        # QUESTION_ID = 3
        # NUMERATOR = 4
        # DENOMINATOR = 5
        # QUESTION_PATH = 6
        # ANSWER_TEXT = 7
        # ANSWER_CREATED_AT = 8
        scored_answers = "SELECT expected_opportunities.account_id,"\
            " survey_answer.id, expected_opportunities.response_id,"\
            " expected_opportunities.question_id, "\
          " CASE WHEN text = '%(yes)s' THEN (opportunity * 3)"\
          "      WHEN text = '%(moderate_improvement)s' THEN (opportunity * 2)"\
          "      WHEN text = '%(significant_improvement)s' THEN opportunity "\
          "      ELSE 0.0 END AS numerator,"\
          " CASE WHEN text IN"\
            " (%(yes_no)s) THEN (opportunity * 3) ELSE 0.0 END AS denominator,"\
            " expected_opportunities.path AS path,"\
            " survey_answer.text, survey_answer.created_at"\
            " FROM (%(expected_opportunities)s) AS expected_opportunities"\
            " LEFT OUTER JOIN survey_answer ON survey_answer.question_id"\
            " = expected_opportunities.question_id"\
            " AND survey_answer.response_id ="\
            " expected_opportunities.response_id" % {
                'yes': Consumption.YES,
                'moderate_improvement': Consumption.NEEDS_MODERATE_IMPROVEMENT,
                'significant_improvement':
                    Consumption.NEEDS_SIGNIFICANT_IMPROVEMENT,
                'yes_no': ','.join(["'%s'" % val
                    for val in Consumption.PRESENT + Consumption.ABSENT]),
                'expected_opportunities': self.get_expected_opportunities()}
        self._show_query_and_result(scored_answers)

        scored_answers_results = []
        with connection.cursor() as cursor:
            cursor.execute(scored_answers)
            scored_answers_results = cursor.fetchall()
        return scored_answers_results


    def populate_leafs(self, leafs, answers,
                       numerator_key='numerator',
                       denominator_key='denominator',
                       count_answers=True,
                       view_account=None):
        #pylint:disable=too-many-arguments
        """
        Populate all leafs with aggregated scores.
        """
        #pylint:disable=too-many-locals
        for prefix, values_tuple in six.iteritems(leafs):
            values = values_tuple[0]
            accounts = {}
            if not 'accounts' in values:
                values['accounts'] = {}
            accounts = values['accounts']
            for row in answers:
                answer_id = row[self.ANSWER_ID]
                path = row[self.QUESTION_PATH]
                account_id = row[self.ACCOUNT_ID]
                numerator = row[self.NUMERATOR]
                denominator = row[self.DENOMINATOR]
                if len(row) > self.ANSWER_CREATED_AT:
                    # ``populate_leafs`` is called for both answers
                    # and improvements.
                    created_at = row[self.ANSWER_CREATED_AT]
                else:
                    created_at = None
                if path.startswith(prefix):
                    if account_id == view_account and 'consumption' in values:
                        if count_answers:
                            values['consumption']['implemented'] = \
                                row[self.ANSWER_TEXT]
                        else:
                            values['consumption']['planned'] = True
                    if not account_id in accounts:
                        accounts[account_id] = {}
                    metrics = accounts[account_id]
                    if count_answers:
                        metrics.update({
                            'nb_answers': metrics.get('nb_answers', 0)
                                + (1 if answer_id is not None else 0),
                            'nb_questions': metrics.get('nb_questions', 0) + 1})
                    if not numerator_key in metrics:
                        metrics[numerator_key] = numerator
                    else:
                        metrics[numerator_key] += numerator
                    if not denominator_key in metrics:
                        metrics[denominator_key] = denominator
                    else:
                        metrics[denominator_key] += denominator
                    if created_at is not None:
                        if 'created_at' in metrics:
                            metrics['created_at'] = max(
                                created_at, metrics['created_at'])
                        else:
                            metrics['created_at'] = created_at
            for account_id, account_metrics in six.iteritems(accounts):
                if (count_answers and account_metrics['nb_answers']
                    != account_metrics['nb_questions']):
                    # If we don't have the same number of questions
                    # and answers, numerator and denominator are meaningless.
                    accounts[account_id].pop(numerator_key, None)
                    accounts[account_id].pop(denominator_key, None)

    def populate_rollup(self, rollup_tree,
                    numerator_key='numerator', denominator_key='denominator'):
        """
        Populate aggregated scores up the tree.
        """
        if len(rollup_tree[1].keys()) == 0:
            for account_id, metrics in six.iteritems(rollup_tree[0].get(
                    'accounts', {})):
                nb_answers = metrics.get('nb_answers', 0)
                nb_questions = metrics.get('nb_questions', 0)
                if nb_answers == nb_questions:
                    denominator = metrics.get(denominator_key, 0)
                    if denominator > 0:
                        metrics['normalized_score'] = int(
                            metrics[numerator_key] * 100.0 / denominator)
                        if 'improvement_numerator' in metrics:
                            metrics['improvement_score'] = int(
                                metrics['improvement_numerator'] * 100.0
                                / denominator)
                    else:
                        metrics['normalized_score'] = 0
            return
        values = rollup_tree[0]
        if not 'accounts' in values:
            values['accounts'] = {}
        accounts = values['accounts']
        slug = rollup_tree[0].get('slug', None)
        for node in six.itervalues(rollup_tree[1]):
            self.populate_rollup(node)
            for account_id, metrics in six.iteritems(
                    node[0].get('accounts', {})):
                if not account_id in accounts:
                    accounts[account_id] = {}
                agg_metrics = accounts[account_id]
                if not 'nb_answers' in agg_metrics:
                    agg_metrics['nb_answers'] = 0
                if not 'nb_questions' in agg_metrics:
                    agg_metrics['nb_questions'] = 0

                if 'created_at' in metrics:
                    if not 'created_at' in agg_metrics:
                        agg_metrics['created_at'] = metrics['created_at']
                    else:
                        agg_metrics['created_at'] = max(
                            agg_metrics['created_at'], metrics['created_at'])
                nb_answers = metrics['nb_answers']
                nb_questions = metrics['nb_questions']
                if slug != 'total-score' or nb_answers > 0:
                    # Aggregation of total scores is different. We only want to
                    # count scores for self-assessment that matter
                    # for an organization's industry.
                    agg_metrics['nb_answers'] += nb_answers
                    agg_metrics['nb_questions'] += nb_questions
                    for key in [numerator_key, denominator_key,
                                'improvement_numerator']:
                        agg_metrics[key] = agg_metrics.get(key, 0) + (
                            metrics.get(key, 0)
                            * node[0].get('score_weight', 1.0))
        for account_id, agg_metrics in six.iteritems(accounts):
            nb_answers = agg_metrics.get('nb_answers', 0)
            nb_questions = agg_metrics.get('nb_questions', 0)
            if nb_answers == nb_questions:
                # If we don't have the same number of questions
                # and answers, numerator and denominator are meaningless.
                denominator = agg_metrics.get(denominator_key, 0)
                agg_metrics.update({
                    'normalized_score': int(agg_metrics[numerator_key] * 100.0
                        / denominator) if denominator > 0 else 0})
                if 'improvement_numerator' in agg_metrics:
                    agg_metrics.update({
                        'improvement_score': int(
                            agg_metrics['improvement_numerator'] * 100.0
                            / denominator) if denominator > 0 else 0})
            else:
                agg_metrics.pop(numerator_key, None)
                agg_metrics.pop(denominator_key, None)

    def rollup_scores(self, root=None, root_prefix=None):
        """
        Returns a tree populated with scores per accounts.
        """
        self._report_queries("at rollup_scores entry point")
        start_time = monotonic.monotonic()
        rollup_tree = None
        roots = [root] if root is not None else None
        rollups = self.build_content_tree(roots, prefix=root_prefix,
            cut=TransparentCut())
        if len(rollups) <= 1:
            rollup_tree = ({}, rollups)
        else:
            for rup in six.itervalues(rollups):
                rollup_tree = rup
                break
        self._report_queries("(elapsed: %.2fs) rollup_tree generated"
            % (monotonic.monotonic() - start_time))
        if 'title' not in rollup_tree[0]:
            rollup_tree[0].update({
                "slug": "total-score", "title": "Total Score"})
        leafs = self.get_leafs(rollup_tree=rollup_tree)
        self._report_queries("(elapsed: %.2fs) leafs loaded"
            % (monotonic.monotonic() - start_time))
        self.populate_leafs(leafs, self.get_scored_answers())
        self.populate_leafs(leafs, self.get_scored_improvements(),
            count_answers=False, numerator_key='improvement_numerator',
            denominator_key='improvement_denominator')
        self._report_queries("(elapsed: %.2fs) leafs populated"
            % (monotonic.monotonic() - start_time))
        self.populate_rollup(rollup_tree)
        self._report_queries("(elapsed: %.2fs) rollup_tree populated"
            % (monotonic.monotonic() - start_time))
        return rollup_tree


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
            "slug":"total-score",
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
        root = trail[-1][0] if len(trail) > 0 else None
        rollup_tree = self.rollup_scores(root, from_root)
        self.create_distributions(rollup_tree,
            view_account=self.sample.account.pk)
        charts, complete = self.flatten_distributions(rollup_tree,
            prefix=from_root)
        total_score = None
        parts = from_root.split('/')
        if parts:
            slug = parts[-1]
            for chart in charts:
                if chart['slug'] == slug:
                    total_score = chart.copy()
                    break
        if not total_score:
            total_score = rollup_tree[0]
        if not total_score:
            total_score = {"nb_respondents": "-"}
        total_score.update({"slug": "total-score", "title": "Total Score"})
        if not complete and 'normalized_score' in total_score:
            del total_score['normalized_score']
        charts += [total_score]
        return charts

    def get(self, request, *args, **kwargs):
        return RestResponse(self.get_queryset())


class EnableScorecardAPIView(ToggleTagContentAPIView):

    added_tag = 'scorecard'


class DisableScorecardAPIView(ToggleTagContentAPIView):

    removed_tag = 'scorecard'


class ScoreWeightAPIView(TrailMixin, generics.RetrieveUpdateAPIView):

    lookup_field = 'path'
    serializer_class = ScoreWeightSerializer

    def retrieve(self, request, *args, **kwargs):
        trail = self.get_full_element_path(self.kwargs.get('path'))
        return RestResponse(self.serializer_class().to_representation({
            'weight': get_score_weight(trail[-1].tag)}))

    def update(self, request, *args, **kwargs):#pylint:disable=unused-argument
        partial = kwargs.pop('partial', False)
        serializer = self.serializer_class(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return RestResponse(serializer.data)

    def perform_update(self, serializer):
        trail = self.get_full_element_path(self.kwargs.get('path'))
        element = trail[-1]
        extra = {}
        try:
            extra = json.loads(element.tag)
        except (TypeError, ValueError):
            pass
        extra.update(serializer.validated_data)
        element.tag = json.dumps(extra, cls=DecimalEncoder)
        element.save()
