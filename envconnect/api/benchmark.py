# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging

from django.conf import settings
from django.db import connection
from django.http import Http404
from pages.models import PageElement
from rest_framework import generics
from rest_framework.response import Response as RestResponse
from survey.models import Answer, Response, SurveyModel

from ..mixins import ReportMixin
from ..models import Consumption, Improvement, ScoreWeight
from ..serializers import ScoreWeightSerializer


LOGGER = logging.getLogger(__name__)


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

    @property
    def sample(self):
        if not hasattr(self, '_sample'):
            try:
                # If we call ``get_or_create`` to do the same thing, it will
                # not call ``ResponseManager.create`` but ``QuerySet.create``
                # instead.
                self._sample = Response.objects.get(
                    account=self.account, survey__title=self.report_title)
            except Response.DoesNotExist:
                self._sample = Response.objects.create(account=self.account,
                    survey=SurveyModel.objects.get(title=self.report_title))
        return self._sample

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


    def build_aggregate_tree(self, roots=None, path=None):
        """
        Returns top level industries and flatten sub-systems as a tree
        that can be used to present benchmark charts.

        Example::
        [{
           "score_weight": 1.0
         }, {
           "/boxes-and-enclosures": [{
             "score_weight": 1.0,
             "title": "Boxes & enclosures",
             "slug": "boxes-and-enclosures"
           }, {
             "/boxes-and-enclosures/management-basics": [{
               "score_weight": 1.0,
               "text": "/media/envconnect/management-basics.png",
               "title": "Management"
               "tag": "management",
               "slug": "management-basics",
             }, {}],
             "/boxes-and-enclosures/production": [{
               "score_weight": 1.0
               "title": "Production",
               "slug": "production"
             },{
               "/boxes-and-enclosures/production/energy-efficiency": [{
                  "score_weight": 1.0,
                  "text": "/media/envconnect/production.png",
                  "title": "Production",
                  "subtitle": "Energy Efficiency",
                  "tag": "system",
                  "slug": "energy-efficiency"
             },{}],
           }],
         }]
        """
        details = {}
        if roots is None:
            roots = PageElement.objects.get_roots()
        if path is None:
            path = ''
        elif not path.startswith('/'):
            path = '/' + path
        for root in roots:
            base = path + '/' + root.slug
            levels = root.relationships.all()
            if root.tag and ('industry' in root.tag
                    or settings.TAG_SCORECARD in root.tag):
                transparent_to_rollover = False
            else:
                transparent_to_rollover = True
                for level in levels:
#                    transparent_to_rollover &= (level.tag is None
#                        or level.tag == '' or level.tag == 'heading')
                    transparent_to_rollover &= (level.tag is None
                        or settings.TAG_SCORECARD not in level.tag)
            metrics = {
                'slug': root.slug,
                'title': root.title,
                'score_weight': ScoreWeight.objects.from_path(base)
            }
            if root.text:
                metrics.update({'text': root.text})
            if root.tag:
                metrics.update({'tag': root.tag})
            if transparent_to_rollover:
                details.update({base: (metrics, {})})
            else:
                level_details = self.build_aggregate_tree(
                    roots=levels, path=base)
                level_details[0].update(metrics)
                for level_detail in level_details[1].values():
                    if settings.TAG_SCORECARD in level_detail[0].get('tag', ''):
                        level_detail[0].update({
                            'subtitle': level_detail[0].get('title', ''),
                            'title': root.title,
                            'text': root.text})
                details.update({base: level_details})
        return ({
            'score_weight': ScoreWeight.objects.from_path(path)
        }, details)

    def get_drilldown(self, rollup_tree, prefix):
        accounts = None
        node = rollup_tree[1].get(prefix, None)
        if node:
            accounts = rollup_tree[0].get('accounts', {})
        elif prefix == 'totals' or rollup_tree[0].get('slug', '') == prefix:
            accounts = rollup_tree[0].get('accounts', {})
        else:
            for node in rollup_tree[1].itervalues():
                accounts = self.get_drilldown(node, prefix)
                if accounts is not None:
                    break
        # Filter out accounts whose score cannot be computed.
        if accounts is not None:
            all_accounts = accounts
            accounts = {}
            for account_id, account_metrics in all_accounts.iteritems():
                normalized_score = account_metrics.get('normalized_score', None)
                if normalized_score is not None:
                    accounts[account_id] = account_metrics

        return accounts

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
        elif not path.startswith('/'):
            path = '/' + path

        if len(rollup_tree[1].keys()) == 0:
            return {path: rollup_tree}
        leafs = {}
        for key, level_detail in rollup_tree[1].iteritems():
            leafs.update(self.get_leafs(level_detail, path=key))
        return leafs

    @staticmethod
    def get_charts(groups, path=None):
        charts = []
        complete = True
        if path is None:
            path = '/'
        for icon_tuple in groups:
            icon = {
                'slug': icon_tuple[0].slug,
                'title': icon_tuple[0].title,
                'text': icon_tuple[0].text,
                'tag': icon_tuple[0].tag,
                'score_weight': ScoreWeight.objects.from_path(
                    path + '/' + icon_tuple[0].slug)
            }
            nb_answers = getattr(icon_tuple[0], 'nb_answers', 0)
            nb_questions = getattr(icon_tuple[0], 'nb_questions', 1)
            complete &= (nb_answers == nb_questions)
            transparent_to_rollover = True
            for practice_tuple in icon_tuple[1]:
                transparent_to_rollover &= (
                    practice_tuple[0].tag is None
                    or settings.TAG_SCORECARD not in practice_tuple[0].tag)
            if transparent_to_rollover:
                practice = {
                    'nb_questions': getattr(icon_tuple[0], 'nb_questions', 0),
                    'nb_answers': nb_answers,
                    'distribution': getattr(icon_tuple[0], 'distribution', {})
                }
                practice.update(icon)
                charts += [practice]
            else:
                for practice_tuple in icon_tuple[1]:
                    if (practice_tuple[0].tag
                        and settings.TAG_SCORECARD in practice_tuple[0].tag):
                        practice = {
                            'slug': practice_tuple[0].slug,
                            'title': icon_tuple[0].title,
                            'text': icon_tuple[0].text,
                            'tag': icon_tuple[0].tag,
                            'subtitle': practice_tuple[0].title,
                            'score_weight': ScoreWeight.objects.from_path(
                                path + '/' + icon_tuple[0].slug
                                + '/' + practice_tuple[0].slug),
                            'nb_questions': getattr(
                                practice_tuple[0], 'nb_questions', 0),
                            'nb_answers': getattr(
                                practice_tuple[0], 'nb_answers', 0),
                            'distribution': getattr(
                                practice_tuple[0], 'distribution', {})
                        }
                        charts += [practice]
        return charts, complete


    def create_distributions(self, rollup_tree, view_account=None):
        """
        Create a tree with distributions of scores from a rollup tree.
        """
        #pylint:disable=too-many-locals
        result_metrics = {
            'tag': rollup_tree[0].get('tag', ""),
            'subtitle': rollup_tree[0].get('subtitle', ""),
            'title': rollup_tree[0].get('title', ""),
            'text': rollup_tree[0].get('text', ""),
            'score_weight': rollup_tree[0].get('score_weight', ""),
            'slug': rollup_tree[0].get('slug', ""),
        }
        highest_normalized_score = 0
        sum_normalized_scores = 0
        nb_respondents = 0
        distribution = None
        for account_id_str, account_metrics in rollup_tree[0].get(
                'accounts', {}).iteritems():
            if account_id_str is None: # XXX why is that?
                continue
            account_id = int(account_id_str)

            if account_id == view_account:
                result_metrics.update(account_metrics)
            normalized_score = account_metrics.get('normalized_score', None)
            if normalized_score is None:
                continue

            nb_respondents += 1
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

        details = {}
        for node_path, node_metrics in rollup_tree[1].iteritems():
            details.update({node_path: self.create_distributions(
                node_metrics, view_account=view_account)})

        if distribution is not None:
            if nb_respondents > 0:
                avg_normalized_score = sum_normalized_scores / nb_respondents
            else:
                avg_normalized_score = 0
            result_metrics.update({
                'nb_respondents': nb_respondents,
                'highest_normalized_score': highest_normalized_score,
                'avg_normalized_score': avg_normalized_score,
                'distribution': distribution
            })
        return (result_metrics, details)


    def flatten_distributions(self, distribution_tree, prefix=None):
        """
        Flatten the tree into a list of charts.
        """
        if prefix and not prefix.startswith('/'):
            prefix = '/' + prefix
        if not distribution_tree[1]:
            return [], True
        charts = []
        complete = True
        for key, chart in distribution_tree[1].iteritems():
            if prefix and key.startswith(prefix):
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
    def get_distributions(numerators, denominators, view_response=None):
        distribution = {
            'x' : ["0-25%", "25-50%", "50-75%", "75-100%"],
            'y' : [0 for _ in range(4)],
            'normalized_score': 0,  # instead of 'ukn.' to avoid js error.
            'organization_rate': ""
        }
        for response, numerator in numerators.iteritems():
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


    def attach_benchmarks_recursive(self, root, path=None, view_response=None):
        #pylint:disable=too-many-locals,too-many-statements
        if path is None:
            path = '/' + root[0].slug
        score_weight = ScoreWeight.objects.from_path(path)
        setattr(root[0], 'score_weight', score_weight)
        numerators = {}
        denominators = {}
        if len(root[1]) == 0:
            # Look for answers
            nb_respondents = 0
            nb_questions = 0
            nb_answers = 0
            rate = 0
            implemented = False
            consumption = root[0].consumption
            if consumption:
                nb_questions = 1
                answers = Answer.objects.filter(question=consumption)
                nb_respondents = answers.count()
                if nb_respondents:
                    nb_yes_no = answers.filter(
                        text__in=(Consumption.PRESENT + Consumption.ABSENT)
                    ).count()
                    if nb_yes_no:
                        rate = (answers.filter(
                            text__in=Consumption.PRESENT).count() * 100
                        ) / nb_yes_no
                opportunity = consumption.avg_value * ((100 + rate) / 100.0)
                implemented = ''
                for answer in answers:
                    if answer.response == view_response:
                        implemented = answer.text
                    if answer.text in Consumption.PRESENT:
                        numerators[answer.response] = opportunity
                        denominators[answer.response] = opportunity
                    else:
                        numerators[answer.response] = 0
                        if answer.text in Consumption.ABSENT:
                            denominators[answer.response] = opportunity
                        else:
                            denominators[answer.response] = 0
                # Is this consumption part of the improvement planning.
                planned = False
                if root[0].consumption:
                    planned = Improvement.objects.filter(account=self.account,
                        consumption=root[0].consumption).exists()
                if view_response in numerators:
                    nb_answers = 1
                setattr(consumption, 'nb_respondents', nb_respondents)
                setattr(consumption, 'implemented', implemented)
                setattr(consumption, 'planned', planned)
                setattr(consumption, 'opportunity', opportunity)
                setattr(consumption, 'rate', rate)
            setattr(root[0], 'nb_answers', nb_answers)
            setattr(root[0], 'nb_questions', nb_questions)
            setattr(root[0], 'denominators', denominators)
            setattr(root[0], 'numerators', numerators)
            setattr(root[0], 'nb_respondents', nb_respondents)
            setattr(root[0], 'rate', rate)
        else:
            nb_answers = 0
            nb_questions = 0
            for node in root[1]:
                self.attach_benchmarks_recursive(node,
                    path='%s/%s' % (path, node[0].slug),
                    view_response=view_response)
                nb_questions += node[0].nb_questions
                nb_answers += node[0].nb_answers
                for response, numerator in node[0].numerators.iteritems():
                    if not response in numerators:
                        numerators[response] = 0
                        denominators[response] = 0
                    numerators[response] += numerator * node[0].score_weight
                    denominators[response] += (
                        node[0].denominators[response] * node[0].score_weight)

            # Create distribution from numerators
            distribution = self.get_distributions(numerators, denominators,
                view_response=view_response)
            setattr(root[0], 'nb_answers', nb_answers)
            setattr(root[0], 'nb_questions', nb_questions)
            setattr(root[0], 'denominators', denominators)
            setattr(root[0], 'numerators', numerators)
            setattr(root[0], 'distribution', distribution)

    def attach_benchmarks(self, root, view_response=None):
        self.attach_benchmarks_recursive(root, view_response=view_response)
        highest_normalized_score = 0
        sum_normalized_scores = 0
        for response, numerator in root[0].numerators.iteritems():
            denominator = root[0].denominators.get(response, 0)
            if denominator != 0:
                normalized_score = int(numerator * 100 / denominator)
            else:
                normalized_score = 0
            if normalized_score > highest_normalized_score:
                highest_normalized_score = normalized_score
            sum_normalized_scores += normalized_score
        root[0].nb_respondents = len(root[0].numerators)
        root[0].highest_normalized_score = highest_normalized_score
        if root[0].nb_respondents > 0:
            root[0].avg_normalized_score = (
                sum_normalized_scores / root[0].nb_respondents)
        else:
            root[0].avg_normalized_score = 0


    def get_opportunities(self):
        """
        Returns a list of question and opportunity associated to each question.
        """
        if True:
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
            " expected_opportunities.question_id, opportunity AS numerator,"\
            " opportunity AS denominator,"\
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
            " expected_opportunities.question_id, CASE WHEN text IN %(yes)s"\
            " THEN opportunity ELSE 0.0 END AS numerator, CASE WHEN text IN"\
            " %(yes_no)s THEN opportunity ELSE 0.0 END AS denominator,"\
            " expected_opportunities.path AS path,"\
            " survey_answer.text, survey_answer.created_at"\
            " FROM (%(expected_opportunities)s) AS expected_opportunities"\
            " LEFT OUTER JOIN survey_answer ON survey_answer.question_id"\
            " = expected_opportunities.question_id"\
            " AND survey_answer.response_id ="\
            " expected_opportunities.response_id" % {
                'yes': tuple(Consumption.PRESENT),
                'yes_no': tuple(Consumption.PRESENT + Consumption.ABSENT),
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
                       count_answers=True):
        #pylint:disable=too-many-arguments
        """
        Populate all leafs with aggregated scores.
        """
        #pylint:disable=too-many-locals
        for prefix, values_tuple in leafs.iteritems():
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
            for account_id, account_metrics in accounts.iteritems():
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
            for account_id, metrics in rollup_tree[0].get(
                    'accounts', {}).iteritems():
                nb_answers = metrics.get('nb_answers', 0)
                nb_questions = metrics.get('nb_questions', 0)
                if nb_answers == nb_questions:
                    denominator = metrics.get(denominator_key, 0)
                    if denominator > 0:
                        metrics['normalized_score'] = int(
                            metrics[numerator_key] * 100.0 / denominator)
                    else:
                        metrics['normalized_score'] = 0
            return
        values = rollup_tree[0]
        if not 'accounts' in values:
            values['accounts'] = {}
        accounts = values['accounts']
        slug = rollup_tree[0].get('slug', None)
        for node in rollup_tree[1].itervalues():
            self.populate_rollup(node)
            for account_id, metrics in node[0].get('accounts', {}).iteritems():
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
        for account_id, agg_metrics in accounts.iteritems():
            nb_answers = agg_metrics.get('nb_answers', 0)
            nb_questions = agg_metrics.get('nb_questions', 0)
            if nb_answers == nb_questions:
                # If we don't have the same number of questions
                # and answers, numerator and denominator are meaningless.
                denominator = agg_metrics.get(denominator_key, 0)
                agg_metrics.update({
                    'normalized_score': int(agg_metrics[numerator_key] * 100.0
                        / denominator) if denominator > 0 else 0})
            else:
                agg_metrics.pop(numerator_key, None)
                agg_metrics.pop(denominator_key, None)

    def rollup_scores(self):
        """
        Returns a tree populated with scores per accounts.
        """
        rollup_tree = self.build_aggregate_tree()
        if 'title' not in rollup_tree[0]:
            rollup_tree[0].update({
                "slug": "total-score", "title": "Total Score"})
        leafs = self.get_leafs(rollup_tree=rollup_tree)
        self.populate_leafs(leafs, self.get_scored_answers())
        self.populate_leafs(leafs, self.get_scored_improvements(),
            count_answers=False, numerator_key='improvement_numerator',
            denominator_key='improvement_denominator')
        self.populate_rollup(rollup_tree)
        return rollup_tree


class BenchmarkAPIView(BenchmarkMixin, generics.GenericAPIView):

    def get_queryset(self):
        #pylint:disable=too-many-locals
        _, trail = self.breadcrumbs
        # Returns the total score and industry level charts, regardless
        # of the actual from_path.
        # XXX It could be better to achieve the same result by changing
        # the API path in the template.
        root = self._build_tree(trail[0][0], nocuts=True)
        try:
            view_response = self.sample
        except Http404:
            view_response = None
        total_score = {"slug": "total-score", "title": "Total Score"}

        rollup_tree = self.rollup_scores()
        distributions_tree = self.create_distributions(
            rollup_tree, view_account=view_response.account.pk)
        prefix = str(root[0])
        if not prefix.startswith('/'):
            prefix = '/' + prefix
        charts, complete = self.flatten_distributions(
            distributions_tree, prefix=prefix)
        if complete:
            root_leaf = distributions_tree[1][prefix][0]
            total_score.update({
                "nb_respondents": root_leaf.get('nb_respondents'),
                "scores": {
                  "normalized_score": root_leaf.get(
                      'normalized_score', 0),
                  "highest_normalized_score": root_leaf.get(
                      'highest_normalized_score', 0),
                  "avg_normalized_score": root_leaf.get(
                      'avg_normalized_score', 0)
                }})
            denominator = root_leaf.get('denominator', 0)
            if denominator:
                total_score.update({
                  "improvement_score": "(+%.1f)" % (root_leaf.get(
                      'improvement_numerator', 0) / denominator)})

        charts += [total_score]
        return charts

    def get(self, request, *args, **kwargs):
        return RestResponse(self.get_queryset())


class ScoreWeightAPIView(generics.RetrieveUpdateAPIView):

    lookup_field = 'path'
    queryset = ScoreWeight.objects.all()
    serializer_class = ScoreWeightSerializer

    def get_object(self):
        path = self.kwargs.get('path')
        try:
            obj = self.get_queryset().get(path=path)
        except ScoreWeight.DoesNotExist:
            obj = ScoreWeight(path=path)
        return obj
