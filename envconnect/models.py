# Copyright (c) 2017, DjaoDjin inc.
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
from survey.models import Answer, Question as SurveyQuestion

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


class ScoreWeightManager(models.Manager):

    def from_path(self, path):
        score_weight_obj = self.filter(path=path).first()
        if score_weight_obj is not None:
            score_weight = float(score_weight_obj.weight)
        else:
            score_weight = 1.0
        return score_weight


@python_2_unicode_compatible
class ScoreWeight(models.Model):
    """
    We aggregate weighted scores when walking up the tree.
    """
    objects = ScoreWeightManager()

    path = models.CharField(max_length=255)
    weight = models.DecimalField(decimal_places=2, max_digits=3, default=1)

    def __str__(self):
        return str(self.path)


class ConsumptionQuerySet(models.QuerySet):

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

    def get_opportunities_sql(self):
        # Implementation Note:
        # tried:
        # yes_no_view = str(Consumption.objects.filter(
        #    answer__text__in=Consumption.PRESENT
        #    + Consumption.ABSENT).values('id').annotate(
        #    nb_yes_or_no=Count('answer'),
        #    avg_value=Avg(F('avg_value')).query)
        #
        # but values in ``PRESENT`` and ``ABSENT``
        # do not get quoted.
        yes_view = "SELECT question_id AS question_id, COUNT(survey_answer.id)"\
            " AS nb_yes FROM survey_answer WHERE survey_answer.text IN"\
            " (%(present)s) GROUP BY question_id" % {'present':
                ','.join(["'%s'" % val for val in Consumption.PRESENT])}
        self._show_query_and_result(yes_view)

        yes_no_view = "SELECT envconnect_consumption.question_id"\
            " AS question_id, COUNT(survey_answer.id) AS nb_yes_no,"\
            " AVG(envconnect_consumption.avg_value) AS avg_value"\
            " FROM envconnect_consumption INNER JOIN survey_question"\
            " ON (envconnect_consumption.question_id = survey_question.id)"\
            " INNER JOIN survey_answer"\
            " ON (survey_question.id = survey_answer.question_id)"\
            " WHERE survey_answer.text IN (%(yes_no)s)"\
            "GROUP BY envconnect_consumption.question_id" % {
                'yes_no': ','.join(["'%s'" % val
                    for val in Consumption.PRESENT + Consumption.ABSENT])}
        self._show_query_and_result(yes_no_view)

        # The opportunity for all questions with a "Yes" answer.
        yes_opportunity_view = """SELECT yes_view.question_id AS question_id,
  (yes_no_view.avg_value * (1.0 +
      CAST(yes_view.nb_yes AS FLOAT) / yes_no_view.nb_yes_no)) as opportunity,
  (CAST(yes_view.nb_yes AS FLOAT) * 100 / yes_no_view.nb_yes_no) as rate,
  yes_no_view.nb_yes_no as nb_respondents
FROM (%(yes_view)s) as yes_view INNER JOIN (%(yes_no_view)s) as yes_no_view
ON yes_view.question_id = yes_no_view.question_id""" % {
                'yes_view': yes_view, 'yes_no_view': yes_no_view}
        self._show_query_and_result(yes_opportunity_view)

        # All expected questions for each response decorated with
        # an ``opportunity``.
        # This set of opportunities only has to be computed once.
        # It is shared across all responses.
        # COALESCE now supported on sqlite3.
        questions_with_opportunity = """SELECT
  envconnect_consumption.question_id AS question_id,
  survey_question.survey_id AS survey_id,
  COALESCE(opportunity_view.opportunity, envconnect_consumption.avg_value, 0)
    AS opportunity,
  COALESCE(opportunity_view.rate, 0) AS rate,
  COALESCE(opportunity_view.nb_respondents, 0) AS nb_respondents,
  envconnect_consumption.path AS path
FROM envconnect_consumption INNER JOIN survey_question
ON envconnect_consumption.question_id = survey_question.id
LEFT OUTER JOIN (%(yes_opportunity_view)s) AS opportunity_view
ON envconnect_consumption.question_id = opportunity_view.question_id""" % {
                'yes_opportunity_view': yes_opportunity_view,
            }
        self._show_query_and_result(questions_with_opportunity)
        return questions_with_opportunity

    def with_opportunity(self):
        return self.raw(self.get_opportunities_sql())


@python_2_unicode_compatible
class Consumption(SurveyQuestion):
    """Consumption of externalities in the manufactoring process."""

    YES = 'Yes'
    NEEDS_MODERATE_IMPROVEMENT = 'Yes, but needs a little improvement'
    NEEDS_SIGNIFICANT_IMPROVEMENT = 'Yes, but needs a lot of improvement'
    NO = 'No' #pylint:disable=invalid-name
    NO_NEEDS_IMPROVEMENT = 'No/needs improvement'
    NOT_APPLICABLE = 'Not applicable'
    WORK_IN_PROGRESS = 'Work in progress'

    PRESENT = (YES, NEEDS_MODERATE_IMPROVEMENT, WORK_IN_PROGRESS)
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

    path = models.CharField(max_length=1024)
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

    def save(self, force_insert=False, force_update=False,
             using=None, update_fields=None):
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


class ImprovementManager(models.Manager):

    def get_cart_item(self, account):
        return self.filter(account=account)


@python_2_unicode_compatible
class Improvement(models.Model):

    objects = ImprovementManager()
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
