# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.
"""
This file contains SQL statements as building blocks for benchmarking
results in APIs, downloads, etc.
"""
from django.db import connection
from django.db.models.query import QuerySet, RawQuerySet
from survey.models import Campaign, PortfolioDoubleOptIn, Sample
from survey.queries import (as_sql_date_trunc, is_sqlite3,
    sql_latest_frozen_by_accounts, sql_latest_frozen_by_accounts_by_period)
from survey.settings import DB_PATH_SEP
from survey.utils import get_account_model

from . import humanize
from .api.serializers import ReportingSerializer
from .models import ScorecardCache
from .scores import get_score_calculator


def sql_latest_frozen_by_portfolio_by_period(period='yearly',
                                             campaign=None,
                                             start_at=None, ends_at=None,
                                             segment_prefix=None,
                                             segment_title="",
                                             accounts=None, grantees=None,
                                             exclude_accounts=None,
                                             tags=None):
    """
    Returns the latest frozen sample for each `period` between
    `starts_at` and `ends_at` for each account in `accounts`.

    To get only the latest sample,
    see `Sample.objects.get_latest_frozen_by_accounts`.
    """
    #pylint:disable=too-many-arguments,too-many-locals
    assert isinstance(campaign, Campaign)
    assert bool(grantees)

    accessible_samples_sql_query = sql_latest_frozen_by_accounts_by_period(
        period=period, campaign=campaign,
        start_at=start_at, ends_at=ends_at,
        segment_prefix=segment_prefix, segment_title=segment_title,
        accounts=accounts, grantees=grantees, tags=tags)

    samples_sql_query = sql_latest_frozen_by_accounts_by_period(
        period=period, campaign=campaign,
        start_at=start_at, ends_at=ends_at,
        segment_prefix=segment_prefix, segment_title=segment_title,
        accounts=accounts, grantees=None, tags=tags)
                    # `grantees=None` because we want the latest frozen
                    # sample regardless if it was shared or not when
                    # computing `last_completed_by_accounts_by_period`.

    portfolio_grantees_clause = ""
    if grantees:
        grantee_ids = []
        for grantee in grantees:
            try:
                grantee_ids += [str(grantee.pk)]
            except AttributeError:
                grantee_ids += [str(grantee)]
        grantee_ids = ','.join(grantee_ids)
        portfolio_grantees_clause += (
            " AND survey_portfolio.grantee_id IN (%(grantee_ids)s)" % {
                'grantee_ids': grantee_ids})

    context = {}
    context.update({
        'accessible_samples_sql_query': accessible_samples_sql_query,
        'samples_sql_query': samples_sql_query,
        'as_period': as_sql_date_trunc(
            'survey_sample.created_at', period_type=period),
        'portfolio_grantees_clause': portfolio_grantees_clause,
        'REPORTING_COMPLETED': humanize.REPORTING_COMPLETED,
        'REPORTING_COMPLETED_NOTSHARED': humanize.REPORTING_RESPONDED,
        'REPORTING_VERIFIED': humanize.REPORTING_VERIFIED})

    sql_query = """
WITH accessible_samples AS (
%(accessible_samples_sql_query)s
),
last_completed_by_accounts AS (
%(samples_sql_query)s
),
completed_by_accounts_by_period AS (
SELECT DISTINCT
  COALESCE(accessible_samples.id, last_completed_by_accounts.id) AS id,
  COALESCE(accessible_samples.slug, null) AS slug,
  COALESCE(accessible_samples.created_at,
    last_completed_by_accounts.created_at) AS created_at,
  COALESCE(accessible_samples.campaign_id,
    last_completed_by_accounts.campaign_id) AS campaign_id,
  COALESCE(accessible_samples.account_id,
    last_completed_by_accounts.account_id) AS account_id,
  COALESCE(accessible_samples.is_frozen,
    last_completed_by_accounts.is_frozen) AS is_frozen,
  COALESCE(accessible_samples.time_spent, null) AS time_spent,
  COALESCE(accessible_samples.extra, null) AS extra,
  COALESCE(accessible_samples.updated_at,
    last_completed_by_accounts.updated_at) AS updated_at,
  COALESCE(accessible_samples.period,
    last_completed_by_accounts.period) AS period,
  CASE WHEN (accessible_samples.created_at IS NULL OR
    accessible_samples.created_at < last_completed_by_accounts.created_at)
    THEN %(REPORTING_COMPLETED_NOTSHARED)s
    ELSE %(REPORTING_COMPLETED)s END AS reporting_status
FROM last_completed_by_accounts
LEFT OUTER JOIN accessible_samples
  ON last_completed_by_accounts.account_id = accessible_samples.account_id
  AND last_completed_by_accounts.campaign_id = accessible_samples.campaign_id
  AND last_completed_by_accounts.period = accessible_samples.period
INNER JOIN survey_portfolio
  ON last_completed_by_accounts.account_id = survey_portfolio.account_id
WHERE (survey_portfolio.campaign_id IS NULL OR
  survey_portfolio.campaign_id = last_completed_by_accounts.campaign_id)
  %(portfolio_grantees_clause)s
),
verified_by_accounts_by_period AS (
SELECT
  completed_by_accounts_by_period.id,
  completed_by_accounts_by_period.slug,
  completed_by_accounts_by_period.created_at,
  completed_by_accounts_by_period.campaign_id,
  completed_by_accounts_by_period.account_id,
  completed_by_accounts_by_period.is_frozen,
  completed_by_accounts_by_period.time_spent,
  completed_by_accounts_by_period.extra,
  completed_by_accounts_by_period.updated_at,
  completed_by_accounts_by_period.period,
  CASE WHEN (COALESCE(djaopsp_verifiedsample.verified_status, 0) > 1 AND
    completed_by_accounts_by_period.reporting_status = %(REPORTING_COMPLETED)s)
    THEN %(REPORTING_VERIFIED)s
    ELSE completed_by_accounts_by_period.reporting_status
    END AS reporting_status
FROM completed_by_accounts_by_period
LEFT OUTER JOIN djaopsp_verifiedsample
  ON completed_by_accounts_by_period.id = djaopsp_verifiedsample.sample_id
)
SELECT
  verified_by_accounts_by_period.*,
  verified_by_accounts_by_period.reporting_status AS state
FROM verified_by_accounts_by_period
ORDER BY
  verified_by_accounts_by_period.account_id,
  verified_by_accounts_by_period.created_at
""" % context
    return sql_query


def get_latest_frozen_by_portfolio_by_period(campaign, grantees,
                                             period='yearly',
                                             accounts=None,
                                             start_at=None, ends_at=None,
                                             segment_prefix=None,
                                             segment_title="",
                                             exclude_accounts=None,
                                             tags=None):
    #pylint:disable=too-many-arguments
    return Sample.objects.raw(sql_latest_frozen_by_portfolio_by_period(
        period=period, campaign=campaign, start_at=start_at, ends_at=ends_at,
        segment_prefix=segment_prefix, segment_title=segment_title,
        accounts=accounts, grantees=grantees,
        exclude_accounts=exclude_accounts,
        tags=tags))


def _get_engagement_sql(campaign=None,
                        start_at=None, ends_at=None,
                        segment_prefix=None, segment_title="",
                        accounts=None, grantees=None, tags=None,
                        filter_by=None, order_by=None):
    """
    Decorate samples with an engagement state (invited, completed, etc.)

    When `campaign` is specified, the state will only be computed for
    samples matching the `campaign`, otherwise it will default to 'no-data'.

    When `start_at` and/or `ends_at` are specified, the state will only be
    computed when the sample's account was invited during
    the [`start_at`, `ends_at`[ period.

    When `grantees` is specified, the the state will only be
    computed when the sample's account was invited by all `grantees`.
    """
    #pylint:disable=too-many-arguments,too-many-locals
    optin_primary_filters_clause = (
        "survey_portfoliodoubleoptin.state IN ("
        " %(optin_request_initiated)d, %(optin_request_accepted)d,"
        " %(optin_request_denied)d, %(optin_request_expired)d)" % {
        'optin_request_initiated': PortfolioDoubleOptIn.OPTIN_REQUEST_INITIATED,
        'optin_request_accepted': PortfolioDoubleOptIn.OPTIN_REQUEST_ACCEPTED,
        'optin_request_expired': PortfolioDoubleOptIn.OPTIN_REQUEST_EXPIRED,
        'optin_request_denied': PortfolioDoubleOptIn.OPTIN_REQUEST_DENIED})
    if campaign:
        optin_primary_filters_clause += (
            " AND survey_portfoliodoubleoptin.campaign_id = %(campaign_id)d" % {
                'campaign_id': campaign.pk})

    optin_secondary_filters_clause = ""
    if start_at:
        optin_secondary_filters_clause += (
            "AND survey_portfoliodoubleoptin.created_at >= '%s'" % start_at)
    if ends_at:
        optin_secondary_filters_clause += (
            "AND survey_portfoliodoubleoptin.created_at < '%(ends_at)s'" % {
                'ends_at': ends_at.isoformat()})
    if grantees:
        if isinstance(grantees, RawQuerySet):
            # XXX Is comment for account_ids not true here?
            grantee_ids = "%s" % grantees.query.sql
        else:
            grantee_ids = []
            for grantee in grantees:
                try:
                    grantee_ids += [str(grantee.pk)]
                except AttributeError:
                    grantee_ids += [str(grantee)]
            grantee_ids = ','.join(grantee_ids)
        optin_secondary_filters_clause += (
            " AND grantee_id IN (%(grantee_ids)s)" % {
            'grantee_ids': grantee_ids})
    if accounts:
        # In case we have a QuerySet or RawQuerySet, we still
        # cannot use `accounts.query.sql` because `params` are
        # not quoted. don't ask.
        # https://code.djangoproject.com/ticket/25416
        account_ids = []
        for account in accounts:
            try:
                account_ids += [str(account.pk)]
            except AttributeError:
                account_ids += [str(account)]
        account_ids = ','.join(account_ids)
        optin_secondary_filters_clause += (
            " AND account_id IN (%(account_ids)s)" % {
            'account_ids': account_ids})

    sample_before_created_clause = ""
    sample_before_updated_clause = ""
    if ends_at:
        sample_before_created_clause = (
            "AND survey_sample.created_at < '%(ends_at)s'"  % {
                'ends_at': ends_at.isoformat()})
        sample_before_updated_clause = (
            "AND survey_sample.updated_at < '%(ends_at)s'"  % {
                'ends_at': ends_at.isoformat()})

    sample_extra_filters_clause = ""
    if tags is not None:
        if tags:
            sample_extra_filters_clause += "".join([
                " AND LOWER(survey_sample.extra) LIKE '%%%s%%'" %
                tag.lower() for tag in tags])
        else:
            sample_extra_filters_clause += " AND survey_sample.extra IS NULL"

    filter_by_clause = ""
    if filter_by:
        filter_by_clause = "WHERE reporting_status IN (%s)" % ",".join(
            ["'%s'" % val for val in filter_by])
    order_by_clause = ""
    if order_by:
        order_by_clause = "ORDER BY "
        sep = ""
        for field_ordering in order_by:
            if field_ordering.startswith('-'):
                order_by_clause += "%s%s DESC" % (
                    sep, field_ordering.lstrip('-'))
                sep = ", "
            else:
                order_by_clause += "%s%s" % (
                    sep, field_ordering)
                sep = ", "

    samples_sql_query = sql_latest_frozen_by_accounts(
        campaign=campaign, start_at=start_at, ends_at=ends_at,
        segment_prefix=segment_prefix, segment_title=segment_title,
        accounts=accounts, tags=tags)

    sql_query = """
WITH latest_samples AS (
%(samples_sql_query)s
),
requests AS (
SELECT survey_portfoliodoubleoptin.* FROM survey_portfoliodoubleoptin
INNER JOIN (
    SELECT
      grantee_id,
      account_id,
      MAX(created_at) AS created_at
    FROM survey_portfoliodoubleoptin
    WHERE
      %(optin_primary_filters_clause)s
      %(optin_secondary_filters_clause)s
    GROUP BY grantee_id, account_id) AS last_requests
ON  survey_portfoliodoubleoptin.grantee_id = last_requests.grantee_id AND
    survey_portfoliodoubleoptin.account_id = last_requests.account_id AND
    survey_portfoliodoubleoptin.created_at = last_requests.created_at
    WHERE %(optin_primary_filters_clause)s
),
completed_by_accounts AS (
SELECT DISTINCT
  latest_samples.account_id,
  latest_samples.id,
  latest_samples.slug,
  latest_samples.created_at,
  requests.grantee_id AS grantee_id,
  CASE WHEN (survey_portfolio.ends_at IS NOT NULL AND
             latest_samples.created_at <= survey_portfolio.ends_at)
           THEN %(REPORTING_COMPLETED)s
       WHEN requests.state = %(optin_request_denied)d
           THEN %(REPORTING_COMPLETED_DENIED)s
       ELSE %(REPORTING_COMPLETED_NOTSHARED)s END AS reporting_status
FROM latest_samples
INNER JOIN requests
ON requests.account_id = latest_samples.account_id
LEFT OUTER JOIN survey_portfolio
ON latest_samples.account_id = survey_portfolio.account_id AND
   requests.grantee_id = survey_portfolio.grantee_id  -- avoids 'completed' and
                                      -- 'completed-notshared' in same queryset
WHERE (survey_portfolio.campaign_id IS NULL OR
       survey_portfolio.campaign_id = latest_samples.campaign_id)
    AND (requests.ends_at IS NULL OR
       latest_samples.created_at < requests.ends_at)
    AND (latest_samples.created_at > requests.created_at OR
       survey_portfolio.ends_at > requests.created_at)
),
verified_by_accounts AS (
SELECT
  completed_by_accounts.account_id,
  completed_by_accounts.id,
  completed_by_accounts.slug,
  completed_by_accounts.created_at,
  completed_by_accounts.grantee_id,
  CASE
    WHEN (COALESCE(djaopsp_verifiedsample.verified_status, 0) > 1 AND
     completed_by_accounts.reporting_status = %(REPORTING_COMPLETED_DENIED)s)
    THEN %(REPORTING_VERIFIED_DENIED)s
    WHEN (COALESCE(djaopsp_verifiedsample.verified_status, 0) > 1 AND
     completed_by_accounts.reporting_status = %(REPORTING_COMPLETED_NOTSHARED)s)
    THEN %(REPORTING_VERIFIED_NOTSHARED)s
    WHEN (COALESCE(djaopsp_verifiedsample.verified_status, 0) > 1 AND
     completed_by_accounts.reporting_status = %(REPORTING_COMPLETED)s)
    THEN %(REPORTING_VERIFIED)s
    ELSE completed_by_accounts.reporting_status
  END AS reporting_status
FROM completed_by_accounts
LEFT OUTER JOIN djaopsp_verifiedsample
ON completed_by_accounts.id = djaopsp_verifiedsample.sample_id
),
updated_by_accounts AS (
SELECT
  survey_sample.account_id,
  survey_sample.campaign_id,
  %(REPORTING_UPDATED)s AS reporting_status,
  MAX(survey_sample.updated_at) AS last_updated_at
FROM survey_sample
INNER JOIN requests ON
  requests.account_id = survey_sample.account_id AND
  requests.campaign_id = survey_sample.campaign_id
WHERE
  survey_sample.updated_at >= requests.created_at
  %(sample_extra_filters_clause)s
  %(sample_before_updated_clause)s
GROUP BY survey_sample.account_id, survey_sample.campaign_id
),
last_completed_by_accounts AS (
SELECT
  survey_sample.account_id,
  survey_sample.campaign_id,
  MAX(survey_sample.created_at) AS last_updated_at
FROM survey_sample
INNER JOIN requests ON
  requests.account_id = survey_sample.account_id AND
  requests.campaign_id = survey_sample.campaign_id
WHERE
  survey_sample.is_frozen
  %(sample_extra_filters_clause)s
  %(sample_before_created_clause)s
GROUP BY survey_sample.account_id, survey_sample.campaign_id
),
engaged AS (
SELECT
  requests.*,
  COALESCE(verified_by_accounts.slug, null) AS sample,
  COALESCE(verified_by_accounts.id, null) AS sample_id,
  COALESCE(
    verified_by_accounts.reporting_status,
    updated_by_accounts.reporting_status,
    CASE WHEN requests.state = %(optin_request_denied)d
        THEN %(REPORTING_INVITED_DENIED)s
        ELSE %(REPORTING_INVITED)s END) AS reporting_status,
  COALESCE(
    verified_by_accounts.created_at,
    updated_by_accounts.last_updated_at,
    last_completed_by_accounts.last_updated_at,
    null) AS last_activity_at
FROM requests
LEFT OUTER JOIN verified_by_accounts
ON requests.account_id = verified_by_accounts.account_id AND
   requests.grantee_id = verified_by_accounts.grantee_id
LEFT OUTER JOIN updated_by_accounts
ON requests.account_id = updated_by_accounts.account_id AND
   requests.campaign_id = updated_by_accounts.campaign_id
LEFT OUTER JOIN last_completed_by_accounts
ON requests.account_id = last_completed_by_accounts.account_id  AND
   requests.campaign_id = last_completed_by_accounts.campaign_id
)
SELECT
  %(accounts_table)s.slug,
  %(accounts_table)s.full_name AS printable_name,
  %(accounts_table)s.extra AS account_extra,
  engaged.id AS id,
  engaged.created_at AS requested_at,
  engaged.sample,
  engaged.sample_id,
  engaged.reporting_status,
  engaged.last_activity_at,
  engaged.account_id,
  engaged.campaign_id,
  engaged.grantee_id,
  engaged.initiated_by_id,
  engaged.extra
FROM engaged
INNER JOIN %(accounts_table)s
ON engaged.account_id = %(accounts_table)s.id
%(filter_by_clause)s
%(order_by_clause)s
""" % {
    'samples_sql_query': samples_sql_query,
    'optin_primary_filters_clause': optin_primary_filters_clause,
    'optin_secondary_filters_clause': optin_secondary_filters_clause,
    'filter_by_clause': filter_by_clause,
    'order_by_clause': order_by_clause,
    'sample_extra_filters_clause': sample_extra_filters_clause,
    'sample_before_created_clause': sample_before_created_clause,
    'sample_before_updated_clause': sample_before_updated_clause,
    'accounts_table': get_account_model()._meta.db_table,
    'optin_request_denied': PortfolioDoubleOptIn.OPTIN_REQUEST_DENIED,
    'REPORTING_INVITED_DENIED': humanize.REPORTING_INVITED_DENIED,
    'REPORTING_INVITED': humanize.REPORTING_INVITED,
    'REPORTING_UPDATED': humanize.REPORTING_UPDATED,
    'REPORTING_COMPLETED_DENIED': \
        humanize.REPORTING_COMPLETED_DENIED,
    'REPORTING_COMPLETED_NOTSHARED': \
        humanize.REPORTING_COMPLETED_NOTSHARED,
    'REPORTING_VERIFIED_DENIED': \
        humanize.REPORTING_VERIFIED_DENIED,
    'REPORTING_VERIFIED_NOTSHARED': \
        humanize.REPORTING_VERIFIED_NOTSHARED,
    'REPORTING_COMPLETED': humanize.REPORTING_COMPLETED,
    'REPORTING_VERIFIED': humanize.REPORTING_VERIFIED,
    }
    return sql_query


def get_engagement(campaign, accounts,
                   start_at=None, ends_at=None,
                   segment_prefix=None, segment_title="",
                   grantees=None, filter_by=None, order_by=None):
    #pylint:disable=too-many-arguments
    return PortfolioDoubleOptIn.objects.raw(_get_engagement_sql(
        campaign=campaign, start_at=start_at, ends_at=ends_at,
        segment_prefix=segment_prefix, segment_title=segment_title,
        accounts=accounts, grantees=grantees, tags=[],
        filter_by=filter_by, order_by=order_by))


# XXX This function is currently not used anymore
def get_coalesce_engagement(campaign, accounts,
                            grantees=None, start_at=None, ends_at=None,
                            filter_by=None, order_by=None):
    """
    While `get_engagement` might return an account multiple times, depending
    on how many {grantees} are specified, `get_coalesce_engagement` guarentees
    the returned queryset will contain each account only once.
    This is done at the expanse of the `reporting_status` field which is
    coalesce to the highest value accross all {grantees}.
    """
    #pylint:disable=too-many-arguments
    account_model = get_account_model()
    if not accounts:
        return account_model.objects.none()
    sql_query = """
SELECT
  engagement.account_id AS id,
  engagement.slug,
  engagement.printable_name AS full_name,
  engagement.extra,
  MAX(engagement.requested_at) AS requested_at,
  MAX(engagement.reporting_status) AS reporting_status
FROM (%(engagement_sql)s) AS engagement
-- WHERE reporting_status > 1 -- REPORTING_UPDATED
GROUP BY account_id, slug, printable_name, extra
    """ % {
        'engagement_sql': _get_engagement_sql(
            campaign=campaign, start_at=start_at, ends_at=ends_at,
            accounts=accounts, grantees=grantees,
            filter_by=filter_by, order_by=order_by)}
    return account_model.objects.raw(sql_query)


def get_engagement_by_reporting_status(campaign, accounts,
                                grantees=None, start_at=None, ends_at=None):
    # Implementation note: We use the order defined in
    # `humanize.REPORTING_STATUSES` to collapse to a single
    # reporting_status when an account managed reporting to multiple grantees
    # differently.
    sql_query = """
WITH uniq_engagement AS (
SELECT account_id, MAX(reporting_status) AS reporting_status
FROM (%(engagement_sql)s) AS engagement GROUP BY account_id
)
SELECT reporting_status, COUNT(account_id)
FROM uniq_engagement
GROUP BY reporting_status
    """ % {'engagement_sql': _get_engagement_sql(
        campaign=campaign, start_at=start_at, ends_at=ends_at,
        accounts=accounts, grantees=grantees)}
    with connection.cursor() as cursor:
        cursor.execute(sql_query, params=None)
        results = {val[0]: val[1] for val in cursor.fetchall()}
    return results


def get_requested_by_accounts_by_period(campaign, accounts, grantee,
                                        start_at=None, ends_at=None,
                                        period='yearly'):
    """
    Returns the most recent double-optin for each year between
    starts_at and ends_at for each account in accounts.
    """
    #pylint:disable=too-many-arguments
    date_range_clause = ""
    if start_at:
        date_range_clause = (
            " AND survey_portfoliodoubleoptin.created_at >= '%s'" %
            start_at.isoformat())
    if ends_at:
        date_range_clause += (
            " AND survey_portfoliodoubleoptin.created_at < '%s'" %
            ends_at.isoformat())

    if accounts:
        if isinstance(accounts, list):
            account_ids = []
            for account in accounts:
                try:
                    account_ids += [str(account.pk)]
                except AttributeError:
                    account_ids += [str(account)]
            account_ids = ','.join(account_ids)
        elif isinstance(accounts, QuerySet):
            account_ids = ','.join([
                str(account.pk) for account in accounts])
        elif isinstance(accounts, RawQuerySet):
            # We cannot use `accounts.query.sql` because `params` are
            # not quoted. don't ask.
            # https://code.djangoproject.com/ticket/25416
            account_ids = ','.join([
                str(account.pk) for account in accounts])
    else:
        return PortfolioDoubleOptIn.objects.none()

    accounts_query = "SELECT id, slug FROM %(accounts_table)s"\
        " WHERE id IN (%(account_ids)s)" % {
            'accounts_table': get_account_model()._meta.db_table,
            'account_ids': account_ids
        }
    sql_query = """
WITH accounts AS (
%(accounts_query)s
)
SELECT
    accounts.slug AS account_slug,
    survey_portfoliodoubleoptin.account_id AS account_id,
    survey_portfoliodoubleoptin.id AS id,
--    survey_portfoliodoubleoptin.created_at AS created_at,
    last_updates.period AS created_at
FROM survey_portfoliodoubleoptin
INNER JOIN (
    SELECT
        account_id,
        %(as_period)s AS period,
        MAX(survey_portfoliodoubleoptin.created_at) AS last_updated_at
    FROM survey_portfoliodoubleoptin
    INNER JOIN accounts ON
        survey_portfoliodoubleoptin.account_id = accounts.id
    WHERE survey_portfoliodoubleoptin.campaign_id = %(campaign_id)d AND
          survey_portfoliodoubleoptin.state IN (%(optin_request_states)s) AND
          survey_portfoliodoubleoptin.grantee_id IN (%(grantees)s)
          %(date_range_clause)s
    GROUP BY account_id, period) AS last_updates ON
   survey_portfoliodoubleoptin.account_id = last_updates.account_id AND
   survey_portfoliodoubleoptin.created_at = last_updates.last_updated_at
INNER JOIN accounts ON
   survey_portfoliodoubleoptin.account_id = accounts.id
ORDER BY account_id, created_at
""" % {'campaign_id': campaign.pk,
       'accounts_query': accounts_query,
       'grantees': ",".join([str(grantee.pk)]),
       'as_period': as_sql_date_trunc(
           'survey_portfoliodoubleoptin.created_at', period_type=period),
       'date_range_clause': date_range_clause,
       'optin_request_states': ",".join([
           str(PortfolioDoubleOptIn.OPTIN_REQUEST_INITIATED),
           str(PortfolioDoubleOptIn.OPTIN_REQUEST_ACCEPTED),
           str(PortfolioDoubleOptIn.OPTIN_REQUEST_DENIED),
           str(PortfolioDoubleOptIn.OPTIN_REQUEST_EXPIRED)])
       }
    return PortfolioDoubleOptIn.objects.raw(sql_query)


def _get_frozen_query_sql(campaign, segments, ends_at,
                          start_at=None, expired_at=None):
    frozen_assessments_query = None
    frozen_improvements_query = None

    for segment in segments:
        segment_prefix = segment['path']
        segment_query = Sample.objects.get_latest_frozen_by_accounts(
            campaign=campaign, start_at=start_at, ends_at=ends_at,
            segment_prefix=segment_prefix, segment_title=segment['title'],
            tags=[]).query.sql
        if not frozen_assessments_query:
            frozen_assessments_query = segment_query
        else:
            # SQLite3 doesn't like parentheses around UNION operands
            if is_sqlite3():
                frozen_assessments_query = "%s UNION %s" % (
                    frozen_assessments_query, segment_query)
            else:
                frozen_assessments_query = "(%s) UNION (%s)" % (
                    frozen_assessments_query, segment_query)
        segment_query = Sample.objects.get_latest_frozen_by_accounts(
            campaign=campaign, start_at=start_at, ends_at=ends_at,
            segment_prefix=segment_prefix, segment_title=segment['title'],
            tags=['is_planned']).query.sql
        if not frozen_improvements_query:
            frozen_improvements_query = segment_query
        else:
            if is_sqlite3():
                frozen_improvements_query = "%s UNION %s" % (
                    frozen_improvements_query, segment_query)
            else:
                frozen_improvements_query = "(%s) UNION (%s)" % (
                    frozen_improvements_query, segment_query)

    if not frozen_assessments_query or not frozen_improvements_query:
        # We don't have any segements of interest, so nothing to do.
        return ""

    if expired_at:
        reporting_clause = \
"""  CASE WHEN _frozen_assessments.created_at < '%(expired_at)s'
   THEN %(reporting_expired)d
   ELSE %(reporting_completed)d END""" % {
         'expired_at': expired_at.isoformat(),
         'reporting_completed': ReportingSerializer.REPORTING_PLANNING_PHASE,
         'reporting_expired': ReportingSerializer.REPORTING_ABANDONED
        }
    else:
        reporting_clause = "%d" % ReportingSerializer.REPORTING_PLANNING_PHASE
    frozen_assessments_query = """SELECT
  _frozen_assessments.id AS id,
  _frozen_assessments.slug AS slug,
  _frozen_assessments.created_at AS created_at,
  _frozen_assessments.campaign_id AS campaign_id,
  _frozen_assessments.account_id AS account_id,
  _frozen_assessments.updated_at AS updated_at,
  _frozen_assessments.is_frozen AS is_frozen,
  _frozen_assessments.extra AS extra,
  _frozen_assessments.segment_path AS segment_path,
  _frozen_assessments.segment_title AS segment_title,
  %(reporting_clause)s AS reporting_status
FROM (%(query)s) AS _frozen_assessments""" % {
    'query': frozen_assessments_query.replace('%', '%%'),
    'reporting_clause': reporting_clause}

    frozen_improvements_query = """SELECT
  _frozen_improvements.id AS id,
  _frozen_improvements.slug AS slug,
  _frozen_improvements.created_at AS created_at,
  _frozen_improvements.campaign_id AS campaign_id,
  _frozen_improvements.account_id AS account_id,
  _frozen_improvements.updated_at AS updated_at,
  _frozen_improvements.is_frozen AS is_frozen,
  _frozen_improvements.extra AS extra,
  _frozen_improvements.segment_path AS segment_path,
  _frozen_improvements.segment_title AS segment_title
FROM (%(query)s) AS _frozen_improvements""" % {
    'query': frozen_improvements_query.replace('%', '%%')}

    if expired_at:
        reporting_clause = \
"""  CASE WHEN frozen_assessments.created_at < '%(expired_at)s'
   THEN %(reporting_expired)d
   ELSE %(reporting_completed)d END""" % {
           'expired_at': expired_at.isoformat(),
           'reporting_completed': ReportingSerializer.REPORTING_COMPLETED,
           'reporting_expired': ReportingSerializer.REPORTING_EXPIRED
   }
    else:
        reporting_clause = "%d" % ReportingSerializer.REPORTING_COMPLETED
    frozen_query = """
WITH frozen_assessments AS (%(frozen_assessments_query)s),
frozen_improvements AS (%(frozen_improvements_query)s)
SELECT
  frozen_assessments.id AS id,
  frozen_assessments.slug AS slug,
  frozen_assessments.created_at AS created_at,
  frozen_assessments.campaign_id AS campaign_id,
  frozen_assessments.account_id AS account_id,
  frozen_assessments.updated_at AS updated_at,
  frozen_assessments.is_frozen AS is_frozen,
  frozen_assessments.extra AS extra,
  frozen_assessments.segment_path AS segment_path,
  frozen_assessments.segment_title AS segment_title,
  0 AS nb_na_answers,
  0 AS reporting_publicly,
  0 AS reporting_fines,
  0 AS reporting_energy_consumption,
  0 AS reporting_ghg_generated,
  0 AS reporting_water_consumption,
  0 AS reporting_waste_generated,
  0 AS nb_planned_improvements,
  0 AS reporting_energy_target,
  0 AS reporting_ghg_target,
  0 AS reporting_water_target,
  0 AS reporting_waste_target,
  0 AS normalized_score,
  CASE WHEN frozen_assessments.created_at < frozen_improvements.created_at
       THEN (%(reporting_clause)s)
       ELSE frozen_assessments.reporting_status END AS reporting_status
FROM frozen_assessments
LEFT OUTER JOIN frozen_improvements
ON frozen_assessments.account_id = frozen_improvements.account_id AND
   frozen_assessments.segment_path = frozen_improvements.segment_path""" % {
   'frozen_assessments_query': frozen_assessments_query,
   'frozen_improvements_query': frozen_improvements_query,
   'reporting_clause': reporting_clause}
    # Implementation Note: frozen_improvements will always pick the latest
    # improvement plan which might not be the ones associated with
    # the latest assessment if in a subsequent period no plan is created.
    return frozen_query


def _get_scorecard_cache_query_sql(segments, ends_at,
                                   start_at=None, expired_at=None):
    segments_query = segments_as_sql(segments)

    start_at_clause = ""
    if start_at:
        start_at_clause = "AND survey_sample.created_at >= '%(start_at)s'" % {
            'start_at': start_at.isoformat()
        }

    if expired_at:
        reporting_completed_clause = \
"""  CASE WHEN survey_sample.created_at < '%(expired_at)s'
   THEN %(reporting_expired)d
   ELSE %(reporting_completed)d END""" % {
           'expired_at': expired_at.isoformat(),
           'reporting_expired': ReportingSerializer.REPORTING_EXPIRED,
           'reporting_completed': ReportingSerializer.REPORTING_COMPLETED
   }
        reporting_planning_clause = \
"""  CASE WHEN survey_sample.created_at < '%(expired_at)s'
   THEN %(reporting_expired)d
   ELSE %(reporting_completed)d END""" % {
           'expired_at': expired_at.isoformat(),
           'reporting_expired': ReportingSerializer.REPORTING_ABANDONED,
           'reporting_completed': ReportingSerializer.REPORTING_PLANNING_PHASE
   }
    else:
        reporting_completed_clause = (
            "%d" % ReportingSerializer.REPORTING_COMPLETED)
        reporting_planning_clause = (
            "%d" % ReportingSerializer.REPORTING_PLANNING_PHASE)

    scorecard_cache_query = """WITH
segments AS (
  %(segments_query)s
),
scorecards AS (
  SELECT
    segments.path AS segment_path,
    segments.title AS segment_title,
    survey_sample.account_id AS account_id,
    MAX(survey_sample.created_at) AS created_at
  FROM %(scorecardcache_table)s
  INNER JOIN survey_sample
    ON %(scorecardcache_table)s.sample_id = survey_sample.id
  INNER JOIN segments
    ON %(scorecardcache_table)s.path = segments.path
  WHERE survey_sample.created_at <= '%(ends_at)s' -- '<=' bc `organization_rate`
    %(start_at_clause)s
  GROUP BY segments.path, segments.title, survey_sample.account_id
)
SELECT
  survey_sample.id AS id,
  survey_sample.slug AS slug,
  survey_sample.created_at AS created_at,
  survey_sample.campaign_id AS campaign_id,
  survey_sample.account_id AS account_id,
  survey_sample.updated_at AS updated_at,
  survey_sample.is_frozen AS is_frozen,
  survey_sample.extra AS extra,
  scorecards.segment_path AS segment_path,
  scorecards.segment_title AS segment_title,
  %(scorecardcache_table)s.nb_na_answers AS nb_na_answers,
  %(scorecardcache_table)s.reporting_publicly AS reporting_publicly,
  %(scorecardcache_table)s.reporting_fines AS reporting_fines,
  %(scorecardcache_table)s.reporting_energy_consumption AS reporting_energy_consumption,
  %(scorecardcache_table)s.reporting_ghg_generated AS reporting_ghg_generated,
  %(scorecardcache_table)s.reporting_water_consumption AS reporting_water_consumption,
  %(scorecardcache_table)s.reporting_waste_generated AS reporting_waste_generated,
  %(scorecardcache_table)s.reporting_energy_target AS reporting_energy_target,
  %(scorecardcache_table)s.reporting_ghg_target AS reporting_ghg_target,
  %(scorecardcache_table)s.reporting_water_target AS reporting_water_target,
  %(scorecardcache_table)s.reporting_waste_target AS reporting_waste_target,
  %(scorecardcache_table)s.nb_planned_improvements AS nb_planned_improvements,
  %(scorecardcache_table)s.normalized_score AS normalized_score,
  CASE WHEN %(scorecardcache_table)s.nb_planned_improvements > 0
       THEN (%(reporting_completed_clause)s)
       ELSE (%(reporting_planning_clause)s) END AS reporting_status
FROM %(scorecardcache_table)s
INNER JOIN scorecards
  ON %(scorecardcache_table)s.path = scorecards.segment_path
INNER JOIN survey_sample
  ON survey_sample.id = %(scorecardcache_table)s.sample_id AND
     survey_sample.account_id = scorecards.account_id AND
     survey_sample.created_at = scorecards.created_at
WHERE survey_sample.created_at <= '%(ends_at)s' -- '<=' bc `organization_rate`
    %(start_at_clause)s
""" % {
    'ends_at': ends_at.isoformat(),
    'start_at_clause': start_at_clause,
    'segments_query': segments_query,
    'reporting_planning_clause': reporting_planning_clause,
    'reporting_completed_clause': reporting_completed_clause,
    #pylint:disable=protected-access
    'scorecardcache_table': ScorecardCache._meta.db_table
}
    return scorecard_cache_query


def _get_scored_assessments_sql(campaign, accounts=None,
                                scores_of_interest=None, db_path=None,
                                start_at=None, ends_at=None, expired_at=None,
                                sort_ordering=None):
    #pylint:disable=too-many-arguments,too-many-locals
    # The scores_of_interest do not represent solely segments. They might
    # also represent sections within a segment (see benchmarks API).
    # None-the-less as long as all segments in a survey are scored, this
    # code will work to differentiate between using the scorecard cache
    # and just getting frozen samples.
    use_scorecard_cache = False
    for seg in scores_of_interest:
        segment_prefix = seg.get('path')
        if segment_prefix:
            score_calculator = get_score_calculator(segment_prefix)
            if score_calculator:
                use_scorecard_cache = True
                break
    if use_scorecard_cache:
        frozen_query = _get_scorecard_cache_query_sql(scores_of_interest,
            ends_at, start_at=start_at, expired_at=expired_at)
    else:
        frozen_query = _get_frozen_query_sql(campaign, scores_of_interest,
            ends_at, start_at=start_at, expired_at=expired_at)
    if not frozen_query:
        # We don't have any segements of interest, so nothing to do.
        return ""

    # We mark assessments completed prior to expired_at as expired.
    if expired_at:
        reporting_clause = \
"""  CASE WHEN active_assessments.created_at < '%(expired_at)s'
   THEN %(reporting_abandoned)d
   ELSE %(reporting_inprogress)d END""" % {
           'expired_at': expired_at.isoformat(),
           'reporting_inprogress':
               ReportingSerializer.REPORTING_ASSESSMENT_PHASE,
           'reporting_abandoned': ReportingSerializer.REPORTING_ABANDONED
   }
    else:
        reporting_clause = \
            "%d" % ReportingSerializer.REPORTING_ASSESSMENT_PHASE

    # If we are not returning results on a specific segment, we will
    # show all segments on a campaign.
    if db_path and db_path != DB_PATH_SEP:
        assessments_query = frozen_query
    else:
        assessments_query = """
WITH frozen AS (%(frozen_query)s)
SELECT
  COALESCE(frozen.id, active_assessments.id) AS id,
  COALESCE(frozen.slug, active_assessments.slug) AS slug,
  frozen.created_at AS created_at,
  COALESCE(frozen.campaign_id, active_assessments.campaign_id) AS campaign_id,
  COALESCE(frozen.account_id, active_assessments.account_id) AS account_id,
  active_assessments.updated_at AS updated_at,
  COALESCE(frozen.is_frozen, active_assessments.is_frozen) AS is_frozen,
  COALESCE(frozen.extra, active_assessments.extra) AS extra,
  frozen.segment_path AS segment_path,
  frozen.segment_title AS segment_title,
  frozen.nb_na_answers AS nb_na_answers,
  frozen.reporting_publicly AS reporting_publicly,
  frozen.reporting_fines AS reporting_fines,
  frozen.reporting_energy_consumption AS reporting_energy_consumption,
  frozen.reporting_ghg_generated AS reporting_ghg_generated,
  frozen.reporting_water_consumption AS reporting_water_consumption,
  frozen.reporting_waste_generated AS reporting_waste_generated,
  frozen.nb_planned_improvements AS nb_planned_improvements,
  frozen.reporting_energy_target AS reporting_energy_target,
  frozen.reporting_ghg_target AS reporting_ghg_target,
  frozen.reporting_water_target AS reporting_water_target,
  frozen.reporting_waste_target AS reporting_waste_target,
  frozen.normalized_score AS normalized_score,
  COALESCE(frozen.reporting_status, %(reporting_clause)s) AS reporting_status
FROM (SELECT
    survey_sample.id AS id,
    survey_sample.slug AS slug,
    survey_sample.created_at AS created_at,
    survey_sample.campaign_id AS campaign_id,
    survey_sample.account_id AS account_id,
    survey_sample.updated_at AS updated_at,
    survey_sample.is_frozen AS is_frozen,
    survey_sample.extra AS extra
    FROM survey_sample
    WHERE survey_sample.extra IS NULL AND
          NOT survey_sample.is_frozen AND
          survey_sample.campaign_id = %(campaign_id)d
) AS active_assessments
LEFT OUTER JOIN frozen
ON active_assessments.account_id = frozen.account_id AND
   active_assessments.campaign_id = frozen.campaign_id""" % {
       'frozen_query': frozen_query,
       'campaign_id': campaign.id,
       'reporting_clause': reporting_clause}

    # Select accounts
    account_model = get_account_model()
    accounts_clause = ""
    if accounts:
        if isinstance(accounts, list):
            account_ids = "(%s)" % ','.join([
                str(account_id) for account_id in accounts])
        elif isinstance(accounts, QuerySet):
            account_ids = "(%s)" % ','.join([
                str(account.pk) for account in accounts])
        elif isinstance(accounts, RawQuerySet):
            account_ids = "(%s)" % accounts.query.sql
        accounts_clause = "%(accounts_table)s.id IN %(account_ids)s" % {
            'accounts_table': account_model._meta.db_table,
            'account_ids': account_ids}
    if accounts_clause:
        accounts_clause = "WHERE %s" % accounts_clause

    order_clause = ""
    if sort_ordering:
        order_clause = "ORDER BY "
        sep = ""
        for sort_field, sort_dir in sort_ordering:
            order_clause += "%s%s %s" % (sep, sort_field, sort_dir)
            if sort_field in ('last_activity_at', 'last_completed_at'):
                order_clause += " NULLS LAST"
            sep = ", "

    query = """
WITH assessments AS (%(assessments_query)s)
SELECT
  assessments.id AS id,
  assessments.slug AS slug,
  assessments.created_at AS created_at,
  assessments.campaign_id AS campaign_id,
  COALESCE(assessments.account_id, %(accounts_table)s.id) AS account_id,
  assessments.updated_at AS updated_at,
  assessments.is_frozen AS is_frozen,
  assessments.extra AS extra,
  assessments.segment_path AS segment_path,
  assessments.segment_title AS segment,    -- XXX should be segment_title
  assessments.nb_na_answers AS nb_na_answers,
  assessments.reporting_publicly AS reporting_publicly,
  assessments.reporting_fines AS reporting_fines,
  assessments.reporting_energy_consumption AS reporting_energy_consumption,
  assessments.reporting_ghg_generated AS reporting_ghg_generated,
  assessments.reporting_water_consumption AS reporting_water_consumption,
  assessments.reporting_waste_generated AS reporting_waste_generated,
  assessments.nb_planned_improvements AS nb_planned_improvements,
  assessments.reporting_energy_target AS reporting_energy_target,
  assessments.reporting_ghg_target AS reporting_ghg_target,
  assessments.reporting_water_target AS reporting_water_target,
  assessments.reporting_waste_target AS reporting_waste_target,
  assessments.normalized_score AS normalized_score,
  COALESCE(assessments.reporting_status, %(reporting_status)d) AS reporting_status,
  %(accounts_table)s.slug AS account_slug,
  %(accounts_table)s.full_name AS printable_name,
  %(accounts_table)s.email AS email,
  %(accounts_table)s.phone AS phone,
  assessments.created_at AS last_completed_at,
  assessments.updated_at AS last_activity_at,
  '' AS score_url                              -- updated later
FROM %(accounts_table)s
%(join_clause)s JOIN assessments
ON %(accounts_table)s.id = assessments.account_id
%(accounts_clause)s
%(order_clause)s""" % {
    'assessments_query': assessments_query,
#XXX    'join_clause': "INNER" if self.db_path else "LEFT OUTER",
    'join_clause': "LEFT OUTER",
    'accounts_table': account_model._meta.db_table,
    'reporting_status': humanize.REPORTING_INVITED,
    'accounts_clause': accounts_clause,
    'order_clause': order_clause}

    return query


def get_scored_assessments(campaign, accounts=None,
                           scores_of_interest=None, db_path=None,
                           start_at=None, ends_at=None, expired_at=None,
                           sort_ordering=None):
    #pylint:disable=too-many-arguments
    sql_query = _get_scored_assessments_sql(campaign, accounts=accounts,
        scores_of_interest=scores_of_interest, db_path=db_path,
        start_at=start_at, ends_at=ends_at, expired_at=expired_at,
        sort_ordering=sort_ordering)
    if not sql_query:
        # We don't have any scorecard/chart to compute.
        return Sample.objects.none()
    return Sample.objects.raw(sql_query)


def segments_as_sql(segments):
    """
    Returns an SQL query from a list of segments encoded as
    {'path': ..., 'title': ...}.
    """
    segments_query = None
    for segment in segments:
        if segments_query:
            segments_query = "%(segments_query)s UNION "\
                "SELECT '%(segment_path)s'%(convert_to_text)s AS path,"\
                " '%(segment_title)s'%(convert_to_text)s AS title" % {
                    'segments_query': segments_query,
                    'segment_path': segment['path'],
                    'segment_title': segment['title'],
                    'convert_to_text': ("" if is_sqlite3() else "::text")
                }
        else:
            segments_query = \
                "SELECT '%(segment_path)s'%(convert_to_text)s AS path,"\
                " '%(segment_title)s'%(convert_to_text)s AS title" % {
                    'segment_path': segment['path'],
                    'segment_title': segment['title'],
                    'convert_to_text': ("" if is_sqlite3() else "::text")
                }
    return segments_query
