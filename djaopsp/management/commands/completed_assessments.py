# Copyright (c) 2024, DjaoDjin inc.
# All rights reserved.

"""
Command to list supplier assessments completed within a specified period of time
"""
import logging

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.urls import reverse
from survey.models import Sample, Campaign
from survey.queries import datetime_or_now

from ...models import ScorecardCache

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('campaign',
                            action='store',
                            help='Slug of the campaign',
                            default=None)
        parser.add_argument('--starts_at',
                            action='store',
                            help='Start date, in YYYY-MM-DD format')
        parser.add_argument('--ends_at',
                            action='store',
                            help='End date, in YYYY-MM-DD format')

    def handle(self, *args, **options):
        campaign = options['campaign']
        ends_at = datetime_or_now(options['ends_at'])
        starts_at = datetime_or_now(options['starts_at']) if options['starts_at'] \
                else ends_at - relativedelta(weeks=1)
        if campaign:
            campaign = Campaign.objects.get(slug=str(campaign))

        # We're returning completed/frozen samples belonging to a campaign
        completed_surveys_raw = Sample.objects.get_latest_frozen_by_accounts(
            campaign=campaign, start_at=starts_at, ends_at=ends_at
        )
        completed_surveys = Sample.objects.filter(
            pk__in=[sample.pk for sample in completed_surveys_raw])

        self.stdout.write(f"Completed assessments for {campaign.title}:")
        self.stdout.write(
            f"There were a total of {len(completed_surveys)} surveys completed "
            f"between {starts_at.strftime('%Y-%m-%d')} and {ends_at.strftime('%Y-%m-%d')}")

        for i, survey in enumerate(completed_surveys):
            score_url = reverse('scorecard', args=(survey.account.slug, survey.slug))
            normalized_score = "N/A"
            scorecard_cache = ScorecardCache.objects.filter(sample=survey)
            if scorecard_cache.exists():
                        normalized_score = scorecard_cache.first().normalized_score
            self.stdout.write(
                f"{i+1}. Supplier: {survey.account.slug}, \n"
                f"Completed At: {survey.created_at}, \n"
                f"score_url: {score_url}, \n"
                f"Normalized Score: {normalized_score}, \n")
