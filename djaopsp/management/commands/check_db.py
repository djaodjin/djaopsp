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
from survey.models import PortfolioDoubleOptIn
from survey.utils import get_account_model

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):

    account_model = get_account_model()

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--show-portfolios', action='store_true',
            dest='show_portfolios', default=False,
            help='Show portfolios that do not match optins')
        parser.add_argument('--show-portfolios-fix', action='store_true',
            dest='show_portfolios_fix', default=False,
            help='Show SQL fixes for portfolios that do not match optins')
        parser.add_argument('--dry-run', action='store_true',
            dest='dry_run', default=False,
            help='Do not commit database updates')

    def handle(self, *args, **options):
        #pylint:disable=too-many-locals,too-many-statements
        start_time = datetime.datetime.utcnow()
        self.check_portfolios(
            show=options['show_portfolios'],
            show_fix=options['show_portfolios_fix'])
        end_time = datetime.datetime.utcnow()
        delta = relativedelta(end_time, start_time)
        LOGGER.info("completed in %d hours, %d minutes, %d.%d seconds",
            delta.hours, delta.minutes, delta.seconds, delta.microseconds)
        self.stdout.write("completed in %d hours, %d minutes, %d.%d seconds\n"
            % (delta.hours, delta.minutes, delta.seconds, delta.microseconds))


    def check_portfolios(self, show=False, show_fix=False):
        if show_fix:
            show = True
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
), outofsync_portfolios AS (
SELECT
    optins.grantee_id,
    optins.account_id,
    optins.campaign_id,
    optins.last_trigger_at,
    survey_portfolio.id,
    survey_portfolio.ends_at
FROM optins LEFT OUTER JOIN survey_portfolio ON (
    survey_portfolio.grantee_id = optins.grantee_id AND
    survey_portfolio.account_id = optins.account_id AND
    survey_portfolio.campaign_id = optins.campaign_id)
WHERE
    survey_portfolio.ends_at IS NULL OR
    optins.last_trigger_at > survey_portfolio.ends_at
    ORDER BY optins.last_trigger_at DESC, optins.grantee_id
), latest_completions AS (
SELECT
    account_id,
    MAX(created_at) AS latest_completed_at
FROM survey_sample
WHERE is_frozen AND extra IS NULL
GROUP BY account_id
), portfolios AS (
SELECT
    outofsync_portfolios.*,
    latest_completions.latest_completed_at AS latest_completed_at
FROM latest_completions
INNER JOIN outofsync_portfolios
ON latest_completions.account_id = outofsync_portfolios.account_id)
SELECT
  grantee_slug,
  %(account_table)s.slug AS account_slug,
  campaign_id,
  last_trigger_at,
  portfolio_id,
  ends_at,
  latest_completed_at
FROM (
SELECT
  %(account_table)s.slug AS grantee_slug,
  account_id,
  campaign_id,
  last_trigger_at,
  portfolios.id AS portfolio_id,
  ends_at,
  latest_completed_at
FROM portfolios INNER JOIN %(account_table)s
ON portfolios.grantee_id = %(account_table)s.id) AS portfolio_grantees
INNER JOIN %(account_table)s
ON portfolio_grantees.account_id = %(account_table)s.id
""" % {
    'grant_accepted': PortfolioDoubleOptIn.OPTIN_GRANT_ACCEPTED,
    'request_accepted': PortfolioDoubleOptIn.OPTIN_REQUEST_ACCEPTED,
    'account_table': self.account_model._meta.db_table
}
        count = 0
        sep = ""
        with connection.cursor() as cursor:
            cursor.execute(optins_query, params=None)
            for optin in cursor.fetchall():
                if show:
                    if not sep:
                        if show_fix:
                            self.stdout.write("BEGIN;")
                        else:
                            self.stdout.write("grantee_id,account_id,"\
                            "campaign_id,last_trigger_at,portfolio_id,ends_at")
                        sep = ",\n"
                    grantee_slug = optin[0]
                    account_slug = optin[1]
                    campaign_id = optin[2]
                    last_trigger_at = optin[3]
                    portfolio_id = optin[4]
                    ends_at = optin[5]
                    latest_completed_at = optin[6]
                    if show_fix:
                        if portfolio_id:
                            if campaign_id:
                                self.stdout.write(
                                    "UPDATE survey_portfolio SET"\
" ends_at='%(ends_at)s' WHERE grantee_id=(SELECT id FROM %(account_table)s"\
" WHERE slug='%(grantee_slug)s') AND account_id=(SELECT id"\
" FROM %(account_table)s WHERE slug='%(account_slug)s')"\
" AND campaign_id=%(campaign_id)s;" % {
                    'account_table': self.account_model._meta.db_table,
                    'grantee_slug': grantee_slug,
                    'account_slug': account_slug,
                    'ends_at': max(last_trigger_at, latest_completed_at),
                    'campaign_id': str(campaign_id) if campaign_id else "null"})
                            else:
                                self.stdout.write(
                                    "UPDATE survey_portfolio SET"\
" ends_at='%(ends_at)s' WHERE grantee_id=(SELECT id FROM %(account_table)s"\
" WHERE slug='%(grantee_slug)s') AND account_id=(SELECT id"\
" FROM %(account_table)s WHERE slug='%(account_slug)s')"\
" AND campaign_id IS NULL;" % {
                    'account_table': self.account_model._meta.db_table,
                    'grantee_slug': grantee_slug,
                    'account_slug': account_slug,
                    'ends_at': max(last_trigger_at, latest_completed_at)})
                        else:
                            self.stdout.write(
                                "INSERT INTO survey_portfolio (grantee_id,"\
"account_id,campaign_id,ends_at) VALUES ((SELECT id FROM %(account_table)s"\
" WHERE slug='%(grantee_slug)s'),(SELECT id FROM %(account_table)s"\
" WHERE slug='%(account_slug)s'),%(campaign_id)s,'%(ends_at)s');" % {
                    'account_table': self.account_model._meta.db_table,
                    'grantee_slug': grantee_slug,
                    'account_slug': account_slug,
                    'campaign_id': str(campaign_id) if campaign_id else "null",
                    'ends_at': max(last_trigger_at,
                                   latest_completed_at).strftime("%Y-%m-%d")})
                    else:
                        self.stdout.write("%s,%s,%s,%s,%s,%s,%s" % (
                            grantee_slug, account_slug,
                            str(campaign_id) if campaign_id else "-",
                            last_trigger_at.strftime("%Y-%m-%d"),
                            (latest_completed_at.strftime("%Y-%m-%d")
                             if latest_completed_at else "-"),
                            str(portfolio_id) if portfolio_id else "-",
                            ends_at.strftime("%Y-%m-%d") if ends_at else "-"))
                count += 1
        if sep and show_fix:
            self.stdout.write("COMMIT;")
        self.stderr.write("%d inaccurate portfolios" % count)
