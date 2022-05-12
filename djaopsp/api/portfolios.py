# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import datetime, json, re
from collections import OrderedDict

from dateutil.relativedelta import relativedelta
from deployutils.helpers import datetime_or_now, parse_tz
from django.contrib.auth import get_user_model
from django.db import connection
from django.http import Http404
import pytz
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from pages.helpers import ContentCut
from pages.models import PageElement, build_content_tree
from survey.api.matrix import MatrixDetailAPIView
from survey.api.serializers import MetricsSerializer
from survey.helpers import get_extra
from survey.mixins import CampaignMixin, DateRangeContextMixin, TimersMixin
from survey.models import EditableFilter, Sample
from survey.utils import get_account_model, get_question_model, is_sqlite3

from ..compat import reverse, six
from ..api.serializers import AccountSerializer
from ..mixins import AccountMixin
from ..models import ScorecardCache
from ..utils import (get_reporting_accounts, get_requested_accounts,
    get_segments_candidates)


class CompletionSummaryPagination(PageNumberPagination):
    """
    Decorate the results of an API call with stats on completion of assessment
    and improvement planning.
    """

    def paginate_queryset(self, queryset, request, view=None):
        self.nb_organizations = 0
        self.reporting_publicly_count = 0
        self.no_assessment = 0
        self.abandoned = 0
        self.expired = 0
        self.assessment_phase = 0
        self.improvement_phase = 0
        self.completed = 0
        accounts = {}
        for sample in queryset:
            slug = sample.account_slug
            reporting_status = (sample.reporting_status
                if sample.reporting_status is not None
                else AccountSerializer.REPORTING_NOT_STARTED)
            if not slug in accounts:
                accounts[slug] = {
                    'reporting_status': reporting_status,
                   'reporting_publicly': bool(sample.reporting_publicly),
                    'reporting_fines': bool(sample.reporting_fines)
                }
                continue
            if reporting_status > accounts[slug]['reporting_status']:
                accounts[slug]['reporting_status'] = reporting_status
            if sample.reporting_publicly:
                accounts[slug]['reporting_publicly'] = True
            if sample.reporting_fines:
                accounts[slug]['reporting_fines'] = True

        self.nb_organizations = len(accounts)
        for account in six.itervalues(accounts):
            reporting_status = account.get(
                'reporting_status', AccountSerializer.REPORTING_NOT_STARTED)
            if reporting_status == AccountSerializer.REPORTING_ABANDONED:
                self.abandoned += 1
            elif reporting_status == AccountSerializer.REPORTING_EXPIRED:
                self.expired += 1
            elif (reporting_status
                  == AccountSerializer.REPORTING_ASSESSMENT_PHASE):
                self.assessment_phase += 1
            elif reporting_status == AccountSerializer.REPORTING_PLANNING_PHASE:
                self.improvement_phase += 1
            elif reporting_status == AccountSerializer.REPORTING_COMPLETED:
                self.completed += 1
            else:
                self.no_assessment += 1
            if account.get('reporting_publicly'):
                self.reporting_publicly_count += 1

        return super(CompletionSummaryPagination, self).paginate_queryset(
            queryset, request, view=view)

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('summary', (
                    ('Not started', self.no_assessment),
                    ('Abandoned', self.abandoned),
                    ('Expired', self.expired),
                    ('Assessment phase', self.assessment_phase),
                    ('Planning phase', self.improvement_phase),
                    ('Completed', self.completed),
            )),
            ('reporting_publicly_count', self.reporting_publicly_count),
            ('count', self.nb_organizations),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class DashboardMixin(TimersMixin, DateRangeContextMixin, CampaignMixin,
                     AccountMixin):
    """
    The dashboard contains the columns:
      - Supplier/facility: derived from `sample.account_id`
      - Last activity: derived from `sample.created_at` as long as
      (max(survey_answer.created_at) where survey_answer.sample_id = sample.id)
      < sample.created_at
      - Status: derived from last_assessment.is_frozen,
          last_assessment.created_at, last_improvement.created_at
      - Industry segment: derived from `get_segments(sample)`
      - Score: derived from answers with metric = score.
      - # N/A: derived from count(answer) where sample = last_assessment and
          answer.measured = 'N/A'
      - Reporting publicly: derived from exists(answer) where
          sample = last_assessment and answer.measured = 'yes' and
          answer.question = 'reporting publicly'
      - Environmental files: derived from exists(answer) where
          sample = last_assessment and answer.measured = 'yes' and
          answer.question = 'environmental fines'
      - Planned actions: derived from count(answer) where
          sample = last_improvement and answer.measured = 'improve'

    If we sort by "Supplier/facility", "# N/A", "Reporting publicly",
    or "Environmental files", it is possible to do it in the assessment SQL
    query.
    If we sort by "Planned actions", it is possible to do it in the improvement
    SQL query.
    If we sort by "Industry segment", it might be possible to do it in the
    assessment SQL query provided we decorate Samples with the industry.

    XXX If we sort by "Last activity"?
    XXX If we sort by "Status"?

    XXX If we sort by "Score", we have to re-compute all scores from answers.

    The queryset can be further filtered to a range of dates between
    ``start_at`` and ``ends_at``.

    The queryset can be further filtered by passing a ``q`` parameter.
    The value in ``q`` will be matched against:

      - user.username
      - user.first_name
      - user.last_name
      - user.email

    The result queryset can be ordered by passing an ``o`` (field name)
    and ``ot`` (asc or desc) parameter.
    The fields the queryset can be ordered by are:

      - user.first_name
      - user.last_name
      - created_at
    """
    model = Sample
    account_model = get_account_model()

    search_fields = ['printable_name',
                     'email']

    valid_sort_fields = {
        'printable_name': 'printable_name',
        'last_activity_at': 'last_activity_at',
        'reporting_status': 'reporting_status',
        'last_completed_at': 'last_completed_at',
        'segment': 'segment',
        'normalized_score': 'normalized_score',
        'nb_na_answers': 'nb_na_answers',
        'reporting_publicly': 'reporting_publicly',
        'reporting_fines': 'reporting_fines',
        'nb_planned_improvements': 'nb_planned_improvements',
        'reporting_energy_consumption': 'reporting_energy_consumption',
        'reporting_ghg_generated': 'reporting_ghg_generated',
        'reporting_water_consumption': 'reporting_water_consumption',
        'reporting_waste_generated': 'reporting_waste_generated',
        'reporting_energy_target': 'reporting_energy_target',
        'reporting_ghg_target': 'reporting_ghg_target',
        'reporting_water_target': 'reporting_water_target',
        'reporting_waste_target': 'reporting_waste_target'
    }

    valid_sort_dir = {
        'asc': 'asc',
        'desc': 'desc'
    }

    sample_queryset = Sample.objects.all()

    @property
    def expired_at(self):
        return self.start_at

    @property
    def search_param(self):
        if not hasattr(self, '_search_param'):
            self._search_param = self.request.GET.get('q', None)
        return self._search_param

    @property
    def sort_ordering(self):
        if not hasattr(self, '_sort_ordering'):
            sort_field = self.valid_sort_fields.get(
                self.request.GET.get('o', None))
            sort_dir = self.valid_sort_dir.get(
                self.request.GET.get('ot', 'desc'))
            if sort_field:
                self._sort_ordering = [(sort_field, sort_dir)]
            else:
                # defaults to alphabetical order for suppliers
                self._sort_ordering = [('printable_name', 'asc')]
        return self._sort_ordering

    def _get_frozen_query(self, segments):
        frozen_assessments_query = None
        frozen_improvements_query = None

        for segment in segments:
            prefix = segment['path']
            segment_query = self.sample_queryset.get_latest_assessments(
                prefix, before=self.ends_at, title=segment['title'])
            if not frozen_assessments_query:
                frozen_assessments_query = segment_query
            else:
                frozen_assessments_query = "(%s) UNION (%s)" % (
                    frozen_assessments_query, segment_query)
            segment_query = self.sample_queryset.get_latest_improvements(
                prefix, before=self.ends_at, title=segment['title'])
            if not frozen_improvements_query:
                frozen_improvements_query = segment_query
            else:
                frozen_improvements_query = "(%s) UNION (%s)" % (
                    frozen_improvements_query, segment_query)

        if self.expired_at:
            reporting_clause = \
"""  CASE WHEN _frozen_assessments.created_at < '%(expired_at)s'
       THEN %(reporting_expired)d
       ELSE %(reporting_completed)d END""" % {
             'expired_at': self.expired_at.isoformat(),
             'reporting_completed': AccountSerializer.REPORTING_PLANNING_PHASE,
             'reporting_expired': AccountSerializer.REPORTING_ABANDONED
            }
        else:
            reporting_clause = "%d" % AccountSerializer.REPORTING_PLANNING_PHASE
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
  _frozen_assessments.nb_na_answers AS nb_na_answers,
  _frozen_assessments.reporting_publicly AS reporting_publicly,
  _frozen_assessments.reporting_fines AS reporting_fines,
  _frozen_assessments.reporting_energy_consumption AS reporting_energy_consumption,
  _frozen_assessments.reporting_ghg_generated AS reporting_ghg_generated,
  _frozen_assessments.reporting_water_consumption AS reporting_water_consumption,
  _frozen_assessments.reporting_waste_generated AS reporting_waste_generated,
  _frozen_assessments.reporting_energy_target AS reporting_energy_target,
  _frozen_assessments.reporting_ghg_target AS reporting_ghg_target,
  _frozen_assessments.reporting_water_target AS reporting_water_target,
  _frozen_assessments.reporting_waste_target AS reporting_waste_target,
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
  _frozen_improvements.segment_title AS segment_title,
  _frozen_improvements.nb_planned_improvements AS nb_planned_improvements
FROM (%(query)s) AS _frozen_improvements""" % {
    'query': frozen_improvements_query.replace('%', '%%')}

        if self.expired_at:
            reporting_clause = \
"""  CASE WHEN frozen_assessments.created_at < '%(expired_at)s'
       THEN %(reporting_expired)d
       ELSE %(reporting_completed)d END""" % {
               'expired_at': self.expired_at.isoformat(),
               'reporting_completed': AccountSerializer.REPORTING_COMPLETED,
               'reporting_expired': AccountSerializer.REPORTING_EXPIRED
       }
        else:
            reporting_clause = "%d" % AccountSerializer.REPORTING_COMPLETED
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
  frozen_assessments.nb_na_answers AS nb_na_answers,
  frozen_assessments.reporting_publicly AS reporting_publicly,
  frozen_assessments.reporting_fines AS reporting_fines,
  frozen_assessments.reporting_energy_consumption AS reporting_energy_consumption,
  frozen_assessments.reporting_ghg_generated AS reporting_ghg_generated,
  frozen_assessments.reporting_water_consumption AS reporting_water_consumption,
  frozen_assessments.reporting_waste_generated AS reporting_waste_generated,
  frozen_assessments.reporting_energy_target AS reporting_energy_target,
  frozen_assessments.reporting_ghg_target AS reporting_ghg_target,
  frozen_assessments.reporting_water_target AS reporting_water_target,
  frozen_assessments.reporting_waste_target AS reporting_waste_target,
  CASE WHEN frozen_assessments.created_at < frozen_improvements.created_at
       THEN frozen_improvements.nb_planned_improvements
       ELSE 0 END AS nb_planned_improvements,
  null AS normalized_score,                     -- updated later
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
        # the latest assessment if in a subsequent year no plan is created.
        return frozen_query

    @staticmethod
    def _get_segments_query(segments):
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


    def _get_scorecard_cache_query(self, segments, ends_at=None):
        if not ends_at:
            ends_at = self.ends_at
        segments_query = self._get_segments_query(segments)

        if self.expired_at:
            reporting_completed_clause = \
"""  CASE WHEN survey_sample.created_at < '%(expired_at)s'
       THEN %(reporting_expired)d
       ELSE %(reporting_completed)d END""" % {
               'expired_at': self.expired_at.isoformat(),
               'reporting_expired': AccountSerializer.REPORTING_EXPIRED,
               'reporting_completed': AccountSerializer.REPORTING_COMPLETED
       }
            reporting_planning_clause = \
"""  CASE WHEN survey_sample.created_at < '%(expired_at)s'
       THEN %(reporting_expired)d
       ELSE %(reporting_completed)d END""" % {
               'expired_at': self.expired_at.isoformat(),
               'reporting_expired': AccountSerializer.REPORTING_ABANDONED,
               'reporting_completed': AccountSerializer.REPORTING_PLANNING_PHASE
       }
        else:
            reporting_completed_clause = (
                "%d" % AccountSerializer.REPORTING_COMPLETED)
            reporting_planning_clause = (
                "%d" % AccountSerializer.REPORTING_PLANNING_PHASE)

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
  WHERE survey_sample.created_at < '%(ends_at)s'
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
WHERE survey_sample.created_at < '%(ends_at)s'
""" % {
    'ends_at': ends_at.isoformat(),
    'segments_query': segments_query,
    'reporting_planning_clause': reporting_planning_clause,
    'reporting_completed_clause': reporting_completed_clause,
    #pylint:disable=protected-access
    'scorecardcache_table': ScorecardCache._meta.db_table
}
        return scorecard_cache_query

    def get_queryset(self):
        # XXX requested_accounts
        segments = []
        prefix = None
        if self.db_path:
            try:
                segments = [{
                    #XXX 'title': trail[-1].title,
                    'title': "",
                    'path': self.db_path,
                    'indent': len(self.db_path.split(self.DB_PATH_SEP)) - 1}]
            except Http404:
                prefix = None
        if not prefix:
            segments = get_segments_candidates(self.campaign)

        frozen_query = self._get_scorecard_cache_query(segments)

        if self.expired_at:
            reporting_clause = \
"""  CASE WHEN active_assessments.created_at < '%(expired_at)s'
       THEN %(reporting_abandoned)d
       ELSE %(reporting_inprogress)d END""" % {
               'expired_at': self.expired_at.isoformat(),
               'reporting_inprogress':
                   AccountSerializer.REPORTING_ASSESSMENT_PHASE,
               'reporting_abandoned': AccountSerializer.REPORTING_ABANDONED
       }
        else:
            reporting_clause = \
                "%d" % AccountSerializer.REPORTING_ASSESSMENT_PHASE

        if self.db_path:
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
       'campaign_id': self.campaign.id,
       'reporting_clause': reporting_clause}

        accounts_clause = ""
        if self.requested_accounts_pk:
            accounts_clause = "saas_organization.id IN (%s)" % ','.join(
                [str(pk) for pk in self.requested_accounts_pk])
            if self.search_param:
                if accounts_clause:
                    accounts_clause += "AND "
                accounts_clause += (
                    "saas_organization.full_name ILIKE '%%%%%s%%%%'" %
                    self.search_param)
        if accounts_clause:
            accounts_clause = "WHERE %s" % accounts_clause
        else:
            return Sample.objects.none()

        order_clause = ""
        if self.sort_ordering:
            order_clause = "ORDER BY "
            sep = ""
            for sort_field, sort_dir in self.sort_ordering:
                order_clause += "%s%s %s" % (sep, sort_field, sort_dir)
                if sort_field == 'last_activity_at':
                    order_clause += " NULLS LAST"
                sep = ", "
        query = """
WITH assessments AS (%(assessments_query)s)
SELECT
  assessments.id AS id,
  assessments.slug AS slug,
  assessments.created_at AS created_at,
  assessments.campaign_id AS campaign_id,
  COALESCE(assessments.account_id, saas_organization.id) AS account_id,
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
  saas_organization.slug AS account_slug,
  saas_organization.full_name AS printable_name,
  saas_organization.email AS email,
  saas_organization.phone AS phone,
  assessments.created_at AS last_completed_at,
  assessments.updated_at AS last_activity_at,
  '' AS score_url                              -- updated later
FROM saas_organization
%(join_clause)s JOIN assessments
ON saas_organization.id = assessments.account_id
%(accounts_clause)s
%(order_clause)s""" % {
    'assessments_query': assessments_query,
#XXX    'join_clause': "INNER" if self.db_path else "LEFT OUTER",
    'join_clause': "LEFT OUTER",
    'reporting_status': AccountSerializer.REPORTING_NOT_STARTED,
    'accounts_clause': accounts_clause,
    'order_clause': order_clause}

        # XXX still need to compute status and score.
        # XXX still need to add order by clause.
        return Sample.objects.raw(query)

    @property
    def query_supply_chain(self):
        if not hasattr(self, '_query_supply_chain'):
            self._query_supply_chain = bool(
                get_extra(self.account, 'supply_chain', False))
        return self._query_supply_chain

    @property
    def requested_accounts(self):
        if not hasattr(self, '_requested_accounts'):
            self._requested_accounts = self.get_requested_accounts(
            account=self.account, query_supply_chain=self.query_supply_chain)
        return self._requested_accounts

    @property
    def requested_accounts_pk(self):
        if not hasattr(self, '_requested_accounts_pk'):
            self._requested_accounts_pk = tuple(self.requested_accounts)
        return self._requested_accounts_pk

    @property
    def requested_accounts_pk_as_sql(self):
        if not hasattr(self, '_requested_accounts_pk_as_sql'):
            self._requested_accounts_pk_as_sql = "(%s)" % ','.join(
                [str(pk) for pk in self.requested_accounts_pk])
        return self._requested_accounts_pk_as_sql

    def get_reporting_accounts(self, account=None, query_supply_chain=True):
        """
        All accounts which have elected to share their scorecard
        with ``account``.
        """
        if not account:
            account = self.account
        return get_reporting_accounts(account,
            ends_at=self.ends_at, query_supply_chain=query_supply_chain)


    def get_requested_accounts(self, account=None, query_supply_chain=True):
        """
        All accounts which ``account`` has requested a scorecard from.
        """
        if not account:
            account = self.account
        return get_requested_accounts(account,
            ends_at=self.ends_at, query_supply_chain=query_supply_chain)


class DashboardAggregateMixin(DashboardMixin):
    """
    Builds aggregated reporting
    """
    scale = 1
    serializer_class = MetricsSerializer
    defaults_to_percent = True
    default_ends_at = '2022-01-01'

    @property
    def segments(self):
        if not hasattr(self, '_segments'):
            self._segments = get_segments_candidates(self.campaign)
        return self._segments

    def construct_monthly_periods(self, first_date=None, last_date=None,
                                  timezone=None, years=0):
        # XXX Use *years* to create comparative charts?
        if not last_date:
            last_date = datetime_or_now(self.default_ends_at)
        if not first_date:
            first_date = last_date - relativedelta(months=4)
        at_time = first_date
        tzinfo = parse_tz(timezone)
        if not tzinfo:
            tzinfo = pytz.utc
        week_ends_at = []
        while at_time < last_date:
            ends_at = datetime.datetime(
                year=at_time.year, month=at_time.month, day=1)
            if tzinfo:
                # we are interested in 00:00 local time, if we don't have
                # local time zone, fall back to 00:00 utc time
                # in case we have local timezone, replace utc with it
                ends_at = tzinfo.localize(ends_at.replace(tzinfo=None))
            week_ends_at += [ends_at]
            at_time += relativedelta(months=1)
        return week_ends_at

    def get_reporting_scorecards(self, account=None,
                                 start_at=None, ends_at=None):
        filter_params = {}
        if start_at:
            filter_params.update({
                'sample__created_at__gte': datetime_or_now(start_at)})
        if not ends_at:
            ends_at = self.ends_at
        filter_params.update({
            'sample__created_at__lt': datetime_or_now(ends_at)})

        reporting_accounts = self.get_reporting_accounts(account=account)
        if not reporting_accounts:
            return ScorecardCache.objects.none()

        accounts_clause = "AND account_id IN (%s)" % (
            ','.join([str(key) for key in reporting_accounts.keys()]))

        scorecards_query = """WITH
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
  WHERE survey_sample.created_at < '%(ends_at)s'
    %(accounts_clause)s
  GROUP BY segments.path, segments.title, survey_sample.account_id
)
SELECT %(scorecardcache_table)s.id FROM %(scorecardcache_table)s
INNER JOIN scorecards
  ON %(scorecardcache_table)s.path = scorecards.segment_path
INNER JOIN survey_sample
  ON survey_sample.id = %(scorecardcache_table)s.sample_id AND
     survey_sample.account_id = scorecards.account_id AND
     survey_sample.created_at = scorecards.created_at
""" % {
    'ends_at': ends_at.isoformat(),
    'segments_query': self._get_segments_query(self.segments),
    'accounts_clause': accounts_clause,
    #pylint:disable=protected-access
    'scorecardcache_table': ScorecardCache._meta.db_table
}

        # `ScorecardCache.objects.raw` is terminal so we need to get around it.
        with connection.cursor() as cursor:
            cursor.execute(scorecards_query, params=None)
            pks = [rec[0] for rec in cursor.fetchall()]
        scorecards = ScorecardCache.objects.filter(pk__in=pks)
        return scorecards

    @staticmethod
    def get_labels(aggregate=None):
        if not aggregate:
            return None
        return [val[0] for val in aggregate]

    def get_response_data(self, request, *args, **kwargs):
        #pylint:disable=unused-argument
        alliances = self.account_queryset.filter(
            plans__subscribers=self.account)
        account_aggregate = self.get_aggregate(
            self.account, labels=self.get_labels())
        table = [{
            'key': self.account.printable_name,
            'values': account_aggregate
        }]
        labels = self.get_labels(account_aggregate)
        for account in list(alliances):
            table += [{
                'key': account.printable_name,
                'values': self.get_aggregate(account, labels=labels)
            }]
        return {
            "title": self.title,
            'scale': self.scale,
            'unit': 'percentage' if self.defaults_to_percent else self.unit,
            'table': table
        }


class SupplierListMixin(DashboardMixin):
    """
    Scores for all reporting entities in a format that can be used by the API
    and spreadsheet downloads.
    """
    def decorate_queryset(self, queryset):
        """
        Updates `normalized_score` in rows of the queryset.
        """
        # Populate scores in report summaries
        contacts = {user.email: user
            for user in get_user_model().objects.filter(
                email__in=[account.email for account in queryset])}
        for report_summary in queryset:
            account = self.requested_accounts[report_summary.account_id]
            report_summary.extra = account.extra
            contact = contacts.get(report_summary.email)
            report_summary.contact_name = (
                contact.get_full_name() if contact else "")
            report_summary.requested_at = (
                account.requested_at if account.grant_key else None)
            if report_summary.requested_at:
                report_summary.nb_na_answers = None
                report_summary.reporting_publicly = None
                report_summary.reporting_fines = None
                report_summary.nb_planned_improvements = None
            elif report_summary.segment_path:
                parts = report_summary.segment_path.strip('/').split('/')
                segment_url = parts[-1] if parts else ""
                if report_summary.normalized_score is not None:
                    if report_summary.slug:
                        report_summary.score_url = reverse(
                            'scorecard', args=(
                            report_summary.account_slug,
                            report_summary.slug))
        self._report_queries("report summaries updated with scores")

    def get_nb_questions_per_segment(self):
        nb_questions_per_segment = {}
        for segment in get_segments_candidates(self.campaign):
            nb_questions = get_question_model().objects.filter(
                path__startswith=segment.path).count()
            nb_questions_per_segment.update({segment.path: nb_questions})
        return nb_questions_per_segment


    def paginate_queryset(self, queryset):
        page = super(SupplierListMixin, self).paginate_queryset(queryset)
        if page:
            queryset = page
        self.decorate_queryset(queryset)
        return page


class PortfolioResponsesAPIView(SupplierListMixin, generics.ListAPIView):
    """
    Lists assessments for reporting profiles

    List of suppliers accessible by the request user
    with normalized (total) score when the supplier completed
    an assessment.

    **Tags**: reporting

    **Examples

    .. code-block:: http

        GET /api/energy-utility/suppliers/ HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 1,
          "next": null,
          "previous": null,
          "results":[
          {
              "slug": "andy-shop",
              "printable_name": "Andy's Shop",
              "email": "andy@localhost.localdomain",
              "last_activity_at": "2016-07-15T00:36:19.448000Z",
              "requested_at": null,
              "reporting_status": "Planning phase",
              "segment": "",
              "score_url": "",
              "normalized_score": null,
              "nb_na_answers": null,
              "reporting_publicly": null,
              "reporting_fines": null,
              "nb_planned_improvements": null,
              "tags": ["high_impact"]
          },
          {
              "slug": "supplier-1",
              "printable_name": "S1 - Tamerin (Demo)",
              "email": "steve@localhost.localdomain",
              "last_activity_at": "2017-01-01T00:00:00Z",
              "requested_at": null,
              "reporting_status": "Completed",
              "segment": "Boxes & enclosures",
              "score_url": "/app/supplier-1/scorecard/\
f1e2e916eb494b90f9ff0a36982341/content/boxes-and-enclosures/",
              "normalized_score": 90,
              "nb_na_answers": 1,
              "reporting_publicly": true,
              "reporting_fines": null,
              "nb_planned_improvements": 1,
              "tags": []
          }
          ]
        }
    """
    serializer_class = AccountSerializer
    pagination_class = CompletionSummaryPagination

    def get(self, request, *args, **kwargs):
        self._start_time()
        resp = self.list(request, *args, **kwargs)
        self._report_queries("http response created")
        return resp


class GraphMixin(object):

    def get_charts(self, rollup_tree, excludes=None):
        charts = []
        icon_tag = rollup_tree[0].get('tag', "")
        if icon_tag and TransparentCut.TAG_SCORECARD in icon_tag:
            if not (excludes and rollup_tree[0].get('slug', "") in excludes):
                charts += [rollup_tree[0]]
        for _, icon_tuple in six.iteritems(rollup_tree[1]):
            sub_charts = self.get_charts(icon_tuple, excludes=excludes)
            charts += sub_charts
        return charts

    def create_distributions(self, rollup_tree, view_account=None):
        #pylint:disable=too-many-statements
        """
        Create a tree with distributions of scores from a rollup tree.
        """
        #pylint:disable=too-many-locals
        denominator = None
        highest_normalized_score = 0
        sum_normalized_scores = 0
        nb_normalized_scores = 0
        nb_respondents = 0
        nb_implemeted_respondents = 0
        distribution = None
        for account_id_str, account_metrics in six.iteritems(rollup_tree[0].get(
                'accounts', OrderedDict({}))):
            if account_id_str is None: # XXX why is that?
                continue
            account_id = int(account_id_str)
            is_view_account = (view_account and account_id == view_account)

            if is_view_account:
                rollup_tree[0].update(account_metrics)

            if account_metrics.get('nb_answers', 0):
                nb_respondents += 1

            normalized_score = account_metrics.get('normalized_score', None)
            if normalized_score is None:
                continue

            nb_normalized_scores += 1
            numerator = account_metrics.get('numerator')
            denominator = account_metrics.get('denominator')
            if numerator == denominator:
                nb_implemeted_respondents += 1
            if normalized_score > highest_normalized_score:
                highest_normalized_score = normalized_score
            sum_normalized_scores += normalized_score
            if distribution is None:
                distribution = {
                    'x' : ["0-25%", "25-50%", "50-75%", "75-100%"],
                    'y' : [0 for _ in range(4)],
                    'organization_rate': ""
                }
            if normalized_score < 25:
                distribution['y'][0] += 1
                if is_view_account:
                    distribution['organization_rate'] = distribution['x'][0]
            elif normalized_score < 50:
                distribution['y'][1] += 1
                if is_view_account:
                    distribution['organization_rate'] = distribution['x'][1]
            elif normalized_score < 75:
                distribution['y'][2] += 1
                if is_view_account:
                    distribution['organization_rate'] = distribution['x'][2]
            else:
                assert normalized_score <= 100
                distribution['y'][3] += 1
                if is_view_account:
                    distribution['organization_rate'] = distribution['x'][3]

        for node_metrics in six.itervalues(rollup_tree[1]):
            self.create_distributions(node_metrics, view_account=view_account)

        if distribution is not None:
            if nb_respondents > 0:
                avg_normalized_score = int(
                    sum_normalized_scores / nb_normalized_scores)
                rate = int(100.0
                    * nb_implemeted_respondents / nb_normalized_scores)
            else:
                avg_normalized_score = 0
                rate = 0
            rollup_tree[0].update({
                'nb_respondents': nb_respondents,
                'rate': rate,
                'opportunity': denominator,
                'highest_normalized_score': highest_normalized_score,
                'avg_normalized_score': avg_normalized_score,
                'distribution': distribution
            })
        if 'accounts' in rollup_tree[0]:
            del rollup_tree[0]['accounts']

    def flatten_distributions(self, distribution_tree, prefix=None):
        """
        Flatten the tree into a list of charts.
        """
        # XXX Almost identical to get_charts. Can we abstract differences?
        if prefix is None:
            prefix = "/"
        if not prefix.startswith("/"):
            prefix = '/%s' % prefix
        charts = []
        complete = True
        for key, chart in six.iteritems(distribution_tree[1]):
            if key.startswith(prefix) or prefix.startswith(key):
                leaf_charts, leaf_complete = self.flatten_distributions(
                    chart, prefix=prefix)
                charts += leaf_charts
                complete &= leaf_complete
                charts += [chart[0]]
                if 'distribution' in chart[0]:
                    normalized_score = chart[0].get('normalized_score', None)
                    complete &= (normalized_score is not None)
        return charts, complete


class TransparentCut(object):

    TAG_SCORECARD = 'scorecard'

    def __init__(self, depth=1):
        self.depth = depth

    def enter(self, tag):
        #pylint:disable=unused-argument
        self.depth = self.depth + 1
        return True

    def leave(self, attrs, subtrees):
        self.depth = self.depth - 1
        # `transparent_to_rollover` is meant to speed up computations
        # when the resulting calculations won't matter to the display.
        # We used to compute decide `transparent_to_rollover` before
        # the recursive call (see commit c421ca5) but it would not
        # catch the elements tagged deep in the tree with no chained
        # presentation.
        try:
            tags = attrs.get('extra', {}).get('tags', [])
        except AttributeError:
            tags = []
        attrs['transparent_to_rollover'] = not (
            tags and self.TAG_SCORECARD in tags)
        for subtree in six.itervalues(subtrees):
            try:
                tags = attrs.get('extra', {}).get('tags', [])
            except AttributeError:
                tags = []
            if tags and self.TAG_SCORECARD in tags:
                attrs['transparent_to_rollover'] = False
                break
            if not subtree[0].get('transparent_to_rollover', True):
                attrs['transparent_to_rollover'] = False
                break
        return not attrs['transparent_to_rollover']


class TotalScoreBySubsectorAPIView(SupplierListMixin, GraphMixin,
                                   MatrixDetailAPIView):
    """
    Retrieves a matrix of scores for cohorts against a metric

    Uses the total score for each organization as recorded
    by the assessment surveys and present aggregates
    by industry sub-sectors (Boxes & enclosures, etc.)

    **Tags**: reporting

    **Examples**

    .. code-block:: http

        GET /api/energy-utility/matrix/totals HTTP/1.1

    responds

    .. code-block:: json

        [
          {
           "slug": "totals",
           "title": "Average scores by supplier industry sub-sector",
           "tag": ["scorecard"],
           "cohorts": [{
               "slug": "/portfolio-a",
               "title": "Portfolio A",
                "tags": null,
                "predicates": [],
               "likely_metric": "/app/energy-utility/portfolios/portfolio-a/"
           }],
           "values": {
               "/portfolio-a": 0.1,
               "/portfolio-b": 0.5
           }
          }
        ]
    """

    def get_accounts(self):
        # overrides `MatrixDetailAPIView.get_accounts()`
        return self.get_reporting_accounts(
            account=self.account, query_supply_chain=self.query_supply_chain)

    @staticmethod
    def as_metric_candidate(cohort_slug):
        look = re.match(r"(\S+)(-\d+)$", cohort_slug)
        if look:
            return look.group(1)
        return cohort_slug

    def get_drilldown(self, rollup_tree, prefix):
        accounts = None
        node = rollup_tree[1].get(prefix, None)
        if node:
            accounts = rollup_tree[0].get('accounts', OrderedDict({}))
        elif prefix == 'totals' or rollup_tree[0].get('slug', '') == prefix:
            accounts = rollup_tree[0].get('accounts', OrderedDict({}))
        else:
            for node in six.itervalues(rollup_tree[1]):
                accounts = self.get_drilldown(node, prefix)
                if accounts is not None:
                    break
        # Filter out accounts whose score cannot be computed.
        if accounts is not None:
            all_accounts = accounts
            accounts = OrderedDict({})
            for account_id, account_metrics in six.iteritems(all_accounts):
                normalized_score = account_metrics.get('normalized_score', None)
                if normalized_score is not None:
                    accounts[account_id] = account_metrics

        return accounts

    def _cut_tree(self, roots, cut=None):
        """
        Cuts subtrees out of *roots* when they match the *cut* parameter.
        *roots* has a format compatible with the data structure returned
        by `build_content_tree`.

        code::
            {
              "/boxes-and-enclosures": [
                { ... data for node ... },
                {
                  "boxes-and-enclosures/management": [
                  { ... data for node ... },
                  {}],
                  "boxes-and-enclosures/design": [
                  { ... data for node ... },
                  {}],
                }]
            }
        """
        for node_path, node in list(six.iteritems(roots)):
            self._cut_tree(node[1], cut=cut)
            if cut and not cut.leave(node[0], node[1]):
                del roots[node_path]
        return roots

    def get_scores_tree(self, roots=None, prefix=None):
        """
        Returns a tree specialized to compute rollup scores.

        Typically `get_leafs` and a function to populate a leaf will be called
        before an rollup is done.
        """
        self._report_queries("[get_scores_tree] entry point")
        rollup_tree = None
        rollups = self._cut_tree(build_content_tree(roots, prefix=prefix),
            cut=TransparentCut())

        # Moves up all industry segments which are under a category
        # (ex: /facilities/janitorial-services).
        # If we donot do that, then assessment score will be incomplete
        # in the dashboard, as the aggregator will wait for other sub-segments
        # in the top level category.
        removes = []
        ups = OrderedDict({})
        for root_path, root in six.iteritems(rollups):
            try:
                tags = root[0].get('extra', {}).get('tags', [])
            except AttributeError:
                tags = []
            if ContentCut.TAG_PAGEBREAK not in tags:
                removes += [root_path]
                ups.update(root[1])
        for root_path in removes:
            del rollups[root_path]
        rollups.update(ups)

        rollup_tree = (OrderedDict({}), rollups)
        if 'title' not in rollup_tree[0]:
            rollup_tree[0].update({
                'slug': "totals",
                'title': "Total Score",
                'tag': [TransparentCut.TAG_SCORECARD]})
        self._report_queries("[get_scores_tree] generated")
        return rollup_tree

    def get_score_weight(self, path):
        if not hasattr(self, '_weights'):
            try:
                self._weights = json.loads(self.campaign.extra)
            except (TypeError, ValueError):
                self._weights = {}
        return self._weights.get(path, 1.0)

    def _insert_in_tree(self, rollup_tree, prefix, value):
        for path, node in six.iteritems(rollup_tree[1]):
            if path == prefix:
                accounts = node[0].get('accounts', {})
                account = accounts.get(value.account_id, {})
                account.update({'normalized_score': value.normalized_score})
                if value.account_id not in accounts:
                    accounts.update({value.account_id: account})
                if 'accounts' not in node[0]:
                    node[0].update({'accounts': accounts})
                return True
            if self._insert_in_tree(node, prefix, value):
                return True
        return False

    def rollup_scores(self, queryset, prefix=None):
        roots = None
        if prefix:
            try:
                roots = [PageElement.objects.get(
                    slug=prefix.split(self.DB_PATH_SEP)[-1])]
            except PageElement.DoesNotExist:
                roots = None
        rollup_tree = self.get_scores_tree(roots, prefix=prefix)
        self._report_queries("%d score tree loaded" % len(rollup_tree))
        for score in queryset:
            self._insert_in_tree(rollup_tree, score.segment_path, score)

        self._report_queries("completed rollup_scores")
        return rollup_tree

    def aggregate_scores(self, metric, cohorts, cut=None, accounts=None):
        #pylint:disable=unused-argument
        if accounts is None:
            accounts = get_account_model().objects.all()
        scores = {}
        rollup_tree = self.rollup_scores(self.get_queryset())
        rollup_scores = self.get_drilldown(rollup_tree, metric.slug)
        for cohort in cohorts:
            score = 0
            if isinstance(cohort, EditableFilter):
                if metric.slug == 'totals':
                    # Hard-coded: on the totals matrix we want to use
                    # a different metric for each cohort/column shown.
                    rollup_scores = self.get_drilldown(
                        rollup_tree, self.as_metric_candidate(cohort.slug))
                includes, excludes = cohort.as_kwargs()
                nb_accounts = 0
                for account in accounts.filter(**includes).exclude(**excludes):
                    account_score = rollup_scores.get(account.pk, None)
                    if account_score is not None:
                        score += account_score.get('normalized_score', 0)
                        nb_accounts += 1
                if nb_accounts > 0:
                    score = score / nb_accounts
            else:
                account = cohort
                account_score = rollup_scores.get(account.pk, None)
                if account_score is not None:
                    score = account_score.get('normalized_score', 0)
            scores.update({str(cohort): score})
        return scores

    def get_likely_metric(self, cohort_slug, default=None):
        #pylint:disable=arguments-differ
        if not default and self.matrix is not None:
            default = self.matrix.slug
        likely_metric = None
        look = re.match(r"(\S+)(-\d+)$", cohort_slug)
        if look:
            try:
                likely_metric = reverse('matrix_chart', args=(self.account,
                    self.campaign,
                    EditableFilter.objects.get(slug=look.group(1)).slug,))
            except EditableFilter.DoesNotExist:
                pass
        if likely_metric is None:
            # XXX default is derived from `prefix` argument
            # to `decorate_with_scores`.
            likely_metric = reverse('scorecard',
                args=(cohort_slug, default))
        if likely_metric:
            likely_metric = self.request.build_absolute_uri(likely_metric)
        return likely_metric

    def decorate_with_scores(self, rollup_tree, accounts=None, prefix=""):
        if accounts is None:
            accounts = self.requested_accounts

        for key, values in six.iteritems(rollup_tree[1]):
            self.decorate_with_scores(values, accounts=accounts, prefix=key)

        score = {}
        cohorts = []
        for account_id, account_score in six.iteritems(
                rollup_tree[0].get('accounts', {})):
            account = accounts.get(account_id, None)
            if account:
                n_score = account_score.get('normalized_score', 0)
                if n_score > 0:
                    score[account.slug] = n_score
                    parts = prefix.split('/')
                    default = parts[1] if len(parts) > 1 else None
                    cohorts += [{
                        'slug': account.slug,
                        'title': account.printable_name,
                        'likely_metric': self.get_likely_metric(
                            account.slug, default=default)}]
        rollup_tree[0]['values'] = score
        rollup_tree[0]['cohorts'] = cohorts

    def decorate_with_cohorts(self, rollup_tree, accounts=None, prefix=""):
        #pylint:disable=unused-argument
        if accounts is None:
            accounts = self.requested_accounts

        score = {}
        cohorts = []
        for path, values in six.iteritems(rollup_tree[1]):
            self.decorate_with_scores(values, accounts=accounts, prefix=path)
            nb_accounts = 0
            normalized_score = 0
            for account_id, account_score in six.iteritems(
                    values[0].get('accounts', {})):
                account = accounts.get(account_id, None)
                if account:
                    n_score = account_score.get('normalized_score', 0)
                    if n_score > 0:
                        nb_accounts += 1
                        normalized_score += n_score
            if normalized_score > 0 and nb_accounts > 0:
                score[path] = normalized_score / nb_accounts
                cohorts += [{
                    'slug': path,
                    'title': values[0]['title'],
                    'likely_metric': self.get_likely_metric(
                        values[0]['slug'] + '-1')}]
            values[0]['tag'] = [TransparentCut.TAG_SCORECARD]
        rollup_tree[0]['values'] = score
        rollup_tree[0]['cohorts'] = cohorts

    def get(self, request, *args, **kwargs):
        #pylint:disable=unused-argument,too-many-locals,too-many-statements
        self._start_time()
        segment_prefix = None
        path = self.kwargs.get('path')
        if path:
            last_part = path.split(self.URL_PATH_SEP)[-1]
            for seg in get_segments_candidates(self.campaign):
                if seg.get('path', "").endswith(last_part):
                    segment_prefix = seg.get('path')
                    break
        # calls rollup_scores from TotalScoreBySubsectorAPIView
        rollup_tree = self.rollup_scores(self.get_queryset())
        self._report_queries("rollup_scores completed")
        if segment_prefix:
            for node in six.itervalues(rollup_tree[1]):
                rollup_tree = node
                break
            self.decorate_with_scores(rollup_tree, prefix=segment_prefix)
            charts = self.get_charts(
                rollup_tree, excludes=[segment_prefix.split('/')[-1]])
            charts += [rollup_tree[0]]
        else:
            self.decorate_with_cohorts(rollup_tree)
            self._report_queries("decorate_with_cohorts completed")
            natural_charts = OrderedDict()
            for cohort in rollup_tree[0]['cohorts']:
                natural_chart = (rollup_tree[1][cohort['slug']][0], {})
                natural_charts.update({cohort['slug']: natural_chart})
            rollup_tree = (rollup_tree[0], natural_charts)
            charts = self.get_charts(rollup_tree)
            self._report_queries("get_charts completed")
            for chart in charts:
                element = PageElement.objects.filter(
                    slug=chart['slug']).first()
                chart.update({
                    'breadcrumbs': [chart['title']],
                    'picture': element.text if element is not None else "",
                    'icon_css': 'orange'
                })

        # XXX Shows average value in encompassing supply chain.
        if charts[0].get('slug') == 'totals':
            us_suppliers = charts[0].copy()
            us_suppliers['slug'] = "aggregates-%s" % us_suppliers['slug']
            us_suppliers['title'] = "US suppliers"
            score = {}
            for path, values in six.iteritems(rollup_tree[1]):
                nb_accounts = 0
                normalized_score = 0
                for account_id, account_score in six.iteritems(
                        values[0].get('accounts', {})):
                    if True: # XXX account_id in ``accounts from alliance``
                        n_score = account_score.get('normalized_score', 0)
                        if n_score > 0:
                            nb_accounts += 1
                            normalized_score += n_score
                if normalized_score > 0 and nb_accounts > 0:
                    if path in set([supplier['slug']
                            for supplier in us_suppliers['cohorts']]):
                        score[path] = normalized_score / nb_accounts
            us_suppliers['values'] = score
            charts += [us_suppliers]
            self._report_queries("aggregates completed")

        self.create_distributions(rollup_tree)
        self._report_queries("create_distributions completed")
        self.flatten_distributions(rollup_tree, prefix=segment_prefix)
        self._report_queries("flatten_distributions completed")

        for chart in charts:
            if 'accounts' in chart:
                del chart['accounts']

        return Response(charts)
