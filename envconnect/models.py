# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

"""
Models for envconnect.
"""
from __future__ import unicode_literals

import json, logging

from django.conf import settings
from django.db import models, connection
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from survey.models import Question as SurveyQuestion

# We cannot import signals into __init__.py otherwise it creates an import
# loop error "make initdb".
from . import signals #pylint: disable=unused-import


LOGGER = logging.getLogger(__name__)

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

    def get_opportunities_sql(self, filter_out_testing=None):
        filter_out_testing = ""
        if filter_out_testing:
            filter_out_testing = "AND survey_answer.sample_id NOT IN (%s)" % (
                ', '.join(filter_out_testing))

        # Taken the latest assessment for each account, the implementation rate
        # is defined as the number of positive answers divided by the number of
        # valid answers (i.e. different from "N/A").
        implementation_rate_view = """WITH
latest_assessment_by_accounts AS (
  SELECT survey_sample.account_id, survey_sample.id, created_at
  FROM survey_sample
  INNER JOIN (SELECT account_id, MAX(created_at) AS last_updated_at
              FROM survey_sample
              WHERE survey_sample.extra IS NULL %(filter_out_testing)s
              GROUP BY account_id) AS last_updates
  ON survey_sample.account_id = last_updates.account_id AND
     survey_sample.created_at = last_updates.last_updated_at),

nb_positive_by_questions AS (
  SELECT
    question_id AS question_id,
    COUNT(survey_answer.id) AS nb_yes
  FROM survey_answer INNER JOIN latest_assessment_by_accounts
    ON survey_answer.sample_id = latest_assessment_by_accounts.id
  WHERE survey_answer.measured IN (%(positive_answers)s)
  GROUP BY question_id),

nb_valid_by_questions AS (
  SELECT
    envconnect_consumption.question_id AS question_id,
    COUNT(survey_answer.id) AS nb_yes_no,
    envconnect_consumption.avg_value AS avg_value
  FROM envconnect_consumption
  INNER JOIN survey_question
    ON envconnect_consumption.question_id = survey_question.id
  INNER JOIN survey_answer
    ON survey_question.id = survey_answer.question_id
  INNER JOIN latest_assessment_by_accounts
  ON survey_answer.sample_id = latest_assessment_by_accounts.id
  WHERE survey_answer.measured IN (%(valid_answers)s)
  GROUP BY envconnect_consumption.question_id)
""" % {
    'filter_out_testing': filter_out_testing,
    'positive_answers': Consumption._present_as_sql(),
    'valid_answers': Consumption._relevent_as_sql(),
}

        # The opportunity for all questions with a "Yes" answer.
        yes_opportunity_view = """%(implementation_rate)s SELECT
  yes_no_view.question_id AS question_id,
  (yes_no_view.avg_value * (1.0 +
      CAST(yes_view.nb_yes AS FLOAT) / yes_no_view.nb_yes_no)) as opportunity,
  (CAST(yes_view.nb_yes AS FLOAT) * 100 / yes_no_view.nb_yes_no) as rate,
  yes_no_view.nb_yes_no as nb_respondents
FROM nb_valid_by_questions as yes_no_view
LEFT OUTER JOIN nb_positive_by_questions as yes_view
ON yes_view.question_id = yes_no_view.question_id""" % {
                'implementation_rate': implementation_rate_view}
        self._show_query_and_result(yes_opportunity_view)

        # All expected questions for each sample decorated with
        # an ``opportunity``.
        # This set of opportunities only has to be computed once.
        # It is shared across all samples.
        # COALESCE now supported on sqlite3.
        questions_with_opportunity = """SELECT
  envconnect_consumption.question_id AS question_id,
  COALESCE(opportunity_view.opportunity, envconnect_consumption.avg_value, 0)
    AS opportunity,
  COALESCE(opportunity_view.rate, 0) AS rate,
  COALESCE(opportunity_view.nb_respondents, 0) AS nb_respondents,
  envconnect_consumption.environmental_value AS environmental_value,
  envconnect_consumption.business_value AS business_value,
  envconnect_consumption.implementation_ease AS implementation_ease,
  envconnect_consumption.profitability AS profitability,
  envconnect_consumption.avg_value AS avg_value,
  survey_question.path AS path
FROM envconnect_consumption INNER JOIN survey_question
ON envconnect_consumption.question_id = survey_question.id
LEFT OUTER JOIN (%(yes_opportunity_view)s) AS opportunity_view
ON envconnect_consumption.question_id = opportunity_view.question_id""" % {
                'yes_opportunity_view': yes_opportunity_view,
            }
        self._show_query_and_result(questions_with_opportunity)
        return questions_with_opportunity

    def with_opportunity(self, filter_out_testing=None):
        return self.raw(self.get_opportunities_sql(
            filter_out_testing=filter_out_testing))


@python_2_unicode_compatible
class Consumption(SurveyQuestion):
    """Consumption of externalities in the manufactoring process."""

    YES = 1                           # 'Yes'
    NEEDS_MODERATE_IMPROVEMENT = 2    # 'Yes, but needs a little improvement'
    NEEDS_SIGNIFICANT_IMPROVEMENT = 3 # 'Yes, but needs a lot of improvement'
    NO = 4                            #pylint:disable=invalid-name
    NO_NEEDS_IMPROVEMENT = 6          # 'No/needs improvement'
    NOT_APPLICABLE = 5                # 'Not applicable'

    PRESENT = (YES, NEEDS_MODERATE_IMPROVEMENT)
    ABSENT = (NO, NEEDS_SIGNIFICANT_IMPROVEMENT, NO_NEEDS_IMPROVEMENT)

    ASSESSMENT_CHOICES = {
        'management': (YES, NEEDS_MODERATE_IMPROVEMENT,
            NEEDS_SIGNIFICANT_IMPROVEMENT, NO,
            NOT_APPLICABLE),
        'default': (YES, NEEDS_MODERATE_IMPROVEMENT,
            NEEDS_SIGNIFICANT_IMPROVEMENT, NO,
            NOT_APPLICABLE)}

    # ColumnHeader objects are inserted lazily at the time a column
    # is hidden so we need a default set of columns to compute visible ones
    # in all cases.
    VALUE_SUMMARY_FIELDS = set(['environmental_value', 'business_value',
        'implementation_ease', 'profitability'])

    objects = ConsumptionQuerySet.as_manager()

    question = models.OneToOneField(SurveyQuestion, parent_link=True)

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
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL,
        db_column='reported_by', null=True)

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
        if not self.unit_id:
            self.unit_id = 1 # assessment unit
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

    def requires_measurements(self):
        return self.question_type == self.INTEGER


@python_2_unicode_compatible
class Improvement(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    account = models.ForeignKey(settings.ACCOUNT_MODEL)
    consumption = models.ForeignKey(Consumption, on_delete=models.CASCADE)

    def __str__(self):
        return "%s/%s" % (self.account, self.consumption)


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


def _additional_filters(is_planned=None, includes=None, excludes=None):
    sep = ""
    additional_filters = ""
    if is_planned is not None:
        additional_filters = "survey_sample.extra = '%s'" % (
            "is_planned" if is_planned else "")
        sep = "AND "
    if includes:
        additional_filters += "%ssurvey_sample.id IN (%s)" % (
            sep, ', '.join(includes))
        sep = "AND "
    if excludes:
        additional_filters += "%ssurvey_sample.id NOT IN (%s)" % (
            sep, ', '.join(excludes))
    if additional_filters:
        additional_filters = "WHERE %s" % additional_filters
    return additional_filters


def get_expected_opportunities(is_planned=None, includes=None, excludes=None):
    """
    Decorates with environmental_value, business_value, profitability,
    implementation_ease, avg_value, nb_respondents, and rate such that
    these can be used in assessment and improvement pages.
    """
    questions_with_opportunity = Consumption.objects.with_opportunity(
        filter_out_testing=excludes).query

    # All expected questions for each sample
    # decorated with ``opportunity``.
    #
    # If we are only looking for all expected questions for each sample,
    # then the query can be simplified by using the survey_question table
    # directly.
    # XXX missing rank, implemented, planned, requires_measurements?
    expected_opportunities = """SELECT
    questions_with_opportunity.question_id AS question_id,
    samples.sample_id AS sample_id,
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
    questions_with_opportunity.rate AS rate
FROM (%(questions_with_opportunity)s) AS questions_with_opportunity
INNER JOIN (
    SELECT survey_enumeratedquestions.question_id AS question_id,
           survey_sample.account_id AS account_id,
           survey_sample.id AS sample_id,
           survey_sample.extra AS is_planned
    FROM survey_sample
    INNER JOIN survey_enumeratedquestions
    ON survey_sample.survey_id = survey_enumeratedquestions.campaign_id
    %(additional_filters)s) AS samples
ON questions_with_opportunity.question_id = samples.question_id
""" % {'questions_with_opportunity': questions_with_opportunity,
       'additional_filters': _additional_filters(
           is_planned=is_planned, includes=includes, excludes=excludes)}
    _show_query_and_result(expected_opportunities)
    return expected_opportunities


def get_answer_with_account(is_planned=None, includes=None, excludes=None):
    """
    Returns a list of tuples (answer_id, question_id, sample_id, account_id,
    created_at, measured, is_planned) that corresponds to all answers
    for all (or a subset when *includes* is not `None`) accounts
    excluding accounts that were filtered out by *excludes*.
    """
    query = """SELECT
    survey_answer.id AS id,
    question_id,
    sample_id,
    account_id,
    survey_answer.created_at AS created_at,
    measured,
    survey_sample.extra AS is_planned
FROM survey_answer INNER JOIN survey_sample
ON survey_answer.sample_id = survey_sample.id
%(additional_filters)s""" % {
    'additional_filters': _additional_filters(
        is_planned=is_planned, includes=includes, excludes=excludes)}
    _show_query_and_result(query)
    return query


def get_scored_answers(is_planned=None, includes=None, excludes=None):
    """
    Returns a list of tuples (account_id, answer_id, sample_id, question_id,
    numerator, denominator, path, created_at, measured, is_planned)
    that corresponds to all answers for all (or a subset when *includes*
    is not `None`) accounts excluding accounts that were filtered out
    by *excludes*, decorated with a numerator and denominator.

    Set is_planned to `True` for assessment results only or is_planned
    to `False` for improvement results only. Otherwise both.

    If not `None`, *includes* and *excludes* are the set of organization
    samples which are included and excluded respectively.
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
    scored_answers = """SELECT
    expected_choices.account_id,
    expected_choices.sample_id,
    expected_choices.is_planned,
    expected_choices.numerator,
    expected_choices.denominator,
    expected_choices.last_activity_at,
    expected_choices.answer_id,
    expected_choices.question_id,
    expected_choices.path,
    survey_choice.text AS implemented,
    expected_choices.environmental_value,
    expected_choices.business_value,
    expected_choices.profitability,
    expected_choices.implementation_ease,
    expected_choices.avg_value,
    expected_choices.nb_respondents,
    expected_choices.rate,
    expected_choices.opportunity
FROM (SELECT
    expected_opportunities.account_id AS account_id,
    expected_opportunities.sample_id AS sample_id,
    expected_opportunities.is_planned AS is_planned,
    CASE WHEN measured = %(yes)s THEN (opportunity * 3)
         WHEN measured = %(moderate_improvement)s THEN (opportunity * 2)
         WHEN measured = %(significant_improvement)s THEN opportunity
         ELSE 0.0 END AS numerator,
    CASE WHEN measured IN (%(yes_no)s) THEN (opportunity * 3)
         ELSE 0.0 END AS denominator,
    answers.created_at AS last_activity_at,
    answers.id AS answer_id,
    expected_opportunities.question_id AS question_id,
    expected_opportunities.path AS path,
    answers.measured AS measured,
    expected_opportunities.environmental_value AS environmental_value,
    expected_opportunities.business_value AS business_value,
    expected_opportunities.profitability AS profitability,
    expected_opportunities.implementation_ease AS implementation_ease,
    expected_opportunities.avg_value AS avg_value,
    expected_opportunities.nb_respondents AS nb_respondents,
    expected_opportunities.rate AS rate,
    expected_opportunities.opportunity AS opportunity
FROM (%(expected_opportunities)s) AS expected_opportunities
LEFT OUTER JOIN (%(answers)s) AS answers
ON expected_opportunities.question_id = answers.question_id
   AND expected_opportunities.sample_id = answers.sample_id) AS expected_choices
LEFT OUTER JOIN survey_choice
ON expected_choices.measured = survey_choice.id
""" % {
       'yes': Consumption.YES,
       'moderate_improvement': Consumption.NEEDS_MODERATE_IMPROVEMENT,
       'significant_improvement': Consumption.NEEDS_SIGNIFICANT_IMPROVEMENT,
       'yes_no': Consumption._relevent_as_sql(),
       'expected_opportunities': get_expected_opportunities(
           is_planned=is_planned,
           includes=includes, excludes=excludes),
       'answers': get_answer_with_account(
           is_planned=is_planned,
           includes=includes, excludes=excludes)}
    _show_query_and_result(scored_answers)
    return scored_answers
