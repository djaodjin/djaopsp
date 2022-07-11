# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from __future__ import unicode_literals

import logging
from collections import namedtuple

from deployutils.helpers import datetime_or_now
from django.db import connection
from pages.models import PageElement, flatten_content_tree
from survey.models import Unit
from survey.utils import is_sqlite3

from ..compat import six
from ..models import ScorecardCache
from ..scores.base import (ScoreCalculator as ScoreCalculatorBase,
    populate_rollup)
from ..utils import (get_completed_assessments_at_by, get_highlights,
    get_scores_tree, get_leafs)


LOGGER = logging.getLogger(__name__)

YES = 1                           # 'Yes'
NEEDS_MODERATE_IMPROVEMENT = 2    # 'Mostly yes'
NEEDS_SIGNIFICANT_IMPROVEMENT = 3 # 'Mostly no'
NO = 4                            #pylint:disable=invalid-name
NOT_APPLICABLE = 5                # 'Not applicable'

PRESENT = (YES, NEEDS_MODERATE_IMPROVEMENT)
ABSENT = (NO, NEEDS_SIGNIFICANT_IMPROVEMENT)

ASSESSMENT_ANSWERS = {
    YES: 'Yes',
    NEEDS_MODERATE_IMPROVEMENT: 'Mostly yes',
    NEEDS_SIGNIFICANT_IMPROVEMENT: 'Mostly no',
    NO: 'No',
    NOT_APPLICABLE: 'Not applicable'
}

ASSESSMENT_UNIT = 'assessment'
SCORE_UNIT = 'points'


class ScoreCalculator(ScoreCalculatorBase):
    """
    Abstract base class to compute scores on individual answers
    for an assessment
    """
    def __init__(self):
        self.assessment_unit_id = Unit.objects.get(slug=ASSESSMENT_UNIT).pk
        self.points_unit_id = Unit.objects.get(slug=SCORE_UNIT).pk

    def get_opportunity(self, campaign,
                        includes=None, excludes=None, prefix=None,
                        last_frozen_assessments=None):
        """
        Lists opportunity (intrisic and peers-based)
        """
        #pylint:disable=too-many-arguments,too-many-locals
        # The call to `get_expected_opportunities` within `get_scored_answers`
        # will insure all questions for the assessment are picked up, either
        # they have an answer or not.
        # This is done by listing all question in `get_opportunities_sql`
        # and filtering them out through the `survey_enumeratedquestions`
        # table in `get_expected_opportunities`.
        if not last_frozen_assessments:
            last_frozen_assessments = get_completed_assessments_at_by(
                campaign, excludes=excludes)
        results = []
        scored_answers = _get_scored_answers(
            last_frozen_assessments, self.assessment_unit_id,
            prefix=prefix, includes=includes)
        with connection.cursor() as cursor:
            cursor.execute(scored_answers, params=None)
            col_headers = cursor.description
            consumption_tuple = namedtuple(
                'ConsumptionTuple', [col[0] for col in col_headers])
            for scored_answer in cursor.fetchall():
                scored_answer = consumption_tuple(*scored_answer)
                opportunity = scored_answer.opportunity
                nb_respondents = scored_answer.nb_respondents
                avg_value = scored_answer.avg_value
                if nb_respondents > 0:
                    added = 3 * avg_value / float(nb_respondents)
                else:
                    added = 0
                measured = scored_answer.implemented
                # If the answer is Yes or N/A, then there is no opportunity
                if (measured in [
                    ASSESSMENT_ANSWERS[YES],
                    ASSESSMENT_ANSWERS[
                        NOT_APPLICABLE]]):
                    opportunity_numerator = 0
                elif (measured ==
                      ASSESSMENT_ANSWERS[
                          NEEDS_SIGNIFICANT_IMPROVEMENT]):
                    opportunity_numerator = opportunity
                elif (measured ==
                      ASSESSMENT_ANSWERS[
                          NEEDS_MODERATE_IMPROVEMENT]):
                    opportunity_numerator = 2 * opportunity + added
                else:
                    # No and not yet answered.
                    opportunity_numerator = 3 * opportunity + added
                results += [{
                    'question_id': scored_answer.id,  # question_id
                    'question__path': scored_answer.path,
                    'rate': scored_answer.rate,
                    'opportunity': opportunity_numerator
                }]
        return results


    def get_scored_answers(self, campaign,
                           includes=None, excludes=None, prefix=None):
        #pylint:disable=too-many-arguments
        with connection.cursor() as cursor:
            scored_answers = _get_scored_answers(
                get_completed_assessments_at_by(campaign, excludes=excludes),
                self.assessment_unit_id, includes=includes, prefix=prefix)
            cursor.execute(scored_answers, params=None)
            col_headers = cursor.description
            decorated_answer_tuple = namedtuple(
                'DecoratedAnswerTuple', [col[0] for col in col_headers])
            results = [
                decorated_answer_tuple(*row) for row in cursor.fetchall()]
        return results


    def get_scorecards(self, campaign, prefix, title=None, includes=None):
        """
        Returns an aggregate of answers' scores and relevant metrics
        to be cached.
        """
        #pylint:disable=too-many-locals,too-many-nested-blocks
        scorecard_caches = []
        if includes and includes[0].is_frozen:
            sql = _get_scorecardcache_sql(
                prefix, self.points_unit_id, self.assessment_unit_id,
                title=title, includes=includes)
            with connection.cursor() as cursor:
                cursor.execute(sql, params=None)
                col_headers = cursor.description
                scorecard_cache_tuple = namedtuple(
                    'ScorecardCacheTuple', [col[0] for col in col_headers])
                scorecard_caches = [
                    scorecard_cache_tuple(*row) for row in cursor.fetchall()]
        else:
            parts = prefix.split('/')
            slug = parts[-1]
            slug_prefix = '/'.join(parts[:-1])
            scores_tree = get_scores_tree(
                roots=[PageElement.objects.get(slug=slug)],
                prefix=slug_prefix)
            if scores_tree:
                rollup_tree = scores_tree.get(prefix)
                leafs = get_leafs(rollup_tree, campaign)
                for scored_answer in self.get_scored_answers(
                        campaign, includes=includes, prefix=prefix):
                    if scored_answer.is_planned:
                        continue
                    account_id = scored_answer.account_id
                    for leaf_prefix, leaf_values in six.iteritems(leafs):
                        if scored_answer.path.startswith(leaf_prefix):
                            accounts = leaf_values[0].get('accounts', {})
                            scores = accounts.get(account_id, {})
                            numerator = (scores.get('numerator', 0) +
                                scored_answer.numerator)
                            denominator = (scores.get('denominator', 0) +
                                scored_answer.denominator)
                            nb_answers = (scores.get('nb_answers', 0) +
                                1)
                            nb_questions = (scores.get('nb_questions', 0) +
                                1)
                            scores.update({
                                'numerator': numerator,
                                'denominator': denominator,
                                'nb_answers': nb_answers,
                                'nb_questions': nb_questions
                            })
                            if account_id not in accounts:
                                accounts.update({account_id: scores})
                            if 'accounts' not in leaf_values[0]:
                                leaf_values[0].update({'accounts': accounts})
                            break

                populate_rollup(rollup_tree, True, force_score=True)
                for node in flatten_content_tree(scores_tree):
                    path = node.get('path')
                    scores = node.get('accounts', {}).get(
                        includes[0].account_id, {})
                    normalized_score = scores.get('normalized_score')
                    scorecard_caches += [ScorecardCache(
                        path=path,
                        sample=includes[0],
                        normalized_score=normalized_score)]
            else:
                scorecard_caches += [ScorecardCache(
                        path=prefix, sample=includes[0])]

        for sample in includes:
            highlights = get_highlights(sample)
            for scorecard in scorecard_caches:
                if scorecard.sample_id == sample.id:
                    for highlight in highlights:
                        reporting_field = highlight.get('slug')
                        if reporting_field:
                            pass
                            #XXX setattr(scorecard, reporting_field,
                            #    highlight.get('reporting'))

        return scorecard_caches


def _get_scored_answers(population, unit_id,
                       includes=None, questions=None, prefix=None):
    """
    Returns a list of tuples with the following fields:

        - id
        - account_id
        - sample_id
        - is_completed
        - is_planned
        - numerator
        - denominator
        - last_activity_at
        - answer_id
        - rank
        - path
        - implemented
        - environmental_value
        - business_value
        - profitability
        - implementation_ease
        - avg_value
        - nb_respondents
        - rate
        - metric
        - opportunity

    the list corresponds to all answers (or a subset when *questions*
    or *prefix* is not `None`) to a *unit_id* for all accounts
    (or a subset when *includes* is not `None`).

    *population* is a set of accounts used to compute the expected
    oportunities.
    """
    #pylint:disable=protected-access
    scored_answers = """SELECT
    expected_choices.id AS id,
    expected_choices.account_id AS account_id,
    expected_choices.sample_id AS sample_id,
    expected_choices.is_completed AS is_completed,
    expected_choices.is_planned AS is_planned,
    expected_choices.numerator AS numerator,
    expected_choices.denominator AS denominator,
    expected_choices.last_activity_at AS last_activity_at,
    expected_choices.answer_id AS answer_id,
    expected_choices.rank AS rank,
    expected_choices.path AS path,
    survey_choice.text AS implemented,
    expected_choices.environmental_value AS environmental_value,
    expected_choices.business_value AS business_value,
    expected_choices.profitability AS profitability,
    expected_choices.implementation_ease AS implementation_ease,
    expected_choices.avg_value AS avg_value,
    expected_choices.nb_respondents AS nb_respondents,
    expected_choices.rate AS rate,
    survey_unit.slug AS unit,
    expected_choices.opportunity AS opportunity,
    expected_choices.ui_hint AS ui_hint
FROM (SELECT
        expected_opportunities.account_id AS account_id,
        expected_opportunities.sample_id AS sample_id,
        expected_opportunities.is_completed AS is_completed,
        expected_opportunities.is_planned AS is_planned,
        CASE WHEN measured = %(yes)s THEN (opportunity * 3)
            WHEN measured = %(moderate_improvement)s THEN (opportunity * 2)
            WHEN measured = %(significant_improvement)s THEN opportunity
            ELSE 0.0 END AS numerator,
        CASE WHEN measured IN (%(yes_no)s) THEN (opportunity * 3)
            ELSE 0.0 END AS denominator,
        answers.created_at AS last_activity_at,
        answers.id AS answer_id,
        answers.rank as rank,
        expected_opportunities.id AS id,
        expected_opportunities.path AS path,
        answers.measured AS measured,
        answers.unit_id AS unit_id,
        expected_opportunities.environmental_value AS environmental_value,
        expected_opportunities.business_value AS business_value,
        expected_opportunities.profitability AS profitability,
        expected_opportunities.implementation_ease AS implementation_ease,
        expected_opportunities.avg_value AS avg_value,
        expected_opportunities.nb_respondents AS nb_respondents,
        expected_opportunities.rate AS rate,
        expected_opportunities.default_unit_id AS default_unit_id,
        expected_opportunities.opportunity AS opportunity,
        expected_opportunities.ui_hint AS ui_hint
      FROM (%(expected_opportunities)s) AS expected_opportunities
      LEFT OUTER JOIN (%(answers)s) AS answers
      ON expected_opportunities.id = answers.question_id
          AND expected_opportunities.sample_id = answers.sample_id
     ) AS expected_choices
LEFT OUTER JOIN survey_choice
  ON (expected_choices.measured = survey_choice.id AND
      expected_choices.unit_id = survey_choice.unit_id)
INNER JOIN survey_unit
  ON expected_choices.default_unit_id = survey_unit.id
""" % {
       'yes': YES,
       'moderate_improvement': NEEDS_MODERATE_IMPROVEMENT,
       'significant_improvement': NEEDS_SIGNIFICANT_IMPROVEMENT,
       'yes_no': _relevent_as_sql(),
       'expected_opportunities': _get_expected_opportunities_sql(
           population, unit_id, includes=includes,
           questions=questions, prefix=prefix),
       'answers': _get_answer_with_account_sql(unit_id, includes=includes)}
    return scored_answers


def _get_expected_opportunities_sql(population, unit_id,
                                    includes=None, questions=None, prefix=None):
    """
    Decorates with environmental_value, business_value, profitability,
    implementation_ease, avg_value, nb_respondents, and rate such that
    these can be used in assessment and improvement pages.
    """
    questions_with_opportunity = _get_opportunities_sql(
        population, unit_id, prefix=prefix)

    # All expected questions for each sample
    # decorated with ``opportunity``.
    #
    # If we are only looking for all expected questions for each sample,
    # then the query can be simplified by using the Question table
    # directly.
    # XXX missing rank, implemented, planned?
    expected_opportunities = """SELECT
    questions_with_opportunity.id AS id,
    samples.sample_id AS sample_id,
    samples.is_completed AS is_completed,
    samples.is_planned AS is_planned,
    samples.account_id AS account_id,
    questions_with_opportunity.opportunity AS opportunity,
    questions_with_opportunity.path AS path,
    questions_with_opportunity.environmental_value AS environmental_value,
    questions_with_opportunity.business_value AS business_value,
    questions_with_opportunity.profitability AS profitability,
    questions_with_opportunity.implementation_ease AS implementation_ease,
    questions_with_opportunity.avg_value AS avg_value,
    questions_with_opportunity.nb_respondents AS nb_respondents,
    questions_with_opportunity.rate AS rate,
    questions_with_opportunity.default_unit_id AS default_unit_id,
    questions_with_opportunity.ui_hint AS ui_hint
FROM (%(questions_with_opportunity)s) AS questions_with_opportunity
INNER JOIN (
    SELECT survey_enumeratedquestions.question_id AS question_id,
           survey_sample.account_id AS account_id,
           survey_sample.id AS sample_id,
           survey_sample.is_frozen AS is_completed,
           survey_sample.extra AS is_planned
    FROM survey_sample
    INNER JOIN survey_enumeratedquestions
      ON survey_sample.campaign_id = survey_enumeratedquestions.campaign_id
    %(additional_filters)s
    ) AS samples
ON questions_with_opportunity.id = samples.question_id
""" % {'questions_with_opportunity': questions_with_opportunity,
       'additional_filters': _additional_filters_sql(
           includes=includes, questions=questions)} # no prefix because
                           # survey_question is not referenced in query.
    return expected_opportunities


def _get_opportunities_sql(population, unit_id, prefix=None):
    if isinstance(population, six.string_types):
        # We assument `population` is a SQL query.
        sample_population = ("SELECT id FROM (%s) AS sample_population" %
            population)
    else:
        sample_population = ', '.join(
            [str(sample.pk) for sample in population])

    # Taken the latest assessment for each account, the implementation rate
    # is defined as the number of positive answers divided by the number of
    # valid answers (i.e. different from "N/A").
    #pylint:disable=protected-access
    implementation_rate_view = """WITH
nb_positive_by_questions AS (
  SELECT
    survey_answer.question_id AS question_id,
    COUNT(survey_answer.id) AS nb_yes
  FROM survey_answer
  WHERE survey_answer.unit_id = %(unit_id)s
    AND survey_answer.measured IN (%(positive_answers)s)
    AND survey_answer.sample_id IN (%(sample_population)s)
  GROUP BY survey_answer.question_id),

nb_valid_by_questions AS (
  SELECT
    survey_question.id AS question_id,
    COUNT(survey_answer.id) AS nb_yes_no,
    survey_question.avg_value AS avg_value
  FROM survey_question
  INNER JOIN survey_answer
    ON survey_question.id = survey_answer.question_id
  WHERE survey_answer.unit_id = %(unit_id)s
    AND survey_answer.measured IN (%(valid_answers)s)
    AND survey_answer.sample_id IN (%(sample_population)s)
    %(filter_questions)s
  GROUP BY survey_question.id)
""" % {
    'sample_population': sample_population,
    'unit_id': unit_id,
    'filter_questions': _additional_filters_sql(
        prefix=prefix, intro_keyword="AND"),
    'positive_answers': _present_as_sql(),
    'valid_answers': _relevent_as_sql(),
}

    # The opportunity for all questions with a "Yes" answer.
    yes_opportunity_view = """%(implementation_rate)s,
opportunity_view AS (
  SELECT
    nb_valid_by_questions.question_id AS question_id,
    (nb_valid_by_questions.avg_value * (1.0 +
      CAST(nb_positive_by_questions.nb_yes AS FLOAT)
        / nb_valid_by_questions.nb_yes_no)) as opportunity,
    (CAST(nb_positive_by_questions.nb_yes AS FLOAT) * 100
        / nb_valid_by_questions.nb_yes_no) as rate,
    nb_valid_by_questions.nb_yes_no as nb_respondents
  FROM nb_valid_by_questions
  LEFT OUTER JOIN nb_positive_by_questions
  ON nb_positive_by_questions.question_id = nb_valid_by_questions.question_id)
""" % {'implementation_rate': implementation_rate_view}

    # All expected questions for each sample decorated with
    # an ``opportunity``.
    # This set of opportunities only has to be computed once.
    # It is shared across all samples.
    # COALESCE now supported on sqlite3.
    questions_with_opportunity = """%(yes_opportunity_view)s
SELECT
  survey_question.id AS id,
  COALESCE(opportunity_view.opportunity, survey_question.avg_value, 0)
    AS opportunity,
  COALESCE(opportunity_view.rate, 0) AS rate,
  COALESCE(opportunity_view.nb_respondents, 0) AS nb_respondents,
  survey_question.environmental_value AS environmental_value,
  survey_question.business_value AS business_value,
  survey_question.implementation_ease AS implementation_ease,
  survey_question.profitability AS profitability,
  survey_question.avg_value AS avg_value,
  survey_question.default_unit_id AS default_unit_id,
  survey_question.path AS path,
  survey_question.ui_hint AS ui_hint
FROM survey_question
LEFT OUTER JOIN opportunity_view
  ON survey_question.id = opportunity_view.question_id
%(filter_questions)s
""" % {
    'yes_opportunity_view': yes_opportunity_view,
    'filter_questions': _additional_filters_sql(prefix=prefix),
}
    return questions_with_opportunity


def _get_answer_with_account_sql(unit_id, includes=None):
    """
    Returns a list of tuples (answer_id, question_id, sample_id, account_id,
    created_at, measured, unit_id, is_completed, is_planned, rank)
    that corresponds to all answers with unit *unit_id* for all
    (or a subset when *includes* is not `None`) accounts.
    """
    query = """SELECT
    survey_answer.id AS id,
    survey_answer.question_id AS question_id,
    survey_answer.sample_id AS sample_id,
    survey_sample.account_id AS account_id,
    survey_answer.created_at AS created_at,
    survey_answer.measured AS measured,
    survey_answer.unit_id AS unit_id,
    survey_sample.is_frozen AS is_completed,
    survey_sample.extra AS is_planned,
    survey_enumeratedquestions.rank AS rank
FROM survey_answer
INNER JOIN survey_sample
  ON survey_answer.sample_id = survey_sample.id
INNER JOIN survey_enumeratedquestions
  ON (survey_answer.question_id = survey_enumeratedquestions.question_id
  AND survey_sample.campaign_id = survey_enumeratedquestions.campaign_id)
WHERE survey_answer.unit_id = %(unit_id)d
  %(additional_filters)s""" % {
      'unit_id': unit_id,
      'additional_filters': _additional_filters_sql(
          includes=includes, intro_keyword="AND")}
    return query


def _get_scorecardcache_sql(prefix, points_unit_id, assessment_unit_id,
                           before=None, title=None, includes=None):
    #pylint:disable=too-many-arguments
    before = datetime_or_now(before)
    return """SELECT
    survey_sample.id AS sample_id,
    survey_sample.slug AS slug,
    survey_sample.created_at AS created_at,
    survey_sample.campaign_id AS campaign_id,
    survey_sample.account_id AS account_id,
    survey_sample.updated_at AS updated_at,
    survey_sample.is_frozen AS is_frozen,
    survey_sample.extra AS extra,
    %(segment_prefix)s AS path,
    %(segment_title)s AS segment_title,
    CAST(SUM(CASE WHEN survey_answer.unit_id = %(points_unit_id)s
        THEN survey_answer.measured ELSE 0 END) AS FLOAT) AS numerator,
    CAST(SUM(CASE WHEN survey_answer.unit_id = %(points_unit_id)s
        THEN survey_answer.denominator ELSE 0 END) AS FLOAT) AS denominator,
    COUNT(CASE WHEN survey_answer.unit_id = %(points_unit_id)s
        THEN 1 ELSE 0 END) AS nb_answers,
    COUNT(CASE WHEN survey_answer.unit_id = %(points_unit_id)s
        THEN 1 ELSE 0 END) AS nb_questions,
    SUM(CASE WHEN (
     survey_answer.unit_id = %(assessment_unit_id)s AND
     survey_answer.measured = %(choice)s) THEN 1 ELSE 0 END) AS nb_na_answers,
    MAX(CASE WHEN (
     survey_question.path LIKE '%%/environmental-reporting/%%-publicly-reported' AND
     survey_answer.unit_id = %(yesno_unit_id)s AND
    survey_answer.measured = %(yes)s) THEN 1 ELSE 0 END) AS reporting_publicly,
    MAX(CASE WHEN (
     survey_question.path LIKE '%%/environmental-fines' AND
     survey_answer.unit_id = %(yesno_unit_id)s AND
     survey_answer.measured = %(yes)s) THEN 1 ELSE 0 END) AS reporting_fines,
-- Answers on data metrics per category (Energy, GHG, Water, Waste)
    SUM(CASE WHEN (
     survey_question.path LIKE '%%/energy-measured/%%' AND
     survey_answer.measured IS NOT NULL)
     THEN 1 ELSE 0 END) AS reporting_energy_consumption,
    SUM(CASE WHEN (
     survey_question.path LIKE '%%/ghg-emissions-measured/%%'  AND
     survey_answer.measured IS NOT NULL)
     THEN 1 ELSE 0 END) AS reporting_ghg_generated,
    SUM(CASE WHEN (
     survey_question.path LIKE '%%/water-measured/%%' AND
     survey_answer.measured IS NOT NULL)
     THEN 1 ELSE 0 END) AS reporting_water_consumption,
    SUM(CASE WHEN (
     survey_question.path LIKE '%%/waste-measured/%%' AND
     survey_answer.measured IS NOT NULL)
     THEN 1 ELSE 0 END) AS reporting_waste_generated,
    SUM(CASE WHEN (
     survey_question.path LIKE '%%/energy-target/%%-target-by' AND
     survey_answer.measured IS NOT NULL)
     THEN 1 ELSE 0 END) AS reporting_energy_target,
    SUM(CASE WHEN (
     survey_question.path LIKE '%%/ghg-emissions-target/%%-target-by' AND
     survey_answer.measured IS NOT NULL)
     THEN 1 ELSE 0 END) AS reporting_ghg_target,
    SUM(CASE WHEN (
     survey_question.path LIKE '%%/water-target/%%-target-by' AND
     survey_answer.measured IS NOT NULL)
     THEN 1 ELSE 0 END) AS reporting_water_target,
    SUM(CASE WHEN (
     survey_question.path LIKE '%%/waste-target/%%-target-by' AND
     survey_answer.measured IS NOT NULL)
     THEN 1 ELSE 0 END) AS reporting_waste_target
FROM survey_sample
INNER JOIN (
    SELECT
        survey_sample.account_id,
        MAX(survey_sample.created_at) as last_updated_at
    FROM survey_sample
    INNER JOIN survey_answer
    ON survey_answer.sample_id = survey_sample.id
    INNER JOIN survey_question
    ON survey_answer.question_id = survey_question.id
    WHERE survey_question.path LIKE '%(prefix)s%%' AND
          survey_sample.created_at <= '%(ends_at)s' AND
          survey_sample.extra IS NULL AND
          survey_sample.is_frozen
    GROUP BY survey_sample.account_id) AS last_frozen_assessments
ON survey_sample.account_id = last_frozen_assessments.account_id AND
   survey_sample.created_at = last_frozen_assessments.last_updated_at
INNER JOIN survey_answer
ON survey_answer.sample_id = survey_sample.id
INNER JOIN survey_question
ON survey_answer.question_id = survey_question.id
WHERE survey_sample.extra IS NULL
      AND survey_sample.is_frozen
      AND survey_question.path LIKE '%(prefix)s%%'
      %(samples_clause)s
GROUP BY survey_sample.id
""" % {
        'ends_at': before,
        'prefix': prefix,
        'segment_prefix': ("'%s'" if is_sqlite3() else "'%s'::text") % prefix,
        'segment_title': ("'%s'" if is_sqlite3() else "'%s'::text") % title,
        'points_unit_id': points_unit_id,
        'assessment_unit_id': assessment_unit_id,
        'yesno_unit_id': "(SELECT id FROM survey_unit"\
            " WHERE slug='yes-no')",
        'yes': "(SELECT id FROM survey_choice"\
            " WHERE unit_id=(SELECT id FROM survey_unit WHERE slug='yes-no')"\
            " AND text = 'Yes')",
        'choice': NOT_APPLICABLE,
        'samples_clause': _additional_filters_sql(
            includes=includes, intro_keyword="AND")}


def _additional_filters_sql(includes=None, questions=None, prefix=None,
                            intro_keyword=None):
    sep = ""
    additional_filters = ""
    if includes:
        if isinstance(includes, six.string_types):
            additional_filters += "%ssurvey_sample.id IN (%s)" % (sep, includes)
        elif isinstance(includes, (list, tuple)):
            if isinstance(includes[0], six.integer_types):
                additional_filters += "%ssurvey_sample.id IN (%s)" % (
                    sep, ",".join([str(spk) for spk in includes]))
            else:
                additional_filters += "%ssurvey_sample.id IN (%s)" % (
                    sep, ",".join(
                        [str(sample.pk) for sample in includes if sample.pk]))
        sep = "AND "
    if questions:
        additional_filters += \
            "%ssurvey_enumeratedquestions.question_id IN (%s)" % (
            sep, ', '.join([str(question) for question in questions]))
        sep = "AND "
    if prefix:
        additional_filters += "%ssurvey_question.path LIKE '%s%%'" % (
            sep, prefix)
        sep = "AND "
    if additional_filters:
        if not intro_keyword:
            intro_keyword = "WHERE"
        additional_filters = "%s %s" % (intro_keyword, additional_filters)
    return additional_filters


def _present_as_sql():
    return ','.join(["%s" % val for val in PRESENT])


def _relevent_as_sql():
    return ','.join(["%s" % val for val in PRESENT + ABSENT])
