# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.
import random, timezone

from django.conf import settings as django_settings
from django.db import models, transaction, IntegrityError
from django.template.defaultfilters import slugify
from rest_framework.exceptions import ValidationError
from pages.models import PageElement
from survey.models import Sample, get_extra_field_class, Campaign

from .compat import gettext_lazy as _, python_2_unicode_compatible


@python_2_unicode_compatible
class Account(models.Model):

    slug_field = 'slug'
    slugify_field = 'full_name'

    slug = models.SlugField(unique=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now,
        help_text="Date/time of creation (in ISO format)")
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

    def save(self, force_insert=False, force_update=False,
             using=None, update_fields=None):
        if getattr(self, self.slug_field):
            # serializer will set created slug to '' instead of None.
            return super(Account, self).save(
                force_insert=force_insert, force_update=force_update,
                using=using, update_fields=update_fields)
        max_length = self._meta.get_field(self.slug_field).max_length
        slugified_value = getattr(self, self.slugify_field)
        slug_base = slugify(slugified_value)
        if len(slug_base) > max_length:
            slug_base = slug_base[:max_length]
        setattr(self, self.slug_field, slug_base)
        for _ in range(1, 10):
            try:
                with transaction.atomic():
                    return super(Account, self).save(
                        force_insert=force_insert, force_update=force_update,
                        using=using, update_fields=update_fields)
            except IntegrityError as err:
                if 'uniq' not in str(err).lower():
                    raise
                suffix = '-%s' % "".join([random.choice("abcdef0123456789")
                    for _ in range(7)])
                if len(slug_base) + len(suffix) > max_length:
                    setattr(self, self.slug_field,
                        slug_base[:(max_length - len(suffix))] + suffix)
                else:
                    setattr(self, self.slug_field, slug_base + suffix)
        raise ValidationError({'detail':
            "Unable to create a unique URL slug from %s '%s'" % (
                self.slugify_field, slugified_value)})


@python_2_unicode_compatible
class ScorecardCache(models.Model):
    """
    Cache a scorecard results to speed up computations of reporting entities
    dashboards.
    """
    #pylint:disable=too-many-instance-attributes
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
