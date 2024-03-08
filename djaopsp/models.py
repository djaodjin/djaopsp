# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

from django.conf import settings as django_settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from survey.models import Sample, get_extra_field_class, Campaign
from pages.models import PageElement

from .compat import python_2_unicode_compatible


@python_2_unicode_compatible
class Account(models.Model):

    slug = models.SlugField(unique=True, db_index=True)
    full_name = models.CharField(max_length=60, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=11)
    extra = get_extra_field_class()(null=True, blank=True,
        help_text=_("Extra meta data (can be stringify JSON)"))

    def __str__(self):
        return str(self.slug)

    @property
    def printable_name(self):
        if self.full_name:
            return self.full_name
        return self.slug


@python_2_unicode_compatible
class ScorecardCache(models.Model):
    """
    Cache a scorecard results to speed up computations of reporting entities
    dashboards.
    """

    path = models.CharField(max_length=1024, db_index=True,
        help_text="Unique identifier that can be used in URL")
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE,
        related_name='scorecard_cache')
    normalized_score = models.IntegerField()
    nb_na_answers = models.IntegerField()
    reporting_publicly = models.BooleanField()
    reporting_fines = models.BooleanField()
    reporting_environmental_fines = models.BooleanField()
    reporting_energy_consumption = models.BooleanField()
    reporting_water_consumption = models.BooleanField()
    reporting_ghg_generated = models.BooleanField()
    reporting_waste_generated = models.BooleanField()

    reporting_energy_target = models.BooleanField()
    reporting_water_target = models.BooleanField()
    reporting_ghg_target = models.BooleanField()
    reporting_waste_target = models.BooleanField()

    nb_planned_improvements = models.IntegerField()

    class Meta:
        unique_together = ('sample', 'path')


@python_2_unicode_compatible
class VerifiedSample(models.Model):
    """
    Overall assessment of auditor for a response to a questionnaire.
    """
    STATUS_NO_REVIEW = 0
    STATUS_UNDER_REVIEW = 1
    STATUS_REVIEW_COMPLETED = 2
    STATUS_DISCREPANCIES = 3
    STATUS_LACK_CONSISTENCY = 4
    STATUS_MEET_EXPECTATIONS = 5
    STATUS_RIGOROUS = 6

    STATUSES = [
            (STATUS_NO_REVIEW, 'no-review'),
            (STATUS_UNDER_REVIEW, 'under-review'),
            (STATUS_REVIEW_COMPLETED, 'review-completed'),
            (STATUS_DISCREPANCIES, 'discrepencies'),
            (STATUS_LACK_CONSISTENCY, 'lack-consistency'),
            (STATUS_MEET_EXPECTATIONS, 'meet-expectations'),
            (STATUS_RIGOROUS, 'rigorous'),
        ]

    sample = models.OneToOneField(Sample, on_delete=models.CASCADE,
        related_name='verified')
    verifier_notes = models.OneToOneField(Sample, on_delete=models.CASCADE,
        related_name='notes')
    verified_status = models.PositiveSmallIntegerField(
        choices=STATUSES, default=STATUS_NO_REVIEW,
        help_text=_("Verification Status"))
    verified_by = models.ForeignKey(django_settings.AUTH_USER_MODEL,
        null=True, on_delete=models.PROTECT)
    extra = get_extra_field_class()(null=True, blank=True,
        help_text=_("Extra meta data (can be stringify JSON)"))

    def __str__(self):
        return str(self.sample.slug)


class SurveyEvent(models.Model):
    element = models.ForeignKey(PageElement, on_delete=models.CASCADE,
                              related_name='surveys')
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE,
                                 related_name='campaigns')
    extra = get_extra_field_class()(null=True, blank=True,
        help_text=_("Extra meta data (can be stringify JSON)"))

    def __str__(self):
        return "%s-campaign" % str(self.element)
