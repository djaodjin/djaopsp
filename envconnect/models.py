# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

"""
Models for envconnect.
"""
from __future__ import unicode_literals

import json, logging

from django.db import models, connection
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from survey.models import Sample, AbstractQuestion as SurveyQuestion

# We cannot import signals into __init__.py otherwise it creates an import
# loop error "make initdb".
from . import signals #pylint: disable=unused-import


LOGGER = logging.getLogger(__name__)

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


class ColumnHeaderQuerySet(models.QuerySet):

    def leading_prefix(self, path):
        candidates = []
        parts = path.split('/')
        if parts:
            if not parts[0]:
                parts = parts[1:]
            #pylint:disable=redefined-variable-type
            candidates = Q(path="/%s" % '/'.join(parts[:1]))
            for idx in range(2, len(parts)):
                candidates |= Q(path="/%s" % '/'.join(parts[:idx]))
            return self.filter(candidates).values('slug').annotate(
                models.Max('path'))
        return self.none()


@python_2_unicode_compatible
class ColumnHeader(models.Model):
    """
    Title of columns for fields defined in the ``Consumption`` table
    as well as meta attributes such as hidden, etc.
    """
    objects = ColumnHeaderQuerySet.as_manager()

    path = models.CharField(max_length=255)
    slug = models.SlugField()
    hidden = models.BooleanField()

    class Meta:
        unique_together = ('path', 'slug')

    def __str__(self):
        return str(self.slug)


class ConsumptionQuerySet(models.QuerySet):
    """
    For a Consumption:
       avg_value = (environmental_value + business_value
           + profitability + implementation_ease) / nb_visible_columns

       implementation_rate = SUM(organization answered kind of yes)
           / SUM(organization answered something else than "N/A")

       opportunity = avg_value * (1 + implementation_rate)

    In the context of an Organization:

           CASE WHEN text = '%(yes)s' THEN (opportunity * 3)
                WHEN text = '%(moderate_improvement)s' THEN (opportunity * 2)
                WHEN text = '%(significant_improvement)s' THEN opportunity
                ELSE 0.0 END AS numerator

           CASE WHEN text IN
             (%(yes_no)s) THEN (opportunity * 3) ELSE 0.0 END AS denominator

        rollup
          SUM(numerator) AS numerator
          SUM(denominator) AS denominator

          agg_scores[key] = agg_scores.get(key, 0) + (
              scores.get(key, 0) * node[0].get('score_weight', 1.0))

    """

    def get_active_by_accounts(self, survey, excludes=None):
        """
        Returns the most recent assessment (i.e. "active"/"not frozen")
        indexed by account. All accounts in ``excludes`` are not added
        to the index.
        """
        #pylint:disable=no-self-use
        if excludes:
            if isinstance(excludes, list):
                excludes = ','.join([
                    str(account_id) for account_id in excludes])
            filter_out_testing = (
                "AND survey_sample.account_id NOT IN (%s)" % str(excludes))
        else:
            filter_out_testing = ""
        sql_query = """SELECT
      survey_sample.account_id AS account_id,
      survey_sample.id AS id,
      survey_sample.created_at AS created_at
  FROM survey_sample
  INNER JOIN (SELECT account_id, MAX(created_at) AS last_updated_at
              FROM survey_sample
              WHERE survey_sample.extra IS NULL %(filter_out_testing)s
                    AND survey_sample.survey_id = %(survey_id)d
              GROUP BY account_id) AS last_updates
  ON survey_sample.account_id = last_updates.account_id AND
     survey_sample.created_at = last_updates.last_updated_at
""" % {'survey_id': survey.pk,
       'filter_out_testing': filter_out_testing}
        return Sample.objects.raw(sql_query)

    def get_latest_samples_by_accounts(self, survey, includes=None):
        """
        assessment and planning
        """
        #pylint:disable=no-self-use
        if includes:
            samples_filter = "WHERE survey_sample.id IN (%s)" % (
                ', '.join([str(sample_pk) for sample_pk in includes]))
        else:
            samples_filter = ""
        sql_query = """SELECT
        survey_sample.account_id AS account_id,
        survey_sample.id AS id,
        survey_sample.created_at AS created_at,
        survey_sample.survey_id AS survey_id,
        survey_sample.is_frozen AS is_frozen,
        survey_sample.extra AS extra
      FROM survey_sample
      INNER JOIN (
        SELECT account_id, extra, MAX(created_at) AS last_updated_at
        FROM survey_sample
        WHERE survey_sample.survey_id = %(survey_id)d
          AND (survey_sample.extra IS NULL
            OR survey_sample.extra = 'is_planned')
        GROUP BY account_id, extra) AS latests
      ON survey_sample.account_id = latests.account_id
        AND survey_sample.created_at = latests.last_updated_at
      %(samples_filter)s""" % {
          'survey_id': survey.pk,
          'samples_filter': samples_filter}
        return Sample.objects.raw(sql_query)

    @staticmethod
    def get_opportunities_sql(population, prefix=None):
        sample_population = ', '.join(
            [str(sample.pk) for sample in population])
        if prefix:
            filter_questions = "survey_question.path LIKE '%s%%'" % prefix
        else:
            filter_questions = None

        # Taken the latest assessment for each account, the implementation rate
        # is defined as the number of positive answers divided by the number of
        # valid answers (i.e. different from "N/A").
        #pylint:disable=protected-access
        implementation_rate_view = """WITH
nb_positive_by_questions AS (
  SELECT
    question_id AS question_id,
    COUNT(survey_answer.id) AS nb_yes
  FROM survey_answer
  WHERE survey_answer.metric_id = 1
    AND survey_answer.measured IN (%(positive_answers)s)
    AND survey_answer.sample_id IN (%(sample_population)s)
  GROUP BY question_id),

nb_valid_by_questions AS (
  SELECT
    survey_question.id AS question_id,
    COUNT(survey_answer.id) AS nb_yes_no,
    survey_question.avg_value AS avg_value
  FROM survey_question
  INNER JOIN survey_answer
    ON survey_question.id = survey_answer.question_id
  WHERE survey_answer.metric_id = 1
    AND survey_answer.measured IN (%(valid_answers)s)
    AND survey_answer.sample_id IN (%(sample_population)s)
    %(filter_questions)s
  GROUP BY survey_question.id)
""" % {
    'sample_population': sample_population,
    'filter_questions': "AND %s" % filter_questions if prefix else "",
    'positive_answers': Consumption._present_as_sql(),
    'valid_answers': Consumption._relevent_as_sql(),
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
        _show_query_and_result(yes_opportunity_view)

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
  survey_question.requires_measurements AS requires_measurements,
  survey_question.path AS path
FROM survey_question
LEFT OUTER JOIN opportunity_view
  ON survey_question.id = opportunity_view.question_id
%(filter_questions)s
""" % {
    'yes_opportunity_view': yes_opportunity_view,
    'filter_questions': "WHERE %s" % filter_questions if prefix else ""}
        _show_query_and_result(questions_with_opportunity)
        return questions_with_opportunity

    def with_opportunity(self, population):
        return self.raw(self.get_opportunities_sql(population))


@python_2_unicode_compatible
# XXX Before migration:
#class Consumption(models.Model):
# XXX After migration:
class Consumption(SurveyQuestion):
    """Consumption of externalities in the manufactoring process."""

    YES = 1                           # 'Yes'
    NEEDS_MODERATE_IMPROVEMENT = 2    # 'Mostly yes'
    NEEDS_SIGNIFICANT_IMPROVEMENT = 3 # 'Mostly no'
    NO = 4                            #pylint:disable=invalid-name
    NOT_APPLICABLE = 5                # 'Not applicable'

    PRESENT = (YES, NEEDS_MODERATE_IMPROVEMENT)
    ABSENT = (NO, NEEDS_SIGNIFICANT_IMPROVEMENT)

    ASSESSMENT_CHOICES = {
        'management': (YES, NEEDS_MODERATE_IMPROVEMENT,
            NEEDS_SIGNIFICANT_IMPROVEMENT, NO,
            NOT_APPLICABLE),
        'default': (YES, NEEDS_MODERATE_IMPROVEMENT,
            NEEDS_SIGNIFICANT_IMPROVEMENT, NO,
            NOT_APPLICABLE)}

    ASSESSMENT_ANSWERS = {
        YES: 'Yes',
        NEEDS_MODERATE_IMPROVEMENT: 'Mostly yes',
        NEEDS_SIGNIFICANT_IMPROVEMENT: 'Mostly no',
        NO: 'No',
        NOT_APPLICABLE: 'Not applicable'
    }

    NO_MEASUREMENTS = 0
    FREETEXT_MEASUREMENTS = 1
    CATEGORIZED_MEASUREMENTS = 2

    MEASUREMENTS = (
        (NO_MEASUREMENTS, 'none'),
        (FREETEXT_MEASUREMENTS, 'freetext'),
        (CATEGORIZED_MEASUREMENTS, 'categorized')
    )


    NOT_MEASUREMENTS_METRICS = (
        'assessment',
        'score',
        'framework'
    )

    # ColumnHeader objects are inserted lazily at the time a column
    # is hidden so we need a default set of columns to compute visible ones
    # in all cases.
    VALUE_SUMMARY_FIELDS = set(['environmental_value', 'business_value',
        'implementation_ease', 'profitability'])

    objects = ConsumptionQuerySet.as_manager()

    # Value summary fields
    environmental_value = models.IntegerField(default=1)
    business_value = models.IntegerField(default=1)
    implementation_ease = models.IntegerField(default=1)
    profitability = models.IntegerField(default=1)

    # Description fields
    avg_energy_saving = models.CharField(max_length=50, default="-")
    avg_fuel_saving = models.CharField(max_length=50, default="-")
    capital_cost_low = models.IntegerField(null=True)
    capital_cost_high = models.IntegerField(null=True)
    capital_cost = models.CharField(max_length=50, default="-")
    payback_period = models.CharField(max_length=50, default="-")

    # computed fields
    nb_respondents = models.IntegerField(default=0)
    opportunity = models.IntegerField(default=0)
    rate = models.IntegerField(default=0)

    #   avg_value = (environmental_value + business_value
    #       + profitability + implementation_ease) / nb_visible_columns
    #
    # As a result it needs to be updated every time:
    #   - a column visibility is toggled between visible / hidden.
    #   - a value summary is updated
    #   - a Consumption is initially created
    avg_value = models.IntegerField(default=0)

    # Additional metric on the Question.
    requires_measurements = models.PositiveSmallIntegerField(
        choices=MEASUREMENTS, default=NO_MEASUREMENTS)

    class Meta:
        db_table = 'survey_question'

    def __str__(self):
        return str(self.pk)

    @staticmethod
    def _present_as_sql():
        return ','.join(["%s" % val for val in Consumption.PRESENT])

    @staticmethod
    def _relevent_as_sql():
        return ','.join(["%s" % val
            for val in Consumption.PRESENT + Consumption.ABSENT])

    def save(self, force_insert=False, force_update=False,
             using=None, update_fields=None):
        #pylint:disable=access-member-before-definition
        if not self.default_metric_id:
            self.default_metric_id = 1 # assessment Yes/etc.
        visible_cols = self.VALUE_SUMMARY_FIELDS - set([
            col['slug'] for col in ColumnHeader.objects.leading_prefix(
                self.path).filter(hidden=True)])
        nb_visible_cols = len(visible_cols)
        if nb_visible_cols > 0:
            col_sum = 0
            for col in visible_cols:
                col_sum += getattr(self, col)
            # Round to nearst:
            self.avg_value = (col_sum + nb_visible_cols // 2) // nb_visible_cols
            if self.avg_value >= 4:
                # We bump average to "Gold".
                self.avg_value = 6
        LOGGER.debug("Save Consumption(path='%s'), %d visible columns %s,"\
            " with avg_value of %d", self.path, nb_visible_cols,
            [(col, getattr(self, col)) for col in visible_cols], self.avg_value)
        return super(Consumption, self).save(
            force_insert=force_insert, force_update=force_update,
            using=using, update_fields=update_fields)


def get_score_weight(tag):
    """
    We aggregate weighted scores when walking up the tree.

    Storing the weight in the `PageElement.tag` field works when we assume
    only best practices (leafs) are aliased and best practices do not have
    weight themselves.
    """
    try:
        extra = json.loads(tag)
        return extra.get('weight', 1.0)
    except (TypeError, ValueError):
        pass
    return 1.0


def _additional_filters(includes=None, questions=None, prefix=None, extra=None):
    sep = ""
    additional_filters = ""
    if includes:
        additional_filters += "%ssurvey_sample.id IN (%s)" % (
            sep, ', '.join([str(sample.pk) for sample in includes]))
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
    if extra:
        additional_filters += "%s%s" % (sep, extra)
        sep = "AND "
    if additional_filters:
        additional_filters = "WHERE %s" % additional_filters
    return additional_filters


def get_expected_opportunities(population, includes=None,
                               questions=None, prefix=None):
    """
    Decorates with environmental_value, business_value, profitability,
    implementation_ease, avg_value, nb_respondents, and rate such that
    these can be used in assessment and improvement pages.
    """
    questions_with_opportunity = Consumption.objects.get_opportunities_sql(
        population, prefix=prefix)

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
    questions_with_opportunity.requires_measurements AS requires_measurements
FROM (%(questions_with_opportunity)s) AS questions_with_opportunity
INNER JOIN (
    SELECT survey_enumeratedquestions.question_id AS question_id,
           survey_sample.account_id AS account_id,
           survey_sample.id AS sample_id,
           survey_sample.is_frozen AS is_completed,
           survey_sample.extra AS is_planned
    FROM survey_sample
    INNER JOIN survey_enumeratedquestions
      ON survey_sample.survey_id = survey_enumeratedquestions.campaign_id
    %(additional_filters)s
    ) AS samples
ON questions_with_opportunity.id = samples.question_id
""" % {'questions_with_opportunity': questions_with_opportunity,
       'additional_filters': _additional_filters(
           includes=includes, questions=questions)}
    _show_query_and_result(expected_opportunities)
    return expected_opportunities


def get_answer_with_account(includes=None, metric_id=1):
    """
    Returns a list of tuples (answer_id, question_id, sample_id, account_id,
    created_at, measured, is_planned) that corresponds to all answers
    for all (or a subset when *includes* is not `None`) accounts.
    """
    query = """SELECT
    survey_answer.id AS id,
    question_id,
    sample_id,
    account_id,
    survey_answer.created_at AS created_at,
    measured,
    survey_sample.is_frozen AS is_completed,
    survey_sample.extra AS is_planned,
    survey_answer.rank AS rank
FROM survey_answer
INNER JOIN survey_sample
  ON survey_answer.sample_id = survey_sample.id
%(additional_filters)s""" % {
    'additional_filters': _additional_filters(
        includes=includes, extra="survey_answer.metric_id = %d" % metric_id)}
    _show_query_and_result(query)
    return query


def get_historical_scores(includes=None, prefix=None):
    """
    Returns a list of tuples with the following fields:

        - account_id
        - sample_id
        - is_completed
        - is_planned
        - numerator
        - denominator
        - last_activity_at
        - answer_id
        - question_id
        - path

    XXX This query will only work if we have denominator for all questions,
    even the unanswered ones?
    """
    scored_answers = """SELECT
survey_sample.account_id AS account_id,
survey_answer.sample_id AS sample_id,
survey_sample.is_frozen AS is_completed,
survey_sample.extra = 'is_planned' AS is_planned,
survey_answer.measured AS numerator,
survey_answer.denominator AS denominator,
survey_sample.created_at AS last_activity_at,
survey_answer.id AS answer_id,
survey_answer.question_id AS question_id,
survey_question.path AS path
FROM survey_answer
INNER JOIN survey_sample
  ON survey_answer.sample_id = survey_sample.id
INNER JOIN survey_question
  ON survey_answer.question_id = survey_question.id
%(additional_filters)s""" % {
    'additional_filters': _additional_filters(
        includes=includes, prefix=prefix, extra="survey_answer.metric_id = 2")}
    _show_query_and_result(scored_answers)
    return scored_answers


def get_scored_answers(population, metric_id,
                       includes=None, questions=None, prefix=None):
    """
    Returns a list of tuples with the following fields:

        - account_id
        - sample_id
        - is_completed
        - is_planned
        - numerator
        - denominator
        - last_activity_at
        - answer_id
        - question_id
        - path
        - implemented
        - environmental_value
        - business_value
        - profitability
        - implementation_ease
        - avg_value
        - nb_respondents
        - rate
        - opportunity

    the list corresponds to all answers for all (or a subset when *includes*
    is not `None`) accounts excluding accounts that were filtered out
    by *excludes*, decorated with a numerator and denominator.

    Set is_planned to `True` for assessment results only or is_planned
    to `False` for improvement results only. Otherwise both.

    If not `None`, *includes* and *excludes* are the set of organization
    samples which are included and excluded respectively.
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
    expected_choices.requires_measurements AS requires_measurements,
    expected_choices.opportunity AS opportunity
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
    expected_opportunities.environmental_value AS environmental_value,
    expected_opportunities.business_value AS business_value,
    expected_opportunities.profitability AS profitability,
    expected_opportunities.implementation_ease AS implementation_ease,
    expected_opportunities.avg_value AS avg_value,
    expected_opportunities.nb_respondents AS nb_respondents,
    expected_opportunities.rate AS rate,
    expected_opportunities.requires_measurements AS requires_measurements,
    expected_opportunities.opportunity AS opportunity
FROM (%(expected_opportunities)s) AS expected_opportunities
LEFT OUTER JOIN (%(answers)s) AS answers
ON expected_opportunities.id = answers.question_id
   AND expected_opportunities.sample_id = answers.sample_id) AS expected_choices
LEFT OUTER JOIN survey_choice
ON expected_choices.measured = survey_choice.id
""" % {
       'yes': Consumption.YES,
       'moderate_improvement': Consumption.NEEDS_MODERATE_IMPROVEMENT,
       'significant_improvement': Consumption.NEEDS_SIGNIFICANT_IMPROVEMENT,
       'yes_no': Consumption._relevent_as_sql(),
       'expected_opportunities': get_expected_opportunities(
           population,
           includes=includes, questions=questions, prefix=prefix),
       'answers': get_answer_with_account(
           includes=includes, metric_id=metric_id)}
    _show_query_and_result(scored_answers)
    return scored_answers


def get_assessment_answers(campaign, population, prefix=None):
    """
    Returns a SQL query to retrive the specific assessment answer (Yes,
    Mostly yes, Mostly no, No) for all accounts in ``population`` indexed
    by questions. Questions are selected to be present in the index
    if their path starts with ``prefix``.
    """
    assessment_answers = """
WITH assessment_answers AS (
  SELECT survey_answer.question_id AS question_id,
         survey_sample.account_id AS account_id,
         survey_answer.sample_id AS sample_id,
         survey_answer.measured AS measured FROM survey_answer
  INNER JOIN survey_sample
  ON survey_answer.sample_id = survey_sample.id
  WHERE
    survey_answer.metric_id = 1
    AND survey_sample.extra IS NULL
    AND survey_sample.survey_id = %(campaign)d
    AND survey_sample.account_id IN (%(population)s)
), ranked_questions AS (
  SELECT survey_question.id AS id,
         survey_question.path AS path,
         survey_enumeratedquestions.rank AS rank
  FROM survey_question
  INNER JOIN survey_enumeratedquestions
  ON survey_question.id = survey_enumeratedquestions.question_id
  WHERE
    survey_question.path LIKE '%(prefix)s%%'
    AND survey_enumeratedquestions.campaign_id = %(campaign)d
)
  SELECT ranked_questions.path AS path,
         assessment_answers.account_id AS account_id,
         assessment_answers.sample_id AS sample_id,
         assessment_answers.measured AS measured
  FROM ranked_questions
  LEFT OUTER JOIN assessment_answers
  ON ranked_questions.id = assessment_answers.question_id
  ORDER BY ranked_questions.rank""" % {
      'campaign': campaign.pk,
      'population': ','.join([str(sample.pk) for sample in population]),
      'prefix': prefix,
  }
    _show_query_and_result(assessment_answers)
    return assessment_answers
