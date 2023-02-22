# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
"""
This file contains SQL statements as building blocks for benchmarking
results in APIs, downloads, etc.
"""
from django.db.models.query import QuerySet, RawQuerySet
from survey.models import Sample
from survey.utils import is_sqlite3


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
    account_clause = ""
    if accounts:
        if isinstance(accounts, list):
            account_ids = "(%s)" % ','.join([
                str(account_id) for account_id in accounts])
        elif isinstance(accounts, QuerySet):
            account_ids = "(%s)" % ','.join([
                str(account.pk) for account in accounts])
        elif isinstance(accounts, RawQuerySet):
            account_ids = "(%s)" % accounts.query.sql
        account_clause += (
            "AND survey_sample.account_id IN %(account_ids)s" % {
                'account_ids': account_ids})
    if exclude_accounts:
        if isinstance(exclude_accounts, list):
            account_ids = "(%s)" % ','.join([
                str(account_id) for account_id in exclude_accounts])
        account_clause += (
            "AND survey_sample.account_id NOT IN %(account_ids)s" % {
                'account_ids': account_ids})

    daterange_clause = ""
    if start_at:
        daterange_clause += ("AND survey_sample.created_at >= '%s'" %
            start_at.isoformat())
    if ends_at:
        daterange_clause += ("AND survey_sample.created_at < '%s'" %
            ends_at.isoformat())

    extra_clause = ("survey_sample.extra IS NULL" if not extra
        else "survey_sample.extra like '%%%%%s%%%%'" % extra)

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
        prefix_clause = "AND survey_question.path LIKE '%s%%%%'" % prefix
    else:
        prefix_fields = ""
        prefix_join = ""
        prefix_clause = ""

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
          survey_sample.is_frozen AND %(extra_clause)s
          %(daterange_clause)s
          %(prefix_clause)s
          %(account_clause)s
    GROUP BY account_id) AS last_updates
ON survey_sample.account_id = last_updates.account_id AND
   survey_sample.created_at = last_updates.last_updated_at
WHERE survey_sample.is_frozen AND
      %(extra_clause)s
""" % {'campaign_id': campaign.pk,
       'daterange_clause': daterange_clause,
       'extra_clause': extra_clause,
       'prefix_fields': prefix_fields,
       'prefix_join': prefix_join,
       'prefix_clause': prefix_clause,
       'account_clause': account_clause}
    return Sample.objects.raw(sql_query)
