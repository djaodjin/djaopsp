# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
"""
This file contains SQL statements as building blocks for benchmarking
results in APIs, downloads, etc.
"""
from django.db import connection
from django.db.models.query import QuerySet, RawQuerySet
from survey.models import PortfolioDoubleOptIn, Sample
from survey.queries import as_sql_date_trunc_year, is_sqlite3
from survey.utils import get_account_model


def get_completed_assessments_at_by(campaign, start_at=None, ends_at=None,
                            prefix=None, title="",
                            accounts=None, exclude_accounts=None,
                            extra=None):
    """
    Returns the most recent frozen assessment before an optionally specified
    date, indexed by account. Furthermore the query can be restricted to answers
    on a specific segment using `prefix` and matching text in the `extra` field.

    All accounts in ``excludes`` are not added to the index. This is
    typically used to filter out 'testing' accounts
    """
    #pylint:disable=too-many-arguments,too-many-locals
    sep = "AND "
    additional_filters = ""
    if accounts:
        if isinstance(accounts, list):
            account_ids = "(%s)" % ','.join([
                str(account_id) for account_id in accounts])
        elif isinstance(accounts, QuerySet):
            account_ids = "(%s)" % ','.join([
                str(account.pk) for account in accounts])
        elif isinstance(accounts, RawQuerySet):
            account_ids = "(%s)" % accounts.query.sql
        additional_filters += (
            "%(sep)ssurvey_sample.account_id IN %(account_ids)s" % {
                'sep': sep, 'account_ids': account_ids})
        sep = "AND "
    if exclude_accounts:
        if isinstance(exclude_accounts, list):
            account_ids = "(%s)" % ','.join([
                str(account_id) for account_id in exclude_accounts])
        additional_filters += (
            "%(sep)ssurvey_sample.account_id NOT IN %(account_ids)s" % {
                'sep': sep, 'account_ids': account_ids})
        sep = "AND "

    if start_at:
        additional_filters += "%ssurvey_sample.created_at >= '%s'" % (
            sep, start_at.isoformat())
        sep = "AND "
    if ends_at:
        additional_filters += "%ssurvey_sample.created_at < '%s'" % (
            sep, ends_at.isoformat())
        sep = "AND "

    if prefix:
        prefix_fields = """,
    '%(segment_prefix)s'%(convert_to_text)s AS segment_path,
    '%(segment_title)s'%(convert_to_text)s AS segment_title""" % {
        'segment_prefix': prefix,
        'segment_title': title,
        'convert_to_text': ("" if is_sqlite3() else "::text")
    }
        prefix_join = (
"""INNER JOIN survey_answer ON survey_answer.sample_id = survey_sample.id
INNER JOIN survey_question ON survey_answer.question_id = survey_question.id""")
        additional_filters += "%ssurvey_question.path LIKE '%s%%%%'" % (
            sep, prefix)
        sep = "AND "
    else:
        prefix_fields = ""
        prefix_join = ""

    extra_clause = sep + ("survey_sample.extra IS NULL" if not extra
        else "survey_sample.extra like '%%%%%s%%%%'" % extra)

    sql_query = """SELECT
    survey_sample.id AS id,
    survey_sample.slug AS slug,
    survey_sample.created_at AS created_at,
    survey_sample.campaign_id AS campaign_id,
    survey_sample.account_id AS account_id,
    survey_sample.updated_at AS updated_at,
    survey_sample.is_frozen AS is_frozen,
    survey_sample.extra AS extra%(prefix_fields)s
FROM survey_sample
INNER JOIN (
    SELECT
        account_id,
        MAX(survey_sample.created_at) AS last_updated_at
    FROM survey_sample
    %(prefix_join)s
    WHERE survey_sample.campaign_id = %(campaign_id)d AND
          survey_sample.is_frozen
          %(extra_clause)s
          %(additional_filters)s
    GROUP BY account_id) AS last_updates
ON survey_sample.account_id = last_updates.account_id AND
   survey_sample.created_at = last_updates.last_updated_at
WHERE survey_sample.is_frozen
      %(extra_clause)s
""" % {'campaign_id': campaign.pk,
       'extra_clause': extra_clause,
       'prefix_fields': prefix_fields,
       'prefix_join': prefix_join,
       'additional_filters': additional_filters}
    return Sample.objects.raw(sql_query)


def _get_engagement_sql(campaign, accounts,
                        grantees=None, start_at=None, ends_at=None):
    accounts_clause = ""
    if accounts:
        accounts_clause = "AND account_id IN (%s)" % ",".join([
            str(account.pk) for account in accounts])
    grantees_clause = ""
    if grantees:
        grantees_clause = "AND grantee_id IN (%s)" % ",".join([
            str(account.pk) for account in grantees])

    campaign_clause = (
        "AND survey_portfoliodoubleoptin.campaign_id = %d" % campaign.pk)
    after_clause = ""
    if start_at:
        after_clause = (
            "AND survey_portfoliodoubleoptin.created_at >= '%s'" % start_at)
    before_clause = ""
    before_sample_created_clause = ""
    before_sample_updated_clause = ""
    if ends_at:
        before_clause = (
            "AND survey_portfoliodoubleoptin.created_at < '%s'" % ends_at)
        before_sample_created_clause = (
            "AND survey_sample.created_at < '%s'"  % ends_at)
        before_sample_updated_clause = (
            "AND survey_sample.updated_at < '%s'"  % ends_at)

    sql_query = """
WITH requests AS (
SELECT survey_portfoliodoubleoptin.* FROM survey_portfoliodoubleoptin
INNER JOIN (
    SELECT
      grantee_id,
      account_id,
      MAX(created_at) AS created_at
    FROM survey_portfoliodoubleoptin
    WHERE
      state IN (
        %(optin_request_initiated)d,
        %(optin_request_accepted)d,
        %(optin_request_denied)d,
        %(optin_request_expired)d)
      %(campaign_clause)s
      %(after_clause)s
      %(before_clause)s
      %(grantees_clause)s
      %(accounts_clause)s
    GROUP BY grantee_id, account_id) AS latest_requests
ON  survey_portfoliodoubleoptin.grantee_id = latest_requests.grantee_id AND
    survey_portfoliodoubleoptin.account_id = latest_requests.account_id AND
    survey_portfoliodoubleoptin.created_at = latest_requests.created_at
    WHERE
      survey_portfoliodoubleoptin.state IN (
        %(optin_request_initiated)d,
        %(optin_request_accepted)d,
        %(optin_request_denied)d,
        %(optin_request_expired)d)
      %(campaign_clause)s
),
completed_by_accounts AS (
SELECT DISTINCT
  survey_sample.account_id,
  survey_sample.id,
  survey_sample.slug,
  survey_sample.created_at,
  CASE WHEN latest_completion.state = %(optin_request_accepted)d
           THEN 'completed'
       WHEN latest_completion.state = %(optin_request_denied)d
           THEN 'completed-denied'
       ELSE 'completed-notshared' END AS reporting_status
FROM survey_sample INNER JOIN (
  SELECT
    survey_sample.account_id,
    survey_sample.is_frozen,
    requests.state,
    MAX(survey_sample.created_at) AS last_updated_at
  FROM requests
  INNER JOIN survey_sample ON
    requests.account_id = survey_sample.account_id
  WHERE
    survey_sample.created_at >= requests.created_at AND
    survey_sample.is_frozen AND
    survey_sample.extra IS NULL
    %(before_sample_created_clause)s
  GROUP BY survey_sample.account_id, survey_sample.is_frozen, requests.state
) AS latest_completion
ON survey_sample.account_id = latest_completion.account_id AND
   survey_sample.created_at = latest_completion.last_updated_at AND
   survey_sample.is_frozen = latest_completion.is_frozen
),
updated_by_accounts AS (
SELECT DISTINCT
  survey_sample.account_id,
  survey_sample.id,
  survey_sample.slug,
  survey_sample.updated_at,
  'updated' AS reporting_status
FROM survey_sample INNER JOIN (
  SELECT
    survey_sample.account_id,
    MAX(survey_sample.updated_at) AS last_updated_at
  FROM requests
  INNER JOIN survey_sample ON
    requests.account_id = survey_sample.account_id
  WHERE
    survey_sample.updated_at >= requests.created_at AND
    survey_sample.extra IS NULL
    %(before_sample_updated_clause)s
  GROUP BY survey_sample.account_id, survey_sample.extra
  ) AS latest_update
ON survey_sample.account_id = latest_update.account_id AND
   survey_sample.updated_at = latest_update.last_updated_at
)
SELECT
  requests.*,
  COALESCE(
    completed_by_accounts.slug,
    updated_by_accounts.slug) AS sample,
  COALESCE(
    completed_by_accounts.id,
    updated_by_accounts.id) AS sample_id,
  COALESCE(
    completed_by_accounts.reporting_status,
    updated_by_accounts.reporting_status,
    CASE WHEN requests.state = %(optin_request_denied)d
        THEN 'invited-denied' ELSE 'invited' END) AS reporting_status,
  COALESCE(
    completed_by_accounts.created_at,
    updated_by_accounts.updated_at,
    null) AS last_activity_at
FROM requests
LEFT OUTER JOIN completed_by_accounts
ON requests.account_id = completed_by_accounts.account_id
LEFT OUTER JOIN updated_by_accounts
ON requests.account_id = updated_by_accounts.account_id
""" % {
    'grantees_clause': grantees_clause,
    'campaign_clause': campaign_clause,
    'before_clause': before_clause,
    'after_clause': after_clause,
    'accounts_clause': accounts_clause,
    'before_sample_created_clause': before_sample_created_clause,
    'before_sample_updated_clause': before_sample_updated_clause,
    'optin_request_initiated': PortfolioDoubleOptIn.OPTIN_REQUEST_INITIATED,
    'optin_request_accepted': PortfolioDoubleOptIn.OPTIN_REQUEST_ACCEPTED,
    'optin_request_expired': PortfolioDoubleOptIn.OPTIN_REQUEST_EXPIRED,
    'optin_request_denied': PortfolioDoubleOptIn.OPTIN_REQUEST_DENIED
    }
    return sql_query


def get_engagement(campaign, accounts,
                   grantees=None, start_at=None, ends_at=None):
    return PortfolioDoubleOptIn.objects.raw(
        _get_engagement_sql(campaign, accounts, grantees=grantees,
            start_at=start_at, ends_at=ends_at))


def get_engagement_by_reporting_status(campaign, accounts,
                                grantees=None, start_at=None, ends_at=None):
    sql_query = """
SELECT reporting_status, COUNT(account_id)
FROM (SELECT DISTINCT account_id, reporting_status FROM (%(engagement_sql)s)
  AS engagement) AS uniq_engagement
GROUP BY reporting_status
    """ % {'engagement_sql': _get_engagement_sql(
        campaign, accounts, grantees=grantees,
        start_at=start_at, ends_at=ends_at)}
    with connection.cursor() as cursor:
        cursor.execute(sql_query, params=None)
        results = {val[0]: val[1] for val in cursor.fetchall()}
    return results


def get_requested_by_accounts_by_year(campaign, includes, grantee,
                                      start_at=None, ends_at=None):
    """
    Returns the most recent double-optin for each year between
    starts_at and ends_at for each account in includes.
    """
    date_range_clause = ""
    if start_at:
        date_range_clause = (" AND survey_sample.created_at >= '%s'" %
            start_at.isoformat())
    if ends_at:
        date_range_clause += (" AND survey_sample.created_at < '%s'" %
            ends_at.isoformat())
    # We cannot use `self.requested_accounts.query` because `params` are
    # not quoted. don't ask.
    # https://code.djangoproject.com/ticket/25416
    account_ids = [str(account.pk) for account in includes]
    if not account_ids:
        return Sample.objects.none()

    accounts_query = "SELECT id, slug FROM %(accounts_table)s"\
        " WHERE id IN (%(account_ids)s)" % {
            'accounts_table': get_account_model()._meta.db_table,
            'account_ids': ','.join(account_ids)
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
    last_updates.year AS created_at
FROM survey_portfoliodoubleoptin
INNER JOIN (
    SELECT
        account_id,
        %(as_year)s AS year,
        MAX(survey_portfoliodoubleoptin.created_at) AS last_updated_at
    FROM survey_portfoliodoubleoptin
    INNER JOIN accounts ON
        survey_portfoliodoubleoptin.account_id = accounts.id
    WHERE survey_portfoliodoubleoptin.campaign_id = %(campaign_id)d AND
          survey_portfoliodoubleoptin.state IN (%(optin_request_states)s) AND
          survey_portfoliodoubleoptin.grantee_id IN (%(grantees)s)
          %(date_range_clause)s
    GROUP BY account_id, year) AS last_updates ON
   survey_portfoliodoubleoptin.account_id = last_updates.account_id AND
   survey_portfoliodoubleoptin.created_at = last_updates.last_updated_at
INNER JOIN accounts ON
   survey_portfoliodoubleoptin.account_id = accounts.id
ORDER BY account_id, created_at
""" % {'campaign_id': campaign.pk,
       'accounts_query': accounts_query,
       'grantees': ",".join([str(grantee.pk)]),
       'as_year': as_sql_date_trunc_year(
           'survey_portfoliodoubleoptin.created_at'),
       'date_range_clause': date_range_clause,
       'optin_request_states': ",".join([
           str(PortfolioDoubleOptIn.OPTIN_REQUEST_INITIATED),
           str(PortfolioDoubleOptIn.OPTIN_REQUEST_ACCEPTED),
           str(PortfolioDoubleOptIn.OPTIN_REQUEST_DENIED),
           str(PortfolioDoubleOptIn.OPTIN_REQUEST_EXPIRED)])
       }
    return PortfolioDoubleOptIn.objects.raw(sql_query)
