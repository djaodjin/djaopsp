# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

"""
Creates a cross-product that results in 2880 units
and 34560 (2880 * 12) metrics.
"""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import six
from survey.models import Metric, Unit

LOGGER = logging.getLogger(__name__)

MEASURE_SUBJECTS = {
    'energy': "Energy",
    'fuel': "Fuel",
    'ghg-emissions': "GHG emissions",
    'hazardous-waste': "Hazardous waste",
    'material': "Material",
    'nox-emissions': "NOx emissions",
    'particulate-emissions': "Particulate emissions",
    'sox-emissions': "SOx emissions",
    'solid-general-waste': "Solid/general waste",
    'spend': "Spend",
    'water-use': "Water use",
    'waste-water-effluent': "Waste water effluent",
}

MEASURE_STICKS = {
    'count': "Count or number",
    'currency': "Currency",
    'gallons': "Gallons",
    'joules': "Joules",
    'kilograms': "Kilograms",
    'liters': "Liters",
    'tons': "Metric tons",
    'percentage': "Percentage",
    'pounds': "Pounds",
    'short-tons': "Tons (short/US)",
    'long-tons': "Tons (long/UK)",
}

MEASURE_MEANINGS = {
    'saved': "Saved",
    'avoided': "Avoided",
    'reduced': "Reduced",
    'generated': "Generated",
    'emitted': "Emitted",
    'with-environmental-controls': "With environmental controls",
}

MEASURE_SCOPES = {
    'corporate-level-of-which-reporting-entity-is-part':
        "Corporate level, of which reporting entity is part",
    'business-unit-Reporting-entity': "Business unit/Reporting entity",
    'some-activities': "Some activities",
    'all-activities': "All activities",
    'ad-hoc-projects': "Ad hoc projects",
    'some-projects': "Some projects",
    'all-projects': "All projects",
    'office-footprint-only': "Office footprint only",
    'full-operations-footprint': "Full operations footprint",
    'partial-operations-footprint': "Partial operations footprint",
    'scope-1-full': "Scope 1 - full",
    'scope-2-full': "Scope 2 - full",
    'scope-3-full': "Scope 3 - full",
    'scope-1-partial': "Scope 1 - partial",
    'scope-2-partial': "Scope 2 - partial",
    'scope-3-partial': "Scope 3 - partial",
}

MEASURE_FREQEUNCIES = {
    'annual': "Annual",
    'quarterly': "Quarterly",
    'semi-annual': "Semi-annual",
}


class Command(BaseCommand):
    #pylint:disable=too-many-instance-attributes

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)

    def handle(self, *args, **options):
        with transaction.atomic():
            self.insert_metrics(MEASURE_SUBJECTS,
                MEASURE_STICKS, MEASURE_MEANINGS,
                MEASURE_SCOPES, MEASURE_FREQEUNCIES)

    def insert_metrics(self, subjects, sticks, meanings, scopes, frequencies):
        #pylint:disable=too-many-arguments,too-many-locals
        self.stdout.write("inserting %d (%d * %d * %d * %d * %d) metrics" % (
            len(subjects) * len(sticks) * len(meanings) * len(scopes)
            * len(frequencies),
            len(subjects), len(sticks), len(meanings), len(scopes),
            len(frequencies)))
        for subject_slug, subject_title in six.iteritems(subjects):
            for stick_slug, stick_title in six.iteritems(sticks):
                for meaning_slug, meaning_title in six.iteritems(meanings):
                    for scope_slug, scope_title in six.iteritems(scopes):
                        for frequency_slug, frequency_title in six.iteritems(
                                frequencies):
                            self.insert_metric(
                                subject_slug, subject_title,
                                stick_slug, stick_title,
                                meaning_slug, meaning_title,
                                scope_slug, scope_title,
                                frequency_slug, frequency_title)

    def insert_metric(self, subject_slug, subject_title,
                      stick_slug, stick_title,
                      meaning_slug, meaning_title,
                      scope_slug, scope_title,
                      frequency_slug, frequency_title):
        #pylint:disable=too-many-arguments,too-many-locals
        unit_slug = '-'.join([stick_slug, frequency_slug, scope_slug])
        unit_title = "%s / %s / %s" % (stick_title, frequency_title,
            scope_title)
        metric_slug = '-'.join([subject_slug, meaning_slug, unit_slug])
        metric_title = "%s %s (%s)" % (subject_title, meaning_title, unit_title)
        if stick_slug in ('count', 'currency', 'percentage'):
            unit_system = Unit.SYSTEM_RANK
        elif stick_slug in ('gallons', 'pounds', 'short-tons', 'long-tons'):
            unit_system = Unit.SYSTEM_IMPERIAL
        elif stick_slug in ('joules', 'kilograms', 'liters', 'tons'):
            unit_system = Unit.SYSTEM_STANDARD
        else:
            unit_system = Unit.SYSTEM_ENUMERATED
        unit, created = Unit.objects.get_or_create(
            slug=unit_slug, defaults={
                'title': unit_title, 'system': unit_system})
        if created:
            self.stdout.write("%s ... inserted" % unit_title)
        _, created = Metric.objects.get_or_create(
            slug=metric_slug, defaults={
                'title': metric_title, 'unit': unit})
        if created:
            self.stdout.write("%s ... inserted" % metric_title)
