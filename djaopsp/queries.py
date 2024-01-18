# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.
"""
This file contains SQL statements as building blocks for benchmarking
results in APIs, downloads, etc.
"""
from django.db import connection
from django.db.models.query import QuerySet, RawQuerySet
from survey.models import PortfolioDoubleOptIn, Sample
from survey.queries import as_sql_date_trunc, is_sqlite3
from survey.settings import DB_PATH_SEP
from survey.utils import get_account_model

from .api.serializers import EngagementSerializer, ReportingSerializer
from .models import ScorecardCache
from .scores import get_score_calculator


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
                        grantees=None, start_at=None, ends_at=None,
                        filter_by=None, order_by=None):
    #pylint:disable=too-many-arguments,too-many-locals
    accounts_clause = ""
    if accounts:
        account_ids = ""
        if isinstance(accounts, list):
            account_ids = "(%s)" % ','.join([
                str(account_id) for account_id in accounts])
        elif isinstance(accounts, QuerySet):
            account_ids = "(%s)" % ','.join([
                str(account.pk) for account in accounts])
        elif isinstance(accounts, RawQuerySet):
            account_ids = "(%s)" % accounts.query.sql
        if account_ids:
            accounts_clause = "AND account_id IN %s" % account_ids
    grantees_clause = ""
    if grantees:
        grantees_clause = "AND grantee_id IN (%s)" % ",".join([
            str(account.pk) for account in grantees])

    campaign_clause = (
        "AND survey_portfoliodoubleoptin.campaign_id = %d" % campaign.pk)
    portfolio_campaign_clause = (
        "survey_portfolio.campaign_id = %d" % campaign.pk)
    after_clause = ""
    after_sample_created_clause = ""
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
portfolios AS (
  SELECT * FROM survey_portfolio
  WHERE %(portfolio_campaign_clause)s
      %(grantees_clause)s
      %(accounts_clause)s
),
-- last completed in validity period (includes invite period)
last_valid_completed AS (
  SELECT
    survey_sample.account_id,
    survey_sample.is_frozen,
    MAX(survey_sample.created_at) AS last_updated_at
  FROM survey_sample
  WHERE
    survey_sample.is_frozen AND
    survey_sample.extra IS NULL
    %(after_sample_created_clause)s
    %(before_sample_created_clause)s
  GROUP BY survey_sample.account_id, survey_sample.is_frozen
),
completed_by_accounts AS (
SELECT DISTINCT
  survey_sample.account_id,
  survey_sample.id,
  survey_sample.slug,
  survey_sample.created_at,
  requests.grantee_id AS grantee_id,
  CASE WHEN (portfolios.ends_at IS NOT NULL AND
             last_valid_completed.last_updated_at <= portfolios.ends_at)
           THEN %(REPORTING_COMPLETED)s
       WHEN requests.state = %(optin_request_denied)d
           THEN %(REPORTING_COMPLETED_DENIED)s
       ELSE %(REPORTING_COMPLETED_NOTSHARED)s END AS reporting_status
FROM survey_sample
INNER JOIN last_valid_completed
ON survey_sample.account_id = last_valid_completed.account_id AND
   survey_sample.created_at = last_valid_completed.last_updated_at AND
   survey_sample.is_frozen = last_valid_completed.is_frozen
INNER JOIN requests
ON requests.account_id = survey_sample.account_id
LEFT OUTER JOIN portfolios
ON survey_sample.account_id = portfolios.account_id AND
   requests.grantee_id = portfolios.grantee_id        -- avoids 'completed' and
                                      -- 'completed-notshared' in same queryset
WHERE (requests.ends_at IS NULL OR
       last_valid_completed.last_updated_at < requests.ends_at) AND
    (last_valid_completed.last_updated_at > requests.created_at OR
    portfolios.ends_at > requests.created_at)
),
updated_by_accounts AS (
SELECT DISTINCT
  survey_sample.account_id,
  survey_sample.id,
  survey_sample.slug,
  survey_sample.updated_at,
  %(REPORTING_UPDATED)s AS reporting_status
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
),
latest_completion AS (
SELECT
  survey_sample.account_id,
  survey_sample.is_frozen,
  requests.state,
  MAX(survey_sample.created_at) AS last_updated_at
FROM requests
INNER JOIN survey_sample ON
  requests.account_id = survey_sample.account_id
WHERE
  survey_sample.is_frozen AND
  survey_sample.extra IS NULL
  %(before_sample_created_clause)s
GROUP BY survey_sample.account_id, survey_sample.is_frozen, requests.state
)
SELECT
  %(accounts_table)s.slug,
  %(accounts_table)s.full_name AS printable_name,
  %(accounts_table)s.picture,
  %(accounts_table)s.extra,
  engaged.created_at AS requested_at,
  engaged.* FROM (
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
        THEN %(REPORTING_INVITED_DENIED)s
        ELSE %(REPORTING_INVITED)s END) AS reporting_status,
  COALESCE(
    completed_by_accounts.created_at,
    updated_by_accounts.updated_at,
    latest_completion.last_updated_at,
    null) AS last_activity_at
FROM requests
LEFT OUTER JOIN completed_by_accounts
ON requests.account_id = completed_by_accounts.account_id AND
   requests.grantee_id = completed_by_accounts.grantee_id
LEFT OUTER JOIN updated_by_accounts
ON requests.account_id = updated_by_accounts.account_id
LEFT OUTER JOIN latest_completion
ON requests.account_id = latest_completion.account_id
) AS engaged
INNER JOIN %(accounts_table)s
ON engaged.account_id = %(accounts_table)s.id
%(filter_by_clause)s
%(order_by_clause)s
""" % {
    'grantees_clause': grantees_clause,
    'campaign_clause': campaign_clause,
    'portfolio_campaign_clause': portfolio_campaign_clause,
    'accounts_clause': accounts_clause,
    'filter_by_clause': filter_by_clause,
    'order_by_clause': order_by_clause,
    'after_clause': after_clause,
    'after_sample_created_clause': after_sample_created_clause,
    'before_clause': before_clause,
    'before_sample_created_clause': before_sample_created_clause,
    'before_sample_updated_clause': before_sample_updated_clause,
    'optin_request_initiated': PortfolioDoubleOptIn.OPTIN_REQUEST_INITIATED,
    'optin_request_accepted': PortfolioDoubleOptIn.OPTIN_REQUEST_ACCEPTED,
    'optin_request_expired': PortfolioDoubleOptIn.OPTIN_REQUEST_EXPIRED,
    'optin_request_denied': PortfolioDoubleOptIn.OPTIN_REQUEST_DENIED,
    'accounts_table': get_account_model()._meta.db_table,
    'REPORTING_INVITED_DENIED': EngagementSerializer.REPORTING_INVITED_DENIED,
    'REPORTING_INVITED': EngagementSerializer.REPORTING_INVITED,
    'REPORTING_UPDATED': EngagementSerializer.REPORTING_UPDATED,
    'REPORTING_COMPLETED': EngagementSerializer.REPORTING_COMPLETED,
    'REPORTING_COMPLETED_DENIED': \
        EngagementSerializer.REPORTING_COMPLETED_DENIED,
    'REPORTING_COMPLETED_NOTSHARED': \
        EngagementSerializer.REPORTING_COMPLETED_NOTSHARED,
    }
    return sql_query


def get_engagement(campaign, accounts,
                   grantees=None, start_at=None, ends_at=None,
                   filter_by=None, order_by=None):
    #pylint:disable=too-many-arguments
    return PortfolioDoubleOptIn.objects.raw(
        _get_engagement_sql(campaign, accounts, grantees=grantees,
            start_at=start_at, ends_at=ends_at,
            filter_by=filter_by, order_by=order_by))


def get_engagement_by_reporting_status(campaign, accounts,
                                grantees=None, start_at=None, ends_at=None):
    # Implementation note: We use the order defined in
    # `EngagementSerializer.REPORTING_STATUSES` to collapse to a single
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
        campaign, accounts, grantees=grantees,
        start_at=start_at, ends_at=ends_at)}
    with connection.cursor() as cursor:
        cursor.execute(sql_query, params=None)
        results = {val[0]: val[1] for val in cursor.fetchall()}
    return results


def get_requested_by_accounts_by_period(campaign, includes, grantee,
                                        start_at=None, ends_at=None,
                                        period='yearly'):
    """
    Returns the most recent double-optin for each year between
    starts_at and ends_at for each account in includes.
    """
    #pylint:disable=too-many-arguments
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
           'survey_portfoliodoubleoptin.created_at', period=period),
       'date_range_clause': date_range_clause,
       'optin_request_states': ",".join([
           str(PortfolioDoubleOptIn.OPTIN_REQUEST_INITIATED),
           str(PortfolioDoubleOptIn.OPTIN_REQUEST_ACCEPTED),
           str(PortfolioDoubleOptIn.OPTIN_REQUEST_DENIED),
           str(PortfolioDoubleOptIn.OPTIN_REQUEST_EXPIRED)])
       }
    return PortfolioDoubleOptIn.objects.raw(sql_query)


def _get_frozen_query_sql(campaign, segments, ends_at, expired_at=None):
    frozen_assessments_query = None
    frozen_improvements_query = None

    for segment in segments:
        prefix = segment['path']
        segment_query = get_completed_assessments_at_by(
            campaign, ends_at=ends_at,
            prefix=prefix, title=segment['title']).query.sql
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
        segment_query = get_completed_assessments_at_by(
            campaign, ends_at=ends_at,
            prefix=prefix, title=segment['title'],
            extra='is_planned').query.sql
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


def _get_scorecard_cache_query_sql(segments, ends_at, expired_at=None):
    segments_query = segments_as_sql(segments)

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
""" % {
    'ends_at': ends_at.isoformat(),
    'segments_query': segments_query,
    'reporting_planning_clause': reporting_planning_clause,
    'reporting_completed_clause': reporting_completed_clause,
    #pylint:disable=protected-access
    'scorecardcache_table': ScorecardCache._meta.db_table
}
    return scorecard_cache_query


def _get_scored_assessments_sql(campaign, accounts=None,
                                scores_of_interest=None,
                                db_path=None, ends_at=None, expired_at=None,
                                sort_ordering=None):
    #pylint:disable=too-many-arguments,too-many-locals
    # The scores_of_interest do not represent solely segments. They might
    # also represent sections within a segment (see benchmarks API).
    # None-the-less as long as all segments in a survey are scored, this
    # code will work to differentiate between using the scorecard cache
    # and just getting frozen samples.
    use_scorecard_cache = False
    for seg in scores_of_interest:
        prefix = seg.get('path')
        if prefix:
            score_calculator = get_score_calculator(prefix)
            if score_calculator:
                use_scorecard_cache = True
                break
    if use_scorecard_cache:
        frozen_query = _get_scorecard_cache_query_sql(
            scores_of_interest, ends_at, expired_at=expired_at)
    else:
        frozen_query = _get_frozen_query_sql(
            campaign, scores_of_interest, ends_at, expired_at=expired_at)
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
    'reporting_status': ReportingSerializer.REPORTING_NOT_STARTED,
    'accounts_clause': accounts_clause,
    'order_clause': order_clause}

    return query


def get_scored_assessments(campaign, accounts=None,
                           scores_of_interest=None,
                           db_path=None, ends_at=None, expired_at=None,
                           sort_ordering=None):
    #pylint:disable=too-many-arguments
    sql_query = _get_scored_assessments_sql(
        campaign, accounts=accounts, scores_of_interest=scores_of_interest,
        db_path=db_path, ends_at=ends_at, expired_at=expired_at,
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
