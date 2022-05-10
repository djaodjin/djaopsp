# Copyright (c) 2021, DjaoDjin inc.
# see LICENSE.

from django.db import models
from django.utils.translation import ugettext_lazy as _
from survey.models import Sample, get_extra_field_class

from .compat import python_2_unicode_compatible


@python_2_unicode_compatible
class Account(models.Model):

    slug = models.SlugField(unique=True, db_index=True)
    full_name = models.CharField(max_length=60, blank=True)
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
        db_table = 'envconnect_scorecardcache'
