# Copyright (c) 2023, DjaoDjin inc.
# All rights reserved.

"""
Command for data validation

Checks that for each (grantee, account, campaign) triplets,
`portfolio.ends_at` is greater than the last time the `account`
shared `campaign` responses with the `grantee`.
"""
import datetime, logging

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import DatabaseError
from survey.models import Portfolio, PortfolioDoubleOptIn

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--show-portfolios', action='store_true',
            dest='show_portfolios', default=False,
            help='Show portfolios that do not match optins')
        parser.add_argument('--dry-run', action='store_true',
            dest='dry_run', default=False,
            help='Do not commit database updates')

    def handle(self, *args, **options):
        #pylint:disable=too-many-locals,too-many-statements
        start_time = datetime.datetime.utcnow()
        self.check_portfolios(show=options['show_portfolios'])
        end_time = datetime.datetime.utcnow()
        delta = relativedelta(end_time, start_time)
        LOGGER.info("completed in %d hours, %d minutes, %d.%d seconds",
            delta.hours, delta.minutes, delta.seconds, delta.microseconds)
        self.stdout.write("completed in %d hours, %d minutes, %d.%d seconds\n"
            % (delta.hours, delta.minutes, delta.seconds, delta.microseconds))


    def check_portfolios(self, show=False):
        optins_query = """
WITH optins AS (
SELECT
    grantee_id,
    account_id,
    campaign_id,
    MAX(created_at) AS last_trigger_at
FROM survey_portfoliodoubleoptin
WHERE
    state IN (%(grant_accepted)d, %(request_accepted)d)
GROUP BY grantee_id, account_id, campaign_id
)
SELECT
    optins.grantee_id,
    optins.account_id,
    optins.campaign_id,
    optins.last_trigger_at,
    survey_portfolio.ends_at
FROM optins LEFT OUTER JOIN survey_portfolio ON (
    survey_portfolio.grantee_id = optins.grantee_id AND
    survey_portfolio.account_id = optins.account_id AND
    survey_portfolio.campaign_id = optins.campaign_id)
WHERE
    survey_portfolio.ends_at IS NULL OR
    optins.last_trigger_at >= survey_portfolio.ends_at
    ORDER BY optins.last_trigger_at DESC, optins.grantee_id
""" % {
    'grant_accepted': PortfolioDoubleOptIn.OPTIN_GRANT_ACCEPTED,
    'request_accepted': PortfolioDoubleOptIn.OPTIN_REQUEST_ACCEPTED
}
        count = 0
        first_time = True
        with connection.cursor() as cursor:
            cursor.execute(optins_query, params=None)
            for optin in cursor.fetchall():
                if show:
                    if first_time:
                        self.stdout.write(
                    "grantee_id,account_id,campaign_id,last_trigger_at,ends_at")
                        first_time = False
                    grantee_id = optin[0]
                    account_id = optin[1]
                    campaign_id = optin[2]
                    last_trigger_at = optin[3]
                    ends_at = optin[4]
                    self.stdout.write("%d,%d,%s,%s,%s" % (
                        grantee_id, account_id,
                        str(campaign_id) if campaign_id else "-",
                        last_trigger_at.strftime("%Y-%m-%d"),
                        ends_at.strftime("%Y-%m-%d") if ends_at else "-"))
                count += 1
        self.stdout.write("%d inaccurate portfolios" % count)

