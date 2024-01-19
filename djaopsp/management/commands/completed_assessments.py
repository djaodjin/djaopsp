# Copyright (c) 2024, DjaoDjin inc.
# All rights reserved.

"""
Command to list supplier assessments completed within a specified period of time
"""
import logging

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.urls import reverse
from survey.models import Campaign
from survey.queries import datetime_or_now

from ...models import ScorecardCache
from ...queries import get_portfolios_frozen_assessments

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--campaign',
                            action='store',
                            help='Slug of the campaign',
                            default=None)
        parser.add_argument('--grantees',
                            nargs='+',
                            help='Slug(s) of grantee(s)')
        parser.add_argument('--starts_at',
                            action='store',
                            help='Start date, in YYYY-MM-DD format')
        parser.add_argument('--ends_at',
                            action='store',
                            help='End date, in YYYY-MM-DD format')

    def handle(self, *args, **options):
        campaign_slug = options['campaign']
        grantees = options.get('grantees', [])
        ends_at = datetime_or_now(options['ends_at'])
        starts_at = datetime_or_now(options['starts_at']) if options['starts_at'] \
                else ends_at - relativedelta(weeks=1)
        
        campaign = None
        if campaign_slug:
            try:
                campaign = Campaign.objects.get(slug=campaign_slug)
            except Campaign.DoesNotExist:
                self.stdout.write(f"No campaign found with slug '{campaign_slug}'.")
                return

        filter_args = {}
        if campaign:
            filter_args['campaign'] = campaign
        if grantees:
            filter_args['grantees'] = grantees

        if not campaign and not grantees:
            raise ValueError("Either 'campaign' or 'grantees' must be provided")

        _, completed_surveys, campaigns = get_portfolios_frozen_assessments(
             **filter_args)

        if campaigns:
            self.stdout.write(f"Completed assessments for the following campaign(s):")
            for campaign_slug in campaigns:
                campaign = Campaign.objects.get(slug=campaign_slug)
                self.stdout.write(f"{campaign.title} \n")
        elif campaign:
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
                f"Campaign: {survey.campaign}, \n"
                f"Completed At: {survey.created_at}, \n"
                f"score_url: {score_url}, \n"
                f"Normalized Score: {normalized_score}, \n")
