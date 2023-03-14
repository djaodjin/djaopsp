# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
#pylint:disable=too-many-lines

import datetime, json, re
from collections import OrderedDict

from dateutil.relativedelta import relativedelta, SU
from deployutils.crypt import JSONEncoder
from deployutils.helpers import datetime_or_now, parse_tz
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import F
import pytz
from rest_framework import generics
from rest_framework import response as http
from rest_framework.pagination import PageNumberPagination
from pages.models import PageElement
from survey.api.matrix import MatrixDetailAPIView
from survey.api.portfolios import PortfoliosRequestsAPIView
from survey.api.serializers import MetricsSerializer, TableSerializer, UnitSerializer
from survey.filters import SearchFilter, OrderingFilter
from survey.helpers import construct_yearly_periods, get_extra
from survey.queries import get_frozen_answers
from survey.mixins import DateRangeContextMixin
from survey.models import Answer, EditableFilter, PortfolioDoubleOptIn, Sample, UnitEquivalences
from survey.pagination import MetricsPagination
from survey.utils import get_account_model, get_question_model

from .campaigns import CampaignContentMixin
from .samples import attach_answers
from ..compat import reverse, six
from ..queries import get_completed_assessments_at_by
from ..mixins import AccountMixin
from ..models import ScorecardCache
from ..utils import (TransparentCut, get_alliances, get_reporting_accounts,
    get_requested_accounts, get_segments_candidates, segments_as_sql)
from .rollups import GraphMixin, RollupMixin, ScoresMixin
from .serializers import (AssessmentNodeSerializer,
    AssessmentContentSerializer, EngagementSerializer, ReportingSerializer)


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
                else ReportingSerializer.REPORTING_NOT_STARTED)
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
                'reporting_status', ReportingSerializer.REPORTING_NOT_STARTED)
            if reporting_status == ReportingSerializer.REPORTING_ABANDONED:
                self.abandoned += 1
            elif reporting_status == ReportingSerializer.REPORTING_EXPIRED:
                self.expired += 1
            elif (reporting_status
                  == ReportingSerializer.REPORTING_ASSESSMENT_PHASE):
                self.assessment_phase += 1
            elif reporting_status == ReportingSerializer.REPORTING_PLANNING_PHASE:
                self.improvement_phase += 1
            elif reporting_status == ReportingSerializer.REPORTING_COMPLETED:
                self.completed += 1
            else:
                self.no_assessment += 1
            if account.get('reporting_publicly'):
                self.reporting_publicly_count += 1

        return super(CompletionSummaryPagination, self).paginate_queryset(
            queryset, request, view=view)

    def get_paginated_response(self, data):
        return http.Response(OrderedDict([
            ('summary', (
                    ('Not started', self.no_assessment),
                    ('Abandoned', self.abandoned),
                    ('Expired', self.expired),
                    ('Assessment phase', self.assessment_phase),
                    ('Planning phase', self.improvement_phase),
                    ('Completed', self.completed),
            )),
            ('reporting_profiles_count', self.nb_organizations),
            ('reporting_publicly_count', self.reporting_publicly_count),
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class DashboardMixin(ScoresMixin, AccountMixin):
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

    @property
    def start_at(self):
        if not hasattr(self, '_start_at'):
            self._start_at = self.default_start_at
        return self._start_at

    @property
    def ends_at(self):
        """
        End of the period when reporting organization were suppossed to complete
        an assessment.
        """
        if not hasattr(self, '_ends_at'):
            param_ends_at = self.get_query_param('ends_at')
            if param_ends_at is not None:
                param_ends_at = param_ends_at.strip('"')
            # We assume specifying today is as good as `None` in this case.
            self._ends_at = datetime_or_now(param_ends_at)
        return self._ends_at

    @property
    def default_start_at(self):
        """
        Start of the period when reporting organization were invited.
        """
        # XXX `DashboardMixin` in views/portfolios.py has the same definition.
        if not hasattr(self, '_default_start_at'):
            self._default_start_at = get_extra(self.account, 'start_at', None)
            if self._default_start_at:
                self._default_start_at = datetime_or_now(self._default_start_at)
            param_start_at = self.get_query_param('start_at')
            if param_start_at is not None:
                param_start_at = param_start_at.strip('"')
                self._default_start_at = datetime_or_now(param_start_at)
            # In general `ends_at` could be `None`,
            # which would be a problem here.
            default_ends_at = datetime_or_now(self.ends_at)
            if (self._default_start_at and
                self._default_start_at >= default_ends_at):
                try:
                    # fixing period to 12 months if for any reason the start
                    # date is after the ends date.
                    self._default_start_at = (
                        default_ends_at - relativedelta(months=12))
                except ValueError:
                    # deal with a bogus ends_at date
                    self._default_start_at = default_ends_at
        return self._default_start_at

    @property
    def default_expired_at(self):
        """
        Date after which assessments should be updated.
        """
        # XXX `DashboardMixin` in views/portfolios.py has the same definition.
        if not hasattr(self, '_default_expired_at'):
            self._default_expired_at = get_extra(
                self.account, 'expired_at', None)
            if self._default_expired_at:
                self._default_expired_at = datetime_or_now(
                    self._default_expired_at)
            param_expired_at = self.get_query_param('expired_at')
            if param_expired_at is not None:
                param_expired_at = param_expired_at.strip('"')
                self._default_expired_at = datetime_or_now(param_expired_at)
            if (self._default_expired_at and
                self._default_expired_at >= self.default_start_at):
                self._default_expired_at = self.default_start_at
        return self._default_start_at

    @property
    def requested_accounts(self):
        if not hasattr(self, '_requested_accounts'):
            self._requested_accounts = self.get_requested_accounts(
            account=self.account)
        return self._requested_accounts

    @property
    def requested_accounts_pk_as_sql(self):
        if not hasattr(self, '_requested_accounts_pk_as_sql'):
            self._requested_accounts_pk_as_sql = ""
            pks = [str(account.pk) for account in self.requested_accounts]
            if pks:
                self._requested_accounts_pk_as_sql = "(%s)" % ','.join(pks)
        return self._requested_accounts_pk_as_sql


    def get_query_param(self, key):
        try:
            return self.request.query_params.get(key, None)
        except AttributeError:
            pass
        return self.request.GET.get(key, None)

    def get_reporting_accounts(self, account=None):
        """
        All accounts which have elected to share their scorecard
        with ``account``.
        """
        # called directly from `GHGEmissionsAmountMixin`
        # called transitively (get_reporting_scorecards) from `GoalsMixin`,
        #   `BySegmentsMixin`, `GHGEmissionsRateMixin`.
        if not account:
            account = self.account
        return get_reporting_accounts(account,
            start_at=self.start_at, ends_at=self.ends_at)

    def get_requested_accounts(self, account=None):
        """
        All accounts which ``account`` has requested a scorecard from.
        """
        if not account:
            account = self.account
        return get_requested_accounts(account, campaign=self.campaign,
            start_at=self.start_at, ends_at=self.ends_at)


class DashboardAggregateMixin(DashboardMixin):
    """
    Builds aggregated reporting
    """
    scale = 1
    serializer_class = MetricsSerializer
    default_unit = 'profiles'
    valid_units = ('percentage',)

    @property
    def unit(self):
        if not hasattr(self, '_unit'):
            self._unit = self.default_unit
            param_unit = self.get_query_param('unit')
            if param_unit is not None and param_unit in self.valid_units:
                self._unit = param_unit
        return self._unit

    @property
    def is_percentage(self):
        return self.unit == 'percentage'

    @property
    def segments(self):
        if not hasattr(self, '_segments'):
            self._segments = get_segments_candidates(self.campaign)
        return self._segments


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

        reporting_accounts = self.get_requested_accounts(account=account)
        if not reporting_accounts:
            return ScorecardCache.objects.none()

        accounts_clause = "AND account_id IN (%s)" % (
            ','.join([str(account.pk) for account in reporting_accounts]))

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
    'segments_query': segments_as_sql(self.segments),
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

    def get_labels(self, aggregate=None):
        if not aggregate:
            return None
        return [val[0] for val in aggregate]

    def get_response_data(self, request, *args, **kwargs):
        #pylint:disable=unused-argument
        alliances = get_alliances(self.account)
        account_aggregate = self.get_aggregate(
            self.account, labels=self.get_labels())
        table = [{
            'slug': self.account.slug,
            'printable_name': self.account.printable_name,
            'values': account_aggregate
        }]
        labels = self.get_labels(account_aggregate)
        for account in list(alliances):
            table += [{
                'slug': account.slug,
                'printable_name': account.printable_name,
                'values': self.get_aggregate(account, labels=labels)
            }]
        return {
            "title": self.title,
            'scale': self.scale,
            'unit': self.unit,
            'results': table
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
        accounts_by_pks = {account.pk: account
            for account in self.requested_accounts}
        for report_summary in queryset:
            account = accounts_by_pks[report_summary.account_id]
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

        GET /api/energy-utility/reporting/sustainability HTTP/1.1

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
    serializer_class = ReportingSerializer
    pagination_class = CompletionSummaryPagination

    def get(self, request, *args, **kwargs):
        self._start_time()
        resp = self.list(request, *args, **kwargs)
        self._report_queries("http response created")
        return resp


class TotalScoreBySubsectorAPIView(SupplierListMixin, RollupMixin, GraphMixin,
                                   MatrixDetailAPIView):
    """
    Retrieves a matrix of scores for cohorts against a metric

    Uses the total score for each organization as recorded
    by the assessment surveys and present aggregates
    by industry sub-sectors (Boxes & enclosures, etc.)

    **Tags**: reporting

    **Examples**

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/matrix/totals HTTP/1.1

    responds

    .. code-block:: json

          {
           "slug": "totals",
           "title": "Average scores by supplier industry sub-sector",
           "cohorts": [{
               "slug": "/portfolio-a",
               "title": "Portfolio A",
                "tags": null,
                "predicates": [],
               "likely_metric": "/app/energy-utility/portfolios/portfolio-a/"
           }]
          }
    """
    @property
    def db_path(self):
        if not hasattr(self, '_db_path'):
            self._db_path = ""
            prefix_candidate = self.kwargs.get(self.path_url_kwarg, '').replace(
                self.URL_PATH_SEP, self.DB_PATH_SEP)
            if prefix_candidate:
                # If the path is not a segment prefix, we just forget about it.
                last_part = prefix_candidate.split(self.URL_PATH_SEP)[-1]
                for seg in get_segments_candidates(self.campaign):
                    if seg.get('path', "").endswith(last_part):
                        self._db_path = seg.get('path')
                        break
            if self._db_path and not self._db_path.startswith(self.DB_PATH_SEP):
                self._db_path = self.DB_PATH_SEP + self._db_path
        return self._db_path

    def get_accounts(self):
        # overrides `MatrixDetailAPIView.get_accounts()`
        return self.get_reporting_accounts()

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

    def get_score_weight(self, path):
        if not hasattr(self, '_weights'):
            try:
                self._weights = json.loads(self.campaign.extra)
            except (TypeError, ValueError):
                self._weights = {}
        return self._weights.get(path, 1.0)


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
        accounts_by_pks = {account.pk: account for account in accounts}

        for key, values in six.iteritems(rollup_tree):
            self.decorate_with_scores(values[1], accounts=accounts, prefix=key)
            score = {}
            cohorts = []
            for account_id, account_score in six.iteritems(
                    values[0].get('accounts', {})):
                account = accounts_by_pks.get(account_id)
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
            values[0]['values'] = score
            values[0]['cohorts'] = cohorts

    def decorate_with_cohorts(self, rollup_tree, accounts=None, prefix=""):
        #pylint:disable=unused-argument,too-many-locals
        if accounts is None:
            accounts = self.requested_accounts
        accounts_by_pks = {account.pk: account for account in accounts}

        for path, values in six.iteritems(rollup_tree):
            self.decorate_with_scores(values[1], accounts=accounts, prefix=path)
            score = {}
            cohorts = []
            for node_path, node in six.iteritems(values[1]):
                nb_accounts = 0
                normalized_score = 0
                for account_id, account_score in six.iteritems(
                        node[0].get('accounts', {})):
                    account = accounts_by_pks.get(account_id, None)
                    if account:
                        n_score = account_score.get('normalized_score', 0)
                        if n_score > 0:
                            nb_accounts += 1
                            normalized_score += n_score
                if normalized_score > 0 and nb_accounts > 0:
                    score[node_path] = normalized_score / nb_accounts
                    cohorts += [{
                        'slug': node_path,
                        'title': node[0]['title'],
                        'likely_metric': self.get_likely_metric(
                            node[0]['slug'] + '-1')}]
                node[0]['tag'] = [TransparentCut.TAG_SCORECARD]
            values[0]['values'] = score
            values[0]['cohorts'] = cohorts


    def get(self, request, *args, **kwargs):
        #pylint:disable=unused-argument,too-many-locals,too-many-statements
        self._start_time()
        segment_prefix = self.db_path
        rollup_tree = self.rollup_scores(self.get_queryset())
        self._report_queries("rollup_scores completed")
        if segment_prefix:
            self.decorate_with_scores(rollup_tree, prefix=segment_prefix)
            charts = self.get_charts(rollup_tree)
        else:
            rollup_tree = {
                self.DB_PATH_SEP: ({
                    'slug': "totals",
                    'title': "Totals",
                    'extra': {'tags': [TransparentCut.TAG_SCORECARD]}
                }, rollup_tree)
            }
            self.decorate_with_cohorts(rollup_tree)
            self._report_queries("decorate_with_cohorts completed")
            natural_charts = OrderedDict()
            totals = rollup_tree.get(self.DB_PATH_SEP)
            for cohort in totals[0]['cohorts']:
                natural_chart = (totals[1][cohort['slug']][0], {})
                natural_charts.update({cohort['slug']: natural_chart})
            rollup_tree = {
                self.DB_PATH_SEP: (totals[0], natural_charts)}
            charts = self.get_charts(rollup_tree)
            self._report_queries("get_charts completed")
            for chart in charts:
                element = PageElement.objects.filter(
                    slug=chart['slug']).first()
                chart.update({
                    'breadcrumbs': [chart['title']],
                    'picture': element.picture if element is not None else None,
                })

        self.create_distributions(rollup_tree)
        self._report_queries("create_distributions completed")
        self.flatten_distributions(rollup_tree, prefix=segment_prefix)
        self._report_queries("flatten_distributions completed")

        for chart in charts:
            if 'accounts' in chart:
                del chart['accounts']

        return http.Response(charts)


class CompletedAssessmentsMixin(AccountMixin):

    def get_queryset(self):
        queryset = Sample.objects.filter(
            pk__in=[sample.pk
                for sample in Sample.objects.get_latest_frozen_by_accounts(
            tags=[])]).order_by(
            '-created_at').annotate(
                last_completed_at=F('created_at'),
                account_slug=F('account__slug'),
                printable_name=F('account__full_name'),
                email=F('account__email'),
                segment=F('campaign__title'))
        return queryset


class CompletedAssessmentsAPIView(CompletedAssessmentsMixin,
                                  generics.ListAPIView):
    """
    Lists all completed assessments

    List completed assessments available on the platform.

    **Tags**: reporting

    **Examples

    .. code-block:: http

        GET /api/djaopsp/completed HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 1,
          "next": null,
          "previous": null,
          "results":[
          {
            "last_completed_at": "2022-11-28",
            "printable_name": "Supplier 1",
            "segment": "ESG/Environmental practices"
          },
          {
            "last_completed_at": "2022-11-27",
            "printable_name": "Supplier 2",
            "segment": "ESG/Environmental practices"
          }
          ]
        }
    """
    serializer_class = ReportingSerializer
    schema = None

    def decorate_queryset(self, queryset):
        for sample in queryset:
            sample.score_url = reverse('scorecard',
                args=(self.account, sample.slug))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            self.decorate_queryset(page)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        self.decorate_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



# We should use DashboardMixin instead of DateRangeContextMixin
# but there are MRO class order issue between CampaignMixin and AccountMixin
# when we do that.
class CompareAPIView(DateRangeContextMixin, CampaignContentMixin,
                     generics.ListAPIView):
    """
    Lists compared samples

    **Examples**:

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/compare/sustainability\
 HTTP/1.1

    responds

    .. code-block:: json


        {
          "count": 4,
          "results": [
            {
              "count": 1,
              "slug": "sustainability",
              "path": "/sustainability",
              "indent": 0,
              "title": "Core Environment, Social and Governance (ESG) Assessment",
              "picture": null,
              "extra": {
                "pagebreak": true,
                "tags": [
                  "scorecard"
                ],
                "visibility": [
                  "public"
                ],
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": null,
              "environmental_value": null,
              "business_value": null,
              "profitability": null,
              "implementation_ease": null,
              "rank": -1,
              "required": false,
              "default_unit": null,
              "ui_hint": null,
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            },
            {
              "count": 1,
              "slug": "governance",
              "path": "/sustainability/governance",
              "indent": 1,
              "title": "Strategy & Governance",
              "picture": "/tspproject/static/img/management-basics.png",
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
              "count": 1,
              "avg_value": null,
              "environmental_value": null,
              "business_value": null,
              "profitability": null,
              "implementation_ease": null,
              "rank": 1,
              "required": false,
              "default_unit": null,
              "ui_hint": null,
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            },
            {
              "count": 1,
              "slug": "esg-strategy-heading",
              "path": "/sustainability/governance/esg-strategy-heading",
              "indent": 2,
              "title": "Environment, Social & Governance (ESG) Strategy",
              "picture": null,
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": null,
              "environmental_value": null,
              "business_value": null,
              "profitability": null,
              "implementation_ease": null,
              "rank": 1,
              "required": false,
              "default_unit": null,
              "ui_hint": null,
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            },
            {
              "count": 1,
              "slug": "formalized-esg-strategy",
              "path": "/sustainability/governance/esg-strategy-heading/formalized-esg-strategy",
              "indent": 3,
              "title": "(3) Does your company have a formalized ESG strategy and performance targets that: 1/ Define a future vision of ESG performance, 2/ Are clear, actionable, and achievable, 3/ Are resourced effectively, 4/ Address material issues for the business?",
              "picture": "/tspproject/static/img/management-basics.png",
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": 0,
              "environmental_value": 1,
              "business_value": 1,
              "profitability": 1,
              "implementation_ease": 1,
              "rank": 4,
              "required": true,
              "default_unit": {
                "slug": "yes-no",
                "title": "Yes/No",
                "system": "enum",
                "choices": [
                  {
                    "text": "Yes",
                    "descr": "Yes"
                  },
                  {
                    "text": "No",
                    "descr": "No"
                  }
                ]
              },
              "ui_hint": "yes-no-comments",
              "answers": [{
                "measured": true
              }, {
                "measured": false
              }],
              "candidates": [],
              "planned": [],
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            }
          ]
        }
    """
    title = "Compare"
    scale = 1
    unit = None
#XXX    pagination_class = MetricsPagination - hardcoded in serializer
    serializer_class = AssessmentContentSerializer

    @property
    def samples(self):
        """
        Samples to compare

        One per column
        """
        if not hasattr(self, '_samples'):
            reporting_accounts = get_reporting_accounts(
                self.account, campaign=self.campaign)
            # XXX currently start_at and ends_at have shaky definition in
            #     this context.
            if reporting_accounts:
                # Calling `get_completed_assessments_at_by` with an `accounts`
                # arguments evaluating to `False` will return all the latest
                # frozen samples.
                self._samples = get_completed_assessments_at_by(self.campaign,
                    start_at=self.start_at, ends_at=self.ends_at,
                    accounts=reporting_accounts)
            else:
                self._samples = Sample.objects.none()
        return self._samples

    @property
    def labels(self):
        """
        Labels for columns
        """
        if not hasattr(self, '_labels'):
            self._labels = sorted([
                sample.account.printable_name for sample in self.samples])
        return self._labels

    @staticmethod
    def next_answer(answers_iterator, questions_by_key, extra_fields):
        answer = next(answers_iterator)
        question_pk = answer.question_id
        value = questions_by_key.get(question_pk)
        if not value:
            question = answer.question
            default_unit = question.default_unit
            value = {
                'path': question.path,
                'rank': answer.rank,
                'required': answer.required,
                'default_unit': default_unit,
                'ui_hint': question.ui_hint,
            }
            for field_name in extra_fields:
                value.update({field_name: getattr(question, field_name)})
            questions_by_key.update({question_pk: value})
        else:
            default_unit = value.get('default_unit')

        if( answer.unit == default_unit or
            UnitEquivalences.objects.filter(
                source=default_unit, target=answer.unit).exists() or
            UnitEquivalences.objects.filter(
                source=answer.unit, target=default_unit).exists() ):
            # we have the answer we are looking for.
            nb_respondents = value.get('nb_respondents', 0) + 1
            value.update({'nb_respondents': nb_respondents})
        return answer

    def as_answer(self, key):
        return key

    @staticmethod
    def equiv_default_unit(values):
        results = []
        for val in values:
            found = False
            for resp in val:
                try:
                    if resp.is_equiv_default_unit:
                        found = {
                            'measured': resp.measured_text,
                            'unit': resp.unit,
                            'created_at': resp.created_at,
                            'collected_by': resp.collected_by,
                        }
                        break
                except AttributeError:
                    pass
            results += [found]
        return results

    def attach_results(self, units, questions_by_key, answers,
                       extra_fields=None):
        if extra_fields is None:
            extra_fields = []

        question = None
        values = []
        key = None
        answer = None
        keys_iterator = iter(self.labels)
        answers_iterator = iter(answers)
        try:
            answer = self.next_answer(answers_iterator,
                questions_by_key, extra_fields=extra_fields)
            question = answer.question
        except StopIteration:
            pass
        try:
            key = self.as_answer(next(keys_iterator))
        except StopIteration:
            pass
        # `answers` will be populated even when there is no `Answer` model
        # just so we can get the list of questions.
        # On the other hand self.labels will be an empty list if there are
        # no samples to compare.
        try:
            while answer:
                if answer.question != question:
                    try:
                        while key:
                            values += [[{}]]
                            key = self.as_answer(next(keys_iterator))
                    except StopIteration:
                        keys_iterator = iter(self.labels)
                        try:
                            key = self.as_answer(next(keys_iterator))
                        except StopIteration:
                            key = None
                    questions_by_key[question.pk].update({
                        'answers': self.equiv_default_unit(values)})
                    values = []
                    question = answer.question

                if key and answer.sample.account.printable_name > key:
                    while answer.sample.account.printable_name > key:
                        values += [[{}]]
                        key = self.as_answer(next(keys_iterator))
                elif key and answer.sample.account.printable_name < key:
                    try:
                        try:
                            sample = values[-1][0].sample
                        except AttributeError:
                            sample = values[-1][0].get('sample')
                        if answer.sample != sample:
                            values += [[answer]]
                        else:
                            values[-1] += [answer]
                    except IndexError:
                        values += [[answer]]
                    try:
                        answer = self.next_answer(answers_iterator,
                            questions_by_key, extra_fields=extra_fields)
                    except StopIteration:
                        answer = None
                else:
                    try:
                        try:
                            sample = values[-1][0].sample
                        except AttributeError:
                            sample = values[-1][0].get('sample')
                        if answer.sample != sample:
                            values += [[answer]]
                        else:
                            values[-1] += [answer]
                    except IndexError:
                        values += [[answer]]
                    try:
                        answer = self.next_answer(answers_iterator,
                            questions_by_key, extra_fields=extra_fields)
                    except StopIteration:
                        answer = None
                    try:
                        key = self.as_answer(next(keys_iterator))
                    except StopIteration:
                        key = None
            while key:
                values += [[{}]]
                key = self.as_answer(next(keys_iterator))
        except StopIteration:
            pass
        if question:
            questions_by_key[question.pk].update({
                'answers': self.equiv_default_unit(values)})


    def get_questions(self, prefix):
        """
        Overrides CampaignContentMixin.get_questions to return a list
        of questions based on the answers available in the compared samples.
        """
        if prefix != '/sustainability':
            # XXX testing
            return []

        if not hasattr(self, 'units'):
            self.units = {}
        if not prefix.endswith(self.DB_PATH_SEP):
            prefix = prefix + self.DB_PATH_SEP

        units = {}
        questions_by_key = {}
        if self.samples:
            self.attach_results(
                units,
                questions_by_key,
                get_frozen_answers(self.campaign, self.samples, prefix=prefix))

        return list(six.itervalues(questions_by_key))


    def get_serializer_context(self):
        context = super(CompareAPIView, self).get_serializer_context()
        context.update({
            'prefix': self.db_path if self.db_path else self.DB_PATH_SEP,
        })
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Ready to serialize
        serializer = AssessmentNodeSerializer(
            queryset, many=True, context=self.get_serializer_context())
        if not hasattr(self, 'units'):
            self.units = {}
        return http.Response(self.get_serializer_class()(
            context=self.get_serializer_context()).to_representation({
                'count': len(serializer.data),
                'labels': self.labels,
                'units': {key: UnitSerializer().to_representation(val)
                    for key, val in six.iteritems(self.units)},
                'results': serializer.data,
            }))


class CompareIndexAPIView(CompareAPIView):
    """
    Lists compared samples

    **Examples**:

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/compare HTTP/1.1

    responds

    .. code-block:: json


        {
          "count": 4,
          "results": [
            {
              "count": 1,
              "slug": "sustainability",
              "path": "/sustainability",
              "indent": 0,
              "title": "Core Environment, Social and Governance (ESG) Assessment",
              "picture": null,
              "extra": {
                "pagebreak": true,
                "tags": [
                  "scorecard"
                ],
                "visibility": [
                  "public"
                ],
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": null,
              "environmental_value": null,
              "business_value": null,
              "profitability": null,
              "implementation_ease": null,
              "rank": -1,
              "required": false,
              "default_unit": null,
              "ui_hint": null,
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            },
            {
              "count": 1,
              "slug": "governance",
              "path": "/sustainability/governance",
              "indent": 1,
              "title": "Strategy & Governance",
              "picture": "/tspproject/static/img/management-basics.png",
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
              "count": 1,
              "avg_value": null,
              "environmental_value": null,
              "business_value": null,
              "profitability": null,
              "implementation_ease": null,
              "rank": 1,
              "required": false,
              "default_unit": null,
              "ui_hint": null,
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            },
            {
              "count": 1,
              "slug": "esg-strategy-heading",
              "path": "/sustainability/governance/esg-strategy-heading",
              "indent": 2,
              "title": "Environment, Social & Governance (ESG) Strategy",
              "picture": null,
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": null,
              "environmental_value": null,
              "business_value": null,
              "profitability": null,
              "implementation_ease": null,
              "rank": 1,
              "required": false,
              "default_unit": null,
              "ui_hint": null,
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            },
            {
              "count": 1,
              "slug": "formalized-esg-strategy",
              "path": "/sustainability/governance/esg-strategy-heading/formalized-esg-strategy",
              "indent": 3,
              "title": "(3) Does your company have a formalized ESG strategy and performance targets that: 1/ Define a future vision of ESG performance, 2/ Are clear, actionable, and achievable, 3/ Are resourced effectively, 4/ Address material issues for the business?",
              "picture": "/tspproject/static/img/management-basics.png",
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": 0,
              "environmental_value": 1,
              "business_value": 1,
              "profitability": 1,
              "implementation_ease": 1,
              "rank": 4,
              "required": true,
              "default_unit": {
                "slug": "yes-no",
                "title": "Yes/No",
                "system": "enum",
                "choices": [
                  {
                    "text": "Yes",
                    "descr": "Yes"
                  },
                  {
                    "text": "No",
                    "descr": "No"
                  }
                ]
              },
              "ui_hint": "yes-no-comments",
              "answers": [{
                "measured": true
              }, {
                "measured": false
              }],
              "candidates": [],
              "planned": [],
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            }
          ]
        }
    """


class PortfolioAccessibleSamplesMixin(DashboardMixin):

    search_fields = (
        'slug',
        'full_name',
        'email',
    )
    ordering_fields = (
        ('created_at', 'created_at'),
        ('full_name', 'full_name'),
    )

    ordering = ('full_name',)

    filter_backends = (SearchFilter, OrderingFilter)

    def get_latest_frozen_by_accounts_by_year(self, campaign, includes,
        start_at=None, ends_at=None):
        """
        Returns the most recent frozen assessment for each year between
        starts_at and ends_at for each account.
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
    survey_sample.account_id AS account_id,
    survey_sample.id AS id,
    survey_sample.created_at AS created_at
FROM survey_sample
INNER JOIN (
    SELECT
        account_id,
        date_trunc('year', survey_sample.created_at) AS year,
        MAX(survey_sample.created_at) AS last_updated_at
    FROM survey_sample
    INNER JOIN accounts ON
        survey_sample.account_id = accounts.id
    WHERE survey_sample.campaign_id = %(campaign_id)d AND
          survey_sample.is_frozen AND
          survey_sample.extra IS NULL
          %(date_range_clause)s
    GROUP BY account_id, year) AS last_updates ON
   survey_sample.account_id = last_updates.account_id AND
   survey_sample.created_at = last_updates.last_updated_at
INNER JOIN accounts ON
   survey_sample.account_id = accounts.id
WHERE
   survey_sample.is_frozen AND
   survey_sample.extra IS NULL
ORDER BY account_id, created_at
""" % {'campaign_id': campaign.pk,
       'accounts_query': accounts_query,
       'date_range_clause': date_range_clause}
        return Sample.objects.raw(sql_query)

    def get_queryset(self):
        return self.requested_accounts

    def as_sample(self, key):
        return (key, 'no-data', None, None)

    def decorate_queryset(self, page):
        samples_by_account_ids = {}
        samples = self.get_latest_frozen_by_accounts_by_year(
            self.campaign, page)

        latest_sample = None
        earliest_sample = None
        for sample in samples:
            if sample.account_id not in samples_by_account_ids:
                samples_by_account_ids[sample.account_id] = []
            samples_by_account_ids[sample.account_id] += [
                (sample.created_at, 'completed',
                 self.request.build_absolute_uri(reverse('scorecard',
                    args=(self.account, sample.slug))), 0)]
            if latest_sample is None or latest_sample < sample.created_at:
                latest_sample = sample.created_at
            if earliest_sample is None or earliest_sample > sample.created_at:
                earliest_sample = sample.created_at
        first_year = datetime.datetime(
            year=datetime_or_now(earliest_sample).year, month=1, day=1)
        last_year = datetime.datetime(
            year=datetime_or_now(latest_sample).year, month=12, day=31)
        years = construct_yearly_periods(first_year, last_year)
        self.labels = [val.year for val in years]

        for account in page:
            values = []
            key = None
            sample = None
            keys_iterator = iter(years)
            samples_iterator = iter(samples_by_account_ids.get(account.pk, []))
            try:
                sample = next(samples_iterator)
            except StopIteration:
                pass
            try:
                key = self.as_sample(next(keys_iterator))
            except StopIteration:
                pass
            try:
                while sample and key:
                    if sample[0].year < key[0].year:
                        values += [sample]
                        sample = None
                        sample = next(samples_iterator)
                    elif key[0].year < sample[0].year:
                        values += [key]
                        key = None
                        key = self.as_sample(next(keys_iterator))
                    else:
                        values += [sample]
                        try:
                            sample = next(samples_iterator)
                        except StopIteration:
                            sample = None
                        try:
                            key = self.as_sample(next(keys_iterator))
                        except StopIteration:
                            key = None
            except StopIteration:
                pass
            try:
                while sample:
                    values += [sample]
                    sample = next(samples_iterator)
            except StopIteration:
                pass
            try:
                while key:
                    values += [key]
                    key = self.as_sample(next(keys_iterator))
            except StopIteration:
                pass
            account.values = values

        return page

    def paginate_queryset(self, queryset):
        page = super(
            PortfolioAccessibleSamplesMixin, self).paginate_queryset(queryset)
        return self.decorate_queryset(page if page else queryset)


class PortfolioAccessibleSamplesAPIView(PortfolioAccessibleSamplesMixin,
                                        generics.ListAPIView):
    """
    List year-by-year accessible responses for reporting profiles

    **Tags**: reporting

    **Examples

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/accessibles HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 1,
          "next": null,
          "previous": null,
          "results": [
                {
                    "slug": "andy-shop",
                    "printable_name": "Andy's Shop",
                    "values": [
                        ["2023-01-01T00:00:00Z", "complete", 95],
                        ["2022-01-01T00:00:00Z", "complete", 95],
                        ["2021-01-01T00:00:00Z", "invited", null],
                        ["2020-01-01T00:00:00Z", "not-invited", null],
                        ["2019-01-01T00:00:00Z", "not-invited", null],
                        ["2018-01-01T00:00:00Z", "not-invited", null]
                    ]
                },
                {
                    "slug": "supplier-1",
                    "printable_name": "Supplier 1",
                    "values": [
                        ["2023-01-01T00:00:00Z", "complete", 82],
                        ["2022-01-01T00:00:00Z", "complete", 82],
                        ["2021-01-01T00:00:00Z", "invited", null],
                        ["2020-01-01T00:00:00Z", "not-invited", null],
                        ["2019-01-01T00:00:00Z", "not-invited", null],
                        ["2018-01-01T00:00:00Z", "not-invited", null]
                    ]
                }
          ]
        }
    """
    title = "Accessibles"
    scale = 1
    unit = None
    serializer_class = TableSerializer
    pagination_class = MetricsPagination

    def get(self, request, *args, **kwargs):
        self._start_time()
        resp = self.list(request, *args, **kwargs)
        self._report_queries("http response created")
        return resp



class PortfolioEngagementMixin(DashboardMixin):
    """
    """
    search_fields = (
        'slug',
        'full_name',
        'email',
    )
    ordering_fields = (
        ('created_at', 'created_at'),
        ('full_name', 'full_name'),
        ('reporting_status', 'reporting_status'),
        ('last_activity_at', 'last_activity_at'),
        ('requested_at', 'requested_at'),
    )

    ordering = ('full_name',)

    filter_backends = (SearchFilter, OrderingFilter)

    @property
    def segments(self):
        if not hasattr(self, '_segments'):
            self._segments = get_segments_candidates(self.campaign)
        return self._segments

    def decorate_queryset(self, queryset):
        engagement = {val.account_id: val for val
            in self.get_engagement(queryset)}
        scores = ScorecardCache.objects.filter(sample__in={
            val.sample_id for val in engagement.values()}, path__in=[
            seg['path'] for seg in self.segments]).order_by('path')
        scores = {val.sample_id: val for val in scores}
        for account in queryset:
            engage = engagement.get(account.pk)
            if engage:
                account.grantee = engage.grantee
                account.account = engage.account
                account.campaign = engage.campaign
                account.state = engage.state
                account.verification_key = engage.verification_key
                account.extra = engage.extra

                account.sample = engage.sample
                account.reporting_status = engage.reporting_status
                account.last_activity_at = engage.last_activity_at
                #account.requested_at = engage.requested_at
                scorecard_cache = scores.get(engage.sample_id)
                if scorecard_cache:
                    account.normalized_score = scorecard_cache.normalized_score
        return queryset

    def get_queryset(self):
        return self.requested_accounts

    def get_engagement(self, accounts):
        sep = ""
        accounts_clause = ""
        if False:
            search = SearchFilter()
            terms = search.get_search_terms(self.request)
            for search_field in self.search_fields:
                search_field = search_field[len('account__'):]
                for term in terms:
                    accounts_clause += \
                        "%(sep)s%(search_field)s ILIKE '%%%%%(term)s%%%%'" % {
                        'sep': sep,
                        'search_field': search_field,
                        'term': term
                    }
                    sep = "OR "
            if accounts_clause:
                accounts_clause = "AND account_id IN (SELECT id FROM %s WHERE %s)" % (
                    get_account_model()._meta.db_table, accounts_clause)

        if accounts:
            accounts_clause = "AND account_id IN (%s)" % ",".join([
                str(account.pk) for account in accounts])


        campaign_clause = "AND survey_portfoliodoubleoptin.campaign_id = %d" % self.campaign.pk
        after_clause = ""
        if self.start_at:
            after_clause = "AND survey_portfoliodoubleoptin.created_at >= '%s'" % self.start_at
        before_clause = ""
        if self.ends_at:
            before_clause = "AND survey_portfoliodoubleoptin.created_at < '%s'" % self.ends_at
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
      survey_portfoliodoubleoptin.grantee_id IN (%(grantees)s) AND
      survey_portfoliodoubleoptin.state IN (
        %(optin_request_initiated)d,
        %(optin_request_accepted)d,
        %(optin_request_denied)d,
        %(optin_request_expired)d)
      %(campaign_clause)s
      %(after_clause)s
      %(before_clause)s
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
      %(after_clause)s
      %(before_clause)s
),
completed_by_accounts AS (
SELECT
  survey_sample.*,
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
    survey_sample.extra IS NULL AND
    survey_sample.created_at < '%(ends_at)s'
  GROUP BY survey_sample.account_id, survey_sample.is_frozen, requests.state
) AS latest_completion
ON survey_sample.account_id = latest_completion.account_id AND
   survey_sample.created_at = latest_completion.last_updated_at AND
   survey_sample.is_frozen = latest_completion.is_frozen
),
updated_by_accounts AS (
SELECT
  survey_sample.*,
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
    survey_sample.extra IS NULL AND
    survey_sample.updated_at < '%(ends_at)s'
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
    'grantees': self.account.pk,
    'campaign_clause': campaign_clause,
    'before_clause': before_clause,
    'after_clause': after_clause,
    'accounts_clause': accounts_clause,
    'ends_at': self.ends_at,
    'optin_request_initiated': PortfolioDoubleOptIn.OPTIN_REQUEST_INITIATED,
    'optin_request_accepted': PortfolioDoubleOptIn.OPTIN_REQUEST_ACCEPTED,
    'optin_request_expired': PortfolioDoubleOptIn.OPTIN_REQUEST_EXPIRED,
    'optin_request_denied': PortfolioDoubleOptIn.OPTIN_REQUEST_DENIED
}
        return PortfolioDoubleOptIn.objects.raw(sql_query)

    def paginate_queryset(self, queryset):
        page = super(
            PortfolioEngagementMixin, self).paginate_queryset(queryset)
        return self.decorate_queryset(page if page else queryset)


class PortfolioEngagementAPIView(PortfolioEngagementMixin,
                                 generics.ListAPIView): #XXXPortfoliosRequestsAPIView):
    """
    List engagement for reporting profiles


    reporting_status can be one of:
      - invited
      - updated / work-in-progress
      - completed
      - declined (to respond)
      - completed declined to share

    **Tags**: reporting

    **Examples

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/engagement HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 1,
          "next": null,
          "previous": null,
          "results": [
              {
                "grantee": "energy-utility",
                "account": "supplier-1",
                "campaign": "sustainability",
                "created_at": "2022-01-01T00:00:00Z",
                "ends_at": "2023-01-01T00:00:00Z",
                "state": "request-denied",
                "api_accept": null,
                "reporting_status": "completed",
                "last_activity_at": "2022-11-01T00:00:00Z",
                "requested_at": "2022-01-01T00:00:00Z"
              },
              {
                "grantee": "energy-utility",
                "account": "andy-shop",
                "campaign": "sustainability",
                "created_at": "2022-01-01T00:00:00Z",
                "ends_at": "2023-01-01T00:00:00Z",
                "state": "request-accepted",
                "api_accept": null,
                "reporting_status": "completed",
                "last_activity_at": "2022-11-01T00:00:00Z",
                "requested_at": "2022-01-01T00:00:00Z"
              }
          ]
        }
    """
    serializer_class = EngagementSerializer

    def get(self, request, *args, **kwargs):
        self._start_time()
        resp = self.list(request, *args, **kwargs)
        self._report_queries("http response created")
        return resp

    def get_serializer_context(self):
        context = super(
            PortfolioEngagementAPIView, self).get_serializer_context()
        context.update({'account': self.account})
        return context

    def post(self, request, *args, **kwargs):
        """
        Initiates a request

        Initiate a request of data for an account.

        **Tags**: portfolios

        **Examples**

        .. code-block:: http

            POST /api/energy-utility/reporting/sustainability/engagement HTTP/1.1

        .. code-block:: json

            {
               "accounts": [
                 {
                   "slug": "supplier-1",
                   "full_name": "Supplier 1"
                 }
               ]
            }

        responds

        .. code-block:: json

            {
               "accounts": [
                 {
                   "slug": "supplier-1",
                   "full_name": "Supplier 1"
                 }
               ]
             }
        """
        return self.create(request, *args, **kwargs)
