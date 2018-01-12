# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

from __future__ import absolute_import
from __future__ import unicode_literals

import datetime, json, logging

from django.conf import settings
from django.db import connection
from django.utils import six
from pages.mixins import TrailMixin
from rest_framework import generics
from rest_framework.response import Response

from .best_practices import DecimalEncoder, ToggleTagContentAPIView
from ..mixins import ReportMixin, TransparentCut
from ..models import Consumption, get_score_weight
from ..serializers import ScoreWeightSerializer


LOGGER = logging.getLogger(__name__)


class BenchmarkMixin(ReportMixin):

    ACCOUNT_ID = 0
    ANSWER_ID = 1
    SAMPLE_ID = 2
    QUESTION_ID = 3
    NUMERATOR = 4
    DENOMINATOR = 5
    QUESTION_PATH = 6
    ANSWER_CREATED_AT = 7
    ANSWER_MEASURED = 8

    @staticmethod
    def _show_query_and_result(raw_query, show=False):
        if show:
            LOGGER.debug("%s\n", raw_query)
            with connection.cursor() as cursor:
                cursor.execute(raw_query, params=None)
                count = 0
                for row in cursor.fetchall():
                    LOGGER.debug(str(row))
                    count += 1
                LOGGER.debug("%d row(s)", count)

    def decorate_with_breadcrumbs(self, rollup_tree,
                                  icon=None, tag=None, breadcrumbs=None):
        """
        When this method returns each node in the rollup_tree will have
        and icon and breadcumbs attributes. If a node does not have or
        has an empty tag attribute, it will be set to the value of the
        first parent's tag which is meaningful.
        """
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

    def get_charts(self, rollup_tree):
        charts = []
        icon_tag = rollup_tree[0].get('tag', "")
        if icon_tag and settings.TAG_SCORECARD in icon_tag:
            charts += [rollup_tree[0]]
        for _, icon_tuple in six.iteritems(rollup_tree[1]):
            sub_charts = self.get_charts(icon_tuple)
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

    def get_expected_opportunities(self, is_planned=None):
        questions_with_opportunity = Consumption.objects.get_opportunities_sql(
            filter_out_testing=self._get_filter_out_testing())
        # All expected questions for each sample
        # decorated with ``opportunity``.
        #
        # If we are only looking for all expected questions for each sample,
        # then the query can be simplified by using the survey_question table
        # directly.
        sep = ""
        additional_filters = ""
        if is_planned is not None:
            additional_filters = "survey_sample.extra = '%s'" % (
                "is_planned" if is_planned else "")
            sep = "AND "
        if self._get_filter_out_testing():
            additional_filters += "%ssurvey_sample.id NOT IN (%s)" % (
                sep, ', '.join(self._get_filter_out_testing()))
        if additional_filters:
            additional_filters = "WHERE %s" % additional_filters
        expected_opportunities = """SELECT
  questions_with_opportunity.question_id AS question_id,
  samples.sample_id AS sample_id,
  samples.is_planned AS is_planned,
  samples.account_id AS account_id,
  questions_with_opportunity.opportunity,
  questions_with_opportunity.path AS path
FROM (%(questions_with_opportunity)s) AS questions_with_opportunity
INNER JOIN (
    SELECT survey_enumeratedquestions.question_id AS question_id,
           survey_sample.account_id AS account_id,
           survey_sample.id AS sample_id,
           survey_sample.extra AS is_planned
        FROM survey_sample INNER JOIN survey_enumeratedquestions
        ON survey_sample.survey_id = survey_enumeratedquestions.campaign_id
         %(additional_filters)s) AS samples
ON questions_with_opportunity.question_id = samples.question_id
""" % {'questions_with_opportunity': questions_with_opportunity,
       'additional_filters': additional_filters}
        self._show_query_and_result(expected_opportunities)
        return expected_opportunities

    def get_answer_with_account(self, is_planned=None):
        sep = ""
        additional_filters = ""
        if is_planned is not None:
            additional_filters = "survey_sample.extra = '%s'" % (
                "is_planned" if is_planned else "")
            sep = "AND "
        if self._get_filter_out_testing():
            additional_filters += "%ssurvey_sample.id NOT IN (%s)" % (
                sep, ', '.join(self._get_filter_out_testing()))
        if additional_filters:
            additional_filters = "WHERE %s" % additional_filters
        query = """SELECT survey_answer.id AS id,
    question_id,
    sample_id,
    account_id,
    survey_answer.created_at AS created_at,
    measured,
    survey_sample.extra AS is_planned
FROM survey_answer INNER JOIN survey_sample
ON survey_answer.sample_id = survey_sample.id
%(additional_filters)s
""" % {'additional_filters': additional_filters}
        self._show_query_and_result(query)
        return query

    def get_scored_answers(self, is_planned=None):
        """
        Set is_planned to `True` for assessment results only or is_planned
        to `False` for improvement results only. Otherwise both.
        """
        # All expected answers with their scores.
        # ACCOUNT_ID = 0
        # ANSWER_ID = 1
        # SAMPLE_ID = 2
        # QUESTION_ID = 3
        # NUMERATOR = 4
        # DENOMINATOR = 5
        # QUESTION_PATH = 6
        # ANSWER_CREATED_AT = 7
        # ANSWER_MEASURED = 8
        # SAMPLE_IS_PLANNED = 9 (assessment or improvement)
        scored_answers = "SELECT expected_opportunities.account_id,"\
            " answers.id AS answer_id,"\
            " expected_opportunities.sample_id,"\
            " expected_opportunities.question_id, "\
          " CASE WHEN measured = %(yes)s THEN (opportunity * 3)"\
          "      WHEN measured = %(moderate_improvement)s THEN (opportunity * 2)"\
          "      WHEN measured = %(significant_improvement)s THEN opportunity "\
          "      ELSE 0.0 END AS numerator,"\
          " CASE WHEN measured IN"\
            " (%(yes_no)s) THEN (opportunity * 3) ELSE 0.0 END AS denominator,"\
            " expected_opportunities.path AS path,"\
            " answers.created_at,"\
            " answers.measured,"\
            " expected_opportunities.is_planned"\
            " FROM (%(expected_opportunities)s) AS expected_opportunities"\
            " LEFT OUTER JOIN (%(answers)s) AS answers"\
            " ON answers.question_id"\
            " = expected_opportunities.question_id"\
            " AND answers.sample_id ="\
            " expected_opportunities.sample_id" % {
                'yes': Consumption.YES,
                'moderate_improvement': Consumption.NEEDS_MODERATE_IMPROVEMENT,
                'significant_improvement':
                    Consumption.NEEDS_SIGNIFICANT_IMPROVEMENT,
                'yes_no': Consumption._relevent_as_sql(),
                'expected_opportunities':
                    self.get_expected_opportunities(is_planned=is_planned),
                'answers': self.get_answer_with_account(is_planned=is_planned)}
        self._show_query_and_result(scored_answers)
        return scored_answers

    def get_scored_assessments(self):
        """
        Compute scores specifically related to assessments.
        """
        # All expected improvements with their scores.
        scored_assessments = self.get_scored_answers(is_planned=False)
        self._show_query_and_result(scored_assessments)
        return scored_assessments

    def get_scored_improvements(self):
        """
        Compute scores specifically related to improvements.
        """
        # All expected improvements with their scores.
        scored_improvements = self.get_scored_answers(is_planned=True)
        self._show_query_and_result(scored_improvements)
        return scored_improvements

    def populate_leafs(self, leafs, answers):
        """
        Populate all leafs with aggregated scores.
        """
        #pylint:disable=too-many-locals
        for prefix, values_tuple in six.iteritems(leafs):
            values = values_tuple[0]
            agg_scores = """SELECT account_id, sample_id, is_planned,
    COUNT(answer_id) AS nb_answers,
    COUNT(*) AS nb_questions,
    SUM(numerator) AS numerator,
    SUM(denominator) AS denominator,
    MAX(created_at) AS last_activity_at
FROM (%(answers)s) AS answers
WHERE path LIKE '%(prefix)s%%'
GROUP BY account_id, sample_id, is_planned;""" % {
    'answers': answers, 'prefix': prefix}
            self._show_query_and_result(agg_scores)
            with connection.cursor() as cursor:
                cursor.execute(agg_scores, params=None)
                for agg_score in cursor.fetchall():
                    account_id = agg_score[0]
                    #sample_id = agg_score[1]
                    is_planned = agg_score[2]
                    nb_answers = agg_score[3]
                    nb_questions = agg_score[4]
                    numerator = agg_score[5]
                    denominator = agg_score[6]
                    created_at = agg_score[7]
                    if not 'accounts' in values:
                        values['accounts'] = {}
                    accounts = values['accounts']
                    if not account_id in accounts:
                        accounts[account_id] = {}
                    if is_planned:
                        accounts[account_id].update({
                            'improvement_numerator': numerator,
                            'improvement_denominator': denominator})
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
                            'created_at': created_at
                        })
                        if nb_questions == nb_answers:
                            accounts[account_id].update({
                                'numerator': numerator,
                                'denominator': denominator})

    @staticmethod
    def _normalize(scores, score_weight_from_root=1.0, normalize_to_one=False):
        """
        Adds keys ``normalized_score`` and ``improvement_score``
        into the dictionnary *scores* when keys ``nb_answers``
        and ``nb_questions`` are equal and (``numerator``, ``denominator``
        ``improvement_numerator``) are present.

        *score_weight_from_root* is the compound weight (through multiplication)
        from the root to the node. That's the factor for how much a question
        will actually contribute to the final score.

        The ``score_weight`` on a node really represents a percentage the node
        contributes to the parent score. This means we need to normalize the
        node score before using it.
        """
        numerator_key = 'numerator'
        denominator_key = 'denominator'
        nb_answers = scores.get('nb_answers', 0)
        nb_questions = scores.get('nb_questions', 0)
        if nb_answers == nb_questions:
            # If we don't have the same number of questions
            # and answers, numerator and denominator are meaningless.
            denominator = scores.get(denominator_key, 0)
            if denominator > 0:
                scores['normalized_score'] = int(
                    scores[numerator_key] * 100.0 / denominator)
                if 'improvement_numerator' in scores:
                    scores['improvement_score'] = (
                        scores['improvement_numerator'] * 100.0
                        / denominator)
                if normalize_to_one:
                    if numerator_key in scores:
                        scores[numerator_key] /= denominator
                    if 'improvement_numerator' in scores:
                        scores['improvement_numerator'] /= denominator
                    scores[denominator_key] = 1.0
            else:
                scores['normalized_score'] = 0
        else:
            scores.pop(numerator_key, None)
            scores.pop(denominator_key, None)


    def populate_rollup(self, rollup_tree, normalize_to_one,
                        score_weight_from_root=1.0):
        """
        Recursively populate the tree *rollup_tree* with aggregated scores.

        A rollup_tree is recursively defined as a tuple of two dictionnaries.
        The first dictionnary stores the fields on the node while the second
        dictionnary contains the leafs keyed by path.

        Example:

            [{
                "slug": "totals",
                "title": "Total Score",
                "tag": ["scorecard"]
             },
             {
                "/boxes-and-enclosures": [{
                    "path": "/boxes-and-enclosures",
                    "slug": "sustainability-boxes-and-enclosures",
                    "title": "Boxes & enclosures",
                    "tag": "{\"tags\":[\"sustainability\"]}",
                    "score_weight": 1.0,
                    "transparent_to_rollover": false
                },
                {
                    "/boxes-and-enclosures/management-basics": [{
                        "path": "/boxes-and-enclosures/management-basics",
                        "slug": "management-basics",
                        "title": "Management",
                        "tag": "{\"tags\":[\"management\",\"scorecard\"]}",
                        "score_weight": 1.0,
                        "transparent_to_rollover": false,
                        "accounts": {
                            "6": {
                                "nb_answers": 0,
                                "nb_questions": 2,
                                "created_at": null
                            },
                            "7": {
                                "nb_answers": 2,
                                "nb_questions": 2,
                                "created_at": "2017-12-20 18:48:40.666239",
                                "numerator": 4.0,
                                "denominator": 10.5,
                                "improvement_numerator": 1.5,
                                "improvement_denominator": 4.5
                            },
                        }
                    },
                    {}
                    ],
                    "/boxes-and-enclosures/design": [{
                        "path": "/boxes-and-enclosures/design",
                        "slug": "design",
                        "title": "Design",
                        "tag": "{\"tags\":[\"scorecard\"]}",
                        "score_weight": 1.0,
                        "transparent_to_rollover": false,
                        "accounts": {
                            "6": {
                                "nb_answers": 0,
                                "nb_questions": 2,
                                "created_at": null
                            },
                            "7": {
                                "nb_answers": 0,
                                "nb_questions": 2,
                                "created_at": null,
                                "improvement_numerator": 0.0,
                                "improvement_denominator": 0.0
                            },
                        }
                    },
                    {}
                    ],
                    "/boxes-and-enclosures/production": [{
                        "path": "/boxes-and-enclosures/production",
                        "slug": "production",
                        "title": "Production",
                        "tag": "{\"tags\":[\"scorecard\"]}",
                        "score_weight": 1.0,
                        "transparent_to_rollover": false,
                        "text": "/envconnect/static/img/production.png"
                    },
                    {
                        "/boxes-and-enclosures/production/energy-efficiency": [{
                  "path": "/boxes-and-enclosures/production/energy-efficiency",
                            "slug": "energy-efficiency",
                            "title": "Energy Efficiency",
                            "tag": "{\"tags\":[\"system\",\"scorecard\"]}",
                            "score_weight": 1.0,
                            "transparent_to_rollover": false,
                            "accounts": {
                                "6": {
                                    "nb_answers": 1,
                                    "nb_questions": 4,
                                    "created_at": "2016-05-01 00:36:19.448000"
                                },
                                "7": {
                                    "nb_answers": 0,
                                    "nb_questions": 4,
                                    "created_at": null,
                                    "improvement_numerator": 0.0,
                                    "improvement_denominator": 0.0
                                },
                            }
                        },
                        {}
                        ]
                    }
                }]
             }]
        """
        numerator_key = 'numerator'
        denominator_key = 'denominator'
        values = rollup_tree[0]
        slug = values.get('slug', None)
        root_score_weight = values.get('score_weight', 1.0)

        if not 'accounts' in values:
            values['accounts'] = {}
        accounts = values['accounts']

        # If the total of the children weights is 1.0, we are dealing
        # with percentages so we need to normalize all children numerators
        # and denominators to compute this node score.
        total_score_weight = 0
        for node in six.itervalues(rollup_tree[1]):
            score_weight = node[0].get('score_weight', 1.0)
            total_score_weight += score_weight
        normalize_children = ((1.0 - 0.01) < total_score_weight
            and total_score_weight < (1.0 + 0.01))

        for node in six.itervalues(rollup_tree[1]):
            self.populate_rollup(node, normalize_children, # recursive call
                score_weight_from_root=(score_weight_from_root
                    * root_score_weight))
            score_weight = node[0].get('score_weight', 1.0)
            for account_id, scores in six.iteritems(
                    node[0].get('accounts', {})):
                if not account_id in accounts:
                    accounts[account_id] = {}
                agg_scores = accounts[account_id]
                if not 'nb_answers' in agg_scores:
                    agg_scores['nb_answers'] = 0
                if not 'nb_questions' in agg_scores:
                    agg_scores['nb_questions'] = 0

                if 'created_at' in scores:
                    if not ('created_at' in agg_scores and isinstance(
                            agg_scores['created_at'], datetime.datetime)):
                        agg_scores['created_at'] = scores['created_at']
                    elif (isinstance(
                            agg_scores['created_at'], datetime.datetime) and
                          isinstance(scores['created_at'], datetime.datetime)):
                        agg_scores['created_at'] = max(
                            agg_scores['created_at'], scores['created_at'])
                nb_answers = scores['nb_answers']
                nb_questions = scores['nb_questions']
                if slug != 'totals' or nb_answers > 0:
                    # Aggregation of total scores is different. We only want to
                    # count scores for self-assessment that matter
                    # for an organization's industry.
                    agg_scores['nb_answers'] += nb_answers
                    agg_scores['nb_questions'] += nb_questions
                    for key in [numerator_key, denominator_key,
                                'improvement_numerator']:
                        agg_scores[key] = agg_scores.get(key, 0) + (
                            scores.get(key, 0) * score_weight)

        for account_id, scores in six.iteritems(accounts):
            self._normalize(scores,
                score_weight_from_root=score_weight_from_root,
                normalize_to_one=normalize_to_one)


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
        rollup_tree = ({}, rollups)
        self._report_queries("rollup_tree generated")
        if 'title' not in rollup_tree[0]:
            rollup_tree[0].update({
                'slug': "totals",
                'title': "Total Score",
                'tag': [settings.TAG_SCORECARD]})
        leafs = self.get_leafs(rollup_tree=rollup_tree)
        self._report_queries("leafs loaded")
        self.populate_leafs(leafs, self.get_scored_answers())
        self._report_queries("leafs populated")
        self.populate_rollup(rollup_tree, True)
        self._report_queries("rollup_tree populated")
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
            view_account=self.sample.account.pk)
        self.decorate_with_breadcrumbs(rollup_tree)
        charts, complete = self.flatten_distributions(rollup_tree,
            prefix=from_root)
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
            total_score = {"nb_respondents": "-"}
        total_score.update({"slug": "totals", "title": "Total Score"})
        # ... and the following 2 lines together, pylint does not blow up...
        if not complete and 'normalized_score' in total_score:
            del total_score['normalized_score']
        charts += [total_score]
        return charts

    def get(self, request, *args, **kwargs): #pylint:disable=unused-argument
        return Response(self.get_queryset())


class EnableScorecardAPIView(ToggleTagContentAPIView):

    added_tag = 'scorecard'


class DisableScorecardAPIView(ToggleTagContentAPIView):

    removed_tag = 'scorecard'


class ScoreWeightAPIView(TrailMixin, generics.RetrieveUpdateAPIView):

    lookup_field = 'path'
    serializer_class = ScoreWeightSerializer

    def retrieve(self, request, *args, **kwargs):
        trail = self.get_full_element_path(self.kwargs.get('path'))
        return Response(self.serializer_class().to_representation({
            'weight': get_score_weight(trail[-1].tag)}))

    def update(self, request, *args, **kwargs):#pylint:disable=unused-argument
        partial = kwargs.pop('partial', False)
        serializer = self.serializer_class(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

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
