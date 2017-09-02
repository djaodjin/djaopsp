# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

"""Command to populate database with test data"""
import random

from django.apps import apps as django_apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.template.defaultfilters import slugify
from faker import Faker
from pages.models import PageElement
from rest_framework.exceptions import ValidationError
from survey.models import Answer, Response, SurveyModel

from ...mixins import ReportMixin
from ...models import Consumption


class Command(BaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('nb_organizations', metavar='nb_organizations',
            default=1000, help="Number of organizations to create.")

    def handle(self, *args, **options):
        nb_organizations = int(options['nb_organizations'])
        fake = Faker()
        self.survey = SurveyModel.objects.get(title=ReportMixin.report_title)
        organization_class = django_apps.get_model(settings.ACCOUNT_MODEL)
        industries = list(PageElement.objects.get_roots().filter(
            tag__contains='industry'))
        # industries = [PageElement(slug='boxes-and-enclosures')]

        with transaction.atomic():
            # Populate all scorecards for organization 'steve-shop'
            # We will use this organization to measure performance of loading
            # scorecards.
            organization = organization_class.objects.get(slug='steve-shop')
            for industry in industries:
                self.populate_answers(organization, industry)

            # Create random organizations and their scorecard
            for idx in range(1, nb_organizations + 1):
                if idx % 100 == 0:
                    self.stderr.write("generated %d organizations ..." % idx)
                industry = random.choice(industries)
                organization = self.create_unique_organization(
                    organization_class, fake, industries)
                self.populate_answers(organization, industry)
            self.stderr.write(
                "generated %d organizations ..." % nb_organizations)

    def populate_answers(self, organization, industry):
        sample, _ = Response.objects.get_or_create(
            account=organization, survey=self.survey)
        for consumption in Consumption.objects.filter(
                path__startswith="/%s/" % industry.slug):
            Answer.objects.create(
                response=sample, question=consumption.question,
                rank=consumption.question.rank)

    @staticmethod
    def create_unique_organization(organization_class, fake, industries):
        #pylint:disable=protected-access
        max_length = organization_class._meta.get_field('slug').max_length
        industry = random.choice(industries)
        full_name = fake.company()
        extra = '{"industry":"%s"}' % industry.slug
        slug_base = slugify(full_name)
        if not slug_base:
            # title might be empty
            "".join([random.choice("abcdef0123456789") for _ in range(7)])
        elif len(slug_base) > max_length:
            slug_base = slug_base[:max_length]
        slug = slug_base
        for _ in range(1, 10):
            try:
                with transaction.atomic():
                    return organization_class.objects.create(
                        slug=slug,
                        full_name=full_name,
                        extra=extra)
            except IntegrityError as err:
                if 'uniq' not in str(err).lower():
                    raise
                suffix = '-%s' % "".join([random.choice("abcdef0123456789")
                    for _ in range(7)])
                if len(slug_base) + len(suffix) > max_length:
                    slug = slug_base[:(max_length - len(suffix))] + suffix
                else:
                    slug = slug_base + suffix
        raise ValidationError({'detail':
            "Unable to create a unique URL slug from '%s'" % full_name})
