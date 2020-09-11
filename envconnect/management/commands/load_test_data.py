# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

"""Command to populate database with test data"""
import random

from dateutil.relativedelta import relativedelta
from deployutils.helpers import datetime_or_now
from django.apps import apps as django_apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.template.defaultfilters import slugify
from faker import Faker
from pages.models import PageElement
from rest_framework.exceptions import ValidationError
from saas.models import Organization
from survey.models import Answer, Sample, Campaign

from ...helpers import get_testing_accounts
from ...mixins import ReportMixin
from ...models import Consumption
from ...scores import freeze_scores

class Command(BaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--account', action='store',
            dest='account', default=None,
            help="Run `populate_historical_scores` on a specific account")
        parser.add_argument('nb_organizations', metavar='nb_organizations',
            default=1000, help="Number of organizations to create.")

    def handle(self, *args, **options):
        self.campaign = Campaign.objects.get(title=ReportMixin.report_title)
#        self.create_organizations(
#            nb_organizations=int(options['nb_organizations']))
        account = options['account']
        if account:
            self.populate_historical_scores(organization=options['account'])

    def create_organizations(self, nb_organizations):
        fake = Faker()
        organization_class = django_apps.get_model(settings.ACCOUNT_MODEL)
        industries = list(PageElement.objects.get_roots().filter(
            tag__contains='industry'))
        # industries = [PageElement(slug='boxes-and-enclosures')]

        with transaction.atomic():
            # Populate all scorecards for organization 'supplier-1'
            # We will use this organization to measure performance of loading
            # scorecards.
            organization = organization_class.objects.get(slug='supplier-1')
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
        sample, _ = Sample.objects.get_or_create(
            campaign=self.campaign, account=organization)
        for question in Consumption.objects.filter(
                path__startswith="/%s/" % industry.slug):
            Answer.objects.create(
                sample=sample, question=question,
                rank=question.rank)

    def populate_historical_scores(self, organization):
        if not isinstance(organization, Organization):
            organization = Organization.objects.get(slug=organization)
        assessment_sample = Sample.objects.filter(
            extra__isnull=True, campaign=self.campaign,
            account=organization).order_by('-created_at').first()

        # Backup current answers
        backups = {}
        for answer in Answer.objects.filter(
                sample=assessment_sample, metric_id=1):
            backups[answer.pk] = answer.measured

        today = datetime_or_now()
        for months in [6, 12, 24]:
            for answer in Answer.objects.filter(
                    sample=assessment_sample, metric_id=1):
                choices = [1, 2, 3, 4]
                answer.measured = random.choice(choices[(answer.measured - 1):])
                answer.save()
            created_at = today - relativedelta(months=months)
            score_sample = freeze_scores(assessment_sample,
                includes=[assessment_sample.pk],
                excludes=get_testing_accounts(),
                created_at=created_at)
            # XXX Sample.created_at is using `auto_now_add`
            score_sample.created_at = created_at
            score_sample.save()

        # Restore backup
        for answer in Answer.objects.filter(
                sample=assessment_sample, metric_id=1):
            answer.measured = backups[answer.pk]
            answer.save()

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
