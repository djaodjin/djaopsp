# Copyright (c) 2026, DjaoDjin inc.
# see LICENSE.

"""
Command to report assessments completed for a grantee over a period.
"""
import csv, datetime, logging

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from survey.helpers import datetime_or_now
from survey.models import Campaign, PortfolioDoubleOptIn
from survey.utils import get_account_model

from ...humanize import REPORTING_ACCESSIBLE_ANSWERS, REPORTING_STATUSES
from ...queries import get_engagement
from ...utils import send_notification


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):

    account_model = get_account_model()

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--campaign', action='store',
            help='Slug of the campaign')
        parser.add_argument('--grantee', action='append',
            dest='grantees',
            help='Slug of grantee')
        parser.add_argument('--starts_at', action='store',
            help='Start date, in YYYY-MM-DD format')
        parser.add_argument('--ends_at', action='store',
            help='End date, in YYYY-MM-DD format')
        parser.add_argument('--dry-run', action='store_true',
            dest='dry_run', default=False,
            help='Do not send notifications')

    def handle(self, *args, **options):
        #pylint:disable=too-many-locals
        start_time = datetime.datetime.utcnow()

        ends_at = datetime_or_now(options['ends_at'])
        starts_at = datetime_or_now(
            options['starts_at'] if options['starts_at']
            else ends_at - relativedelta(days=7))
        dry_run = options['dry_run']

        if options['campaign']:
            campaigns = [Campaign.objects.get(slug=options['campaign'])]
        else:
            campaigns = Campaign.objects.all()

        requested_grantees = None
        if options['grantees']:
            requested_grantees = list(self.account_model.objects.filter(
                slug__in=options['grantees']))

        reporting_status_labels = dict(REPORTING_STATUSES)

        writer = csv.writer(self.stdout)
        writer.writerow(['grantee_slug', 'account_slug', 'printable_name',
            'campaign', 'last_activity_at', 'reporting_status'])

        for campaign in campaigns:
            grantees = requested_grantees
            if grantees is None:
                grantees = self.account_model.objects.filter(
                    portfolio_double_optin_grantees__campaign=campaign
                ).distinct()

            for grantee in grantees:
                requested_accounts = list(PortfolioDoubleOptIn.objects.filter(
                    grantee=grantee, campaign=campaign).values_list(
                    'account_id', flat=True).distinct())
                if not requested_accounts:
                    continue
                queryset = get_engagement(
                    campaign, accounts=requested_accounts,
                    grantees=[grantee],
                    filter_by=REPORTING_ACCESSIBLE_ANSWERS,
                    activity_starts_at=starts_at,
                    activity_ends_at=ends_at)
                completed_by = []
                for val in queryset:
                    status_label = reporting_status_labels.get(
                        val.reporting_status)
                    last_activity_at = (datetime_or_now(val.last_activity_at)
                        if val.last_activity_at else None)
                    completed_by += [{
                        'slug': val.slug,
                        'printable_name': val.printable_name,
                        'last_activity_at': (
                            last_activity_at.strftime("%b %d, %Y")
                            if last_activity_at else ""),
                        'reporting_status': status_label,
                    }]
                    writer.writerow([
                        grantee.slug,
                        val.slug,
                        val.printable_name,
                        campaign.slug,
                        val.last_activity_at,
                        status_label])
                if not completed_by:
                    continue
                context = {
                    'grantee': {
                        'slug': grantee.slug,
                        'email': grantee.email,
                        'printable_name': grantee.printable_name,
                    },
                    'campaign': campaign,
                    'starts_at': starts_at.strftime("%b %d, %Y"),
                    'ends_at': ends_at.strftime("%b %d, %Y"),
                    'completed_by': completed_by,
                    'total_accounts': len(requested_accounts),
                }
                if not dry_run:
                    send_notification(
                        'completed_assessments_report', context=context)

        end_time = datetime.datetime.utcnow()
        delta = relativedelta(end_time, start_time)
        LOGGER.info("completed in %d hours, %d minutes, %d.%d seconds",
            delta.hours, delta.minutes, delta.seconds, delta.microseconds)
        self.stderr.write("completed in %d hours, %d minutes, %d.%d seconds\n"
            % (delta.hours, delta.minutes, delta.seconds, delta.microseconds))
