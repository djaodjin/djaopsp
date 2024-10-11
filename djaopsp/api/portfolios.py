# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.
#pylint:disable=too-many-lines

import datetime, json, logging, re
from collections import OrderedDict

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import F, Q, Max, Min
from django.template.defaultfilters import slugify
from rest_framework import generics, status
from rest_framework import response as http
from rest_framework.settings import api_settings
from pages.docs import extend_schema
from pages.models import PageElement
from survey.api.matrix import (CompareAPIView as CompareAPIBaseView,
    MatrixDetailAPIView)
from survey.api.serializers import MetricsSerializer, SampleBenchmarksSerializer
from survey.filters import DateRangeFilter, OrderingFilter, SearchFilter
from survey.helpers import (construct_monthly_periods,
    construct_yearly_periods, construct_weekly_periods, datetime_or_now,
    extra_as_internal, period_less_than)
from survey.pagination import MetricsPagination
from survey.api.matrix import (BenchmarkMixin as BenchmarkMixinBase,
    EngagedAccountsMixin, EngagedBenchmarkAPIView)
from survey.mixins import TimersMixin
from survey.models import (EditableFilter, Portfolio,
    PortfolioDoubleOptIn, Sample)
from survey.settings import URL_PATH_SEP, DB_PATH_SEP
from survey.utils import (get_accessible_accounts, get_account_model,
    get_engaged_accounts, get_benchmarks_enumerated)

from .campaigns import CampaignDecorateMixin
from .. import humanize
from ..compat import gettext_lazy as _, reverse, six
from ..helpers import as_percentage
from ..queries import (get_latest_frozen_by_portfolio_by_period, get_engagement,
    get_engagement_by_reporting_status, get_requested_by_accounts_by_period,
    segments_as_sql)
from ..mixins import (AccountMixin, AccountsDateRangeMixin,
    AccountsAggregatedQuerysetMixin, AccountsNominativeQuerysetMixin)
from ..models import ScorecardCache, VerifiedSample
from ..pagination import AccessiblesPagination
from ..utils import (TransparentCut, get_alliances, get_latest_reminders,
    get_segments_candidates)
from .rollups import GraphMixin, RollupMixin, ScoresMixin
from .serializers import (AccessiblesSerializer, CompareNodeSerializer,
    EngagementSerializer, ReportingSerializer)


LOGGER = logging.getLogger(__name__)


class DashboardAggregateMixin(AccountsAggregatedQuerysetMixin):
    """
    Builds aggregated reporting
    """
    scale = 1
    serializer_class = MetricsSerializer
    title = ""

    def get_reporting_scorecards(self, account=None, start_at=None,
                                 ends_at=None, aggregate_set=False):
        filter_params = {}
        if start_at:
            filter_params.update({
                'sample__created_at__gte': datetime_or_now(start_at)})
        if not ends_at:
            ends_at = self.ends_at
        filter_params.update({
            'sample__created_at__lt': datetime_or_now(ends_at)})

        reporting_accounts = self.get_engaged_accounts(
            account, aggregate_set=aggregate_set)
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
    'segments_query': segments_as_sql(self.segments_available),
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
        account_aggregate = self.get_aggregate(
            self.account, labels=self.get_labels())
        table = [{
            'slug': self.account.slug,
            'title': self.account.printable_name,
            'values': account_aggregate
        }]
        labels = self.get_labels(account_aggregate)
        for account in list(get_alliances(self.account)):
            table += [{
                'slug': account.slug,
                'title': account.printable_name,
                'values': self.get_aggregate(
                    account, labels=labels, aggregate_set=True)
            }]
        return {
            "title": self.title,
            'scale': self.scale,
            'unit': self.unit,
            'results': table
        }


class BenchmarkMixin(TimersMixin, AccountsDateRangeMixin,
                     EngagedAccountsMixin, BenchmarkMixinBase):

    def _attach_results(self, questions_by_key, accessible_accounts,
                        title, slug):
        samples = []
        if accessible_accounts:
            # Calling `get_completed_assessments_at_by` with an `accounts`
            # arguments evaluating to `False` will return all the latest
            # frozen samples.
            samples = Sample.objects.get_completed_assessments_at_by(
                self.campaign, accounts=accessible_accounts,
                start_at=self.start_at, ends_at=self.ends_at)

        # samples that will be counted in the benchmark
        if samples:
            questions_by_key = get_benchmarks_enumerated(
                samples, questions_by_key.keys(), questions_by_key)
            for question in six.itervalues(questions_by_key):
                if not 'benchmarks' in question:
                    question['benchmarks'] = []
                account_benchmark = {
                    'slug': slug,
                    'title': title,
                    'values': []
                }
                dkey = 'rate' if self.unit == 'percentage' else 'counts'
                for key, val in six.iteritems(question.get(dkey, {})):
                    account_benchmark['values'] += [(key, int(val))]
                question['benchmarks'] += [account_benchmark]
        else:
            # We need a 'benchamrks' key, otherwise the serializer
            # will raise a `KeyError` exception leading to a 500 error.
            for question in six.itervalues(questions_by_key):
                if not 'benchmarks' in question:
                    question['benchmarks'] = []


    def get_questions_by_key(self, prefix=None, initial=None):
        questions_by_key = super(BenchmarkMixin, self).get_questions_by_key(
            prefix=prefix, initial=initial)

        account = self.account
        self._report_queries(
            "BenchmarkMixin._attach_results(account=%s)" % str(account))

        alliances = get_alliances(account)
        for alliance in list(alliances):
            accessible_accounts = get_engaged_accounts([alliance],
                campaign=self.campaign,
                start_at=self.accounts_start_at, ends_at=self.accounts_ends_at,
                aggregate_set=True)
            self._attach_results(questions_by_key, accessible_accounts,
                alliance.printable_name, alliance.slug)
            self._report_queries(
                "BenchmarkMixin._attach_results(account=%s)" % str(alliance))

        return questions_by_key


class BenchmarkAPIView(BenchmarkMixin, EngagedBenchmarkAPIView):
    """
    XXX deprecated API - Aggregated benchmark for requested accounts

    **Examples**:

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/benchmarks\
/sustainability/governance/environmental-reporting/environmental-fines HTTP/1.1

    responds

    .. code-block:: json


        {
          "count": 1,
          "scale": 1,
          "title": "Benchmarks",
          "unit": "percentage",
          "results": [
            {
              "path": "/sustainability/governance/environmental-reporting\
/environmental-fines",
              "title": "5.1 Has your company received or been responsible\
 for a Notice of Violation (NOV), Consent Order or fine over USD $10,000 from\
 an environmental agency, or an environmental event that required reporting\
 to an environmental agency in the past 36 months?",
              "default_unit": {
                  "slug": "yes-no",
                  "title": "Yes/No",
                  "system": "enum",
                  "choices": []
              },
              "ui_hint": "radio",
              "benchmarks": [
                {
                  "slug": "energy-utility",
                  "title": "Energy Utility (Demo)",
                  "values": [
                      [ "No", 80],
                      [ "Yes", 20]
                  ]
                },
                {
                  "slug": "alliance",
                  "title": "Alliance",
                  "values": [
                      [  "No", 95],
                      [ "Yes", 5]
                  ]
                }
              ]
            }
          ]
        }
    """
    serializer_class = SampleBenchmarksSerializer
    pagination_class = MetricsPagination

    def get_title(self):
        return self.account.printable_name

    def get_serializer_context(self):
        context = super(BenchmarkAPIView, self).get_serializer_context()
        context.update({
            'prefix': self.db_path if self.db_path else DB_PATH_SEP,
        })
        return context


    def get(self, request, *args, **kwargs):
        self._start_time()
        resp = super(BenchmarkAPIView, self).get(request, *args, **kwargs)
        self._report_queries("[BenchmarkAPIView.get] completed HTTP request")
        return resp


class BenchmarkIndexAPIView(BenchmarkAPIView):
    """
    Aggregated benchmark for requested accounts

    **Examples**:

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/benchmarks HTTP/1.1

    responds

    .. code-block:: json


        {
          "count": 4,
          "results": []
        }
    """

    @extend_schema(operation_id='reporting_benchmarks_index')
    def get(self, request, *args, **kwargs):
        return super(BenchmarkIndexAPIView, self).get(
            request, *args, **kwargs)


class SupplierListMixin(ScoresMixin, AccountsNominativeQuerysetMixin):
    """
    Scores for all reporting entities in a format that can be used by the API
    and spreadsheet downloads.

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
            report_summary.requested_at = None
            # There is something fundamentally incorrect with the logic
            # if `report_summary.account_id` is not in the requested accounts.
            account = accounts_by_pks[report_summary.account_id]
            if account:
                report_summary.extra = account.extra
                if account.grant_key:
                    report_summary.requested_at = account.requested_at
            contact = contacts.get(report_summary.email)
            report_summary.contact_name = (
                contact.get_full_name() if contact else "")
            if report_summary.requested_at:
                report_summary.nb_na_answers = None
                report_summary.reporting_publicly = None
                report_summary.reporting_fines = None
                report_summary.nb_planned_improvements = None
            elif report_summary.segment_path:
                if report_summary.normalized_score is not None:
                    if report_summary.slug:
                        report_summary.score_url = reverse('scorecard',
                            args=(self.account, report_summary.slug))
            try:
                report_summary.verified_status = report_summary.verified.verified_status
                report_summary.verified_by = report_summary.verified.verified_by
            except VerifiedSample.DoesNotExist: #RelatedObjectDoesNotExist:
                report_summary.verified_status = VerifiedSample.STATUS_NO_REVIEW
                report_summary.verified_by = None
        self._report_queries("report summaries updated with scores")

    def get_queryset(self):
        return self.get_scored_samples()

    def paginate_queryset(self, queryset):
        page = super(SupplierListMixin, self).paginate_queryset(queryset)
        if page:
            queryset = page
        self.decorate_queryset(queryset)
        return page


class TotalScoreBySubsectorAPIView(RollupMixin, GraphMixin, SupplierListMixin,
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
               "slug": "portfolio-a",
               "title": "Portfolio A",
                "tags": null,
                "predicates": [],
               "likely_metric": "/app/energy-utility/portfolios/portfolio-a/"
           }]
          }
    """
    @property
    def db_path(self):
        #pylint:disable=attribute-defined-outside-init
        if not hasattr(self, '_db_path'):
            self._db_path = ""
            prefix_candidate = self.kwargs.get(self.path_url_kwarg, '').replace(
                URL_PATH_SEP, DB_PATH_SEP)
            if prefix_candidate:
                # If the path is not a segment prefix, we just forget about it.
                last_part = prefix_candidate.split(URL_PATH_SEP)[-1]
                for seg in get_segments_candidates(self.campaign):
                    if seg.get('path', "").endswith(last_part):
                        self._db_path = seg.get('path')
                        break
            if self._db_path and not self._db_path.startswith(DB_PATH_SEP):
                self._db_path = DB_PATH_SEP + self._db_path
        return self._db_path

    def get_accounts(self):
        """
        All accounts which have elected to share their scorecard
        with ``account``.
        """
        # overrides `MatrixDetailAPIView.get_accounts()`
        return get_accessible_accounts([self.account],
            start_at=self.accounts_start_at, ends_at=self.accounts_ends_at)

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
        #pylint:disable=attribute-defined-outside-init
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
                DB_PATH_SEP: ({
                    'slug': "totals",
                    'title': "Totals",
                    'extra': {'tags': [TransparentCut.TAG_SCORECARD]}
                }, rollup_tree)
            }
            self.decorate_with_cohorts(rollup_tree)
            self._report_queries("decorate_with_cohorts completed")
            natural_charts = OrderedDict()
            totals = rollup_tree.get(DB_PATH_SEP)
            for cohort in totals[0]['cohorts']:
                natural_chart = (totals[1][cohort['slug']][0], {})
                natural_charts.update({cohort['slug']: natural_chart})
            rollup_tree = {
                DB_PATH_SEP: (totals[0], natural_charts)}
            charts = self.get_charts(rollup_tree)
            self._report_queries("get_charts completed")
            for chart in charts:
                element = PageElement.objects.filter(
                    slug=chart['slug']).first()
                chart.update({
                    'breadcrumbs': [chart['title']],
                    'picture': element.picture if element is not None else None,
                })

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
                segment=F('campaign__title')).select_related('verified')
        return queryset


    def decorate_queryset(self, queryset):
        for sample in queryset:
            sample.score_url = reverse('scorecard',
                args=(self.account, sample.slug)) # The broker should be able
            # to access all scorecards without requiring a `Portfolio` record
            # to exist.
            try:
                sample.verified_status = sample.verified.verified_status
                sample.verified_by = sample.verified.verified_by
            except VerifiedSample.DoesNotExist: #RelatedObjectDoesNotExist:
                sample.verified_status = VerifiedSample.STATUS_NO_REVIEW
                sample.verified_by = None
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
    schema = None
    serializer_class = ReportingSerializer

    search_fields = (
        'full_name',
        'printable_name'
    )
    alternate_fields = {
        'full_name': 'account__full_name',
        'printable_name': 'account__full_name',
    }
    ordering_fields = (
        ('account__full_name', 'printable_name'),
        ('campaign__title', 'segment'),
        ('verified_status', 'status'),
        ('created_at', 'last_completed_at')
    )
    ordering = ('-created_at',)

    filter_backends = (DateRangeFilter, SearchFilter, OrderingFilter)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            self.decorate_queryset(page)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        self.decorate_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return http.Response(serializer.data)


class CompareAPIView(CampaignDecorateMixin, AccountsNominativeQuerysetMixin,
                     CompareAPIBaseView):
    """
    Compares answers matching prefix (XXX same as download?)

    **Tags**: reporting

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
              "title": "(3) Does your company have a formalized ESG strategy?",
              "picture": "/tspproject/static/img/management-basics.png",
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
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
                "measured": "true"
              }, {
                "measured": "false"
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
    schema = None
    title = "Compare"
    scale = 1
    unit = None
#XXX    pagination_class = Units+labels
    serializer_class = CompareNodeSerializer

    @property
    def samples(self):
        """
        Samples to compare

        One per column
        """
        #pylint:disable=attribute-defined-outside-init
        if not hasattr(self, '_samples'):
            reporting_accounts = get_accessible_accounts(
                [self.account], campaign=self.campaign)
            # XXX currently start_at and ends_at have shaky definition in
            #     this context.
            if reporting_accounts:
                # Calling `get_completed_assessments_at_by` with an `accounts`
                # arguments evaluating to `False` will return all the latest
                # frozen samples.
                self._samples = Sample.objects.get_completed_assessments_at_by(
                    self.campaign, accounts=reporting_accounts,
                    start_at=self.start_at, ends_at=self.ends_at)
            else:
                self._samples = Sample.objects.none()
        return self._samples


    def get_serializer_context(self):
        context = super(CompareAPIView, self).get_serializer_context()
        context.update({
            'prefix': self.db_path if self.db_path else DB_PATH_SEP,
        })
        return context


class CompareIndexAPIView(CompareAPIView):
    """
    Compares answers (XXX same as download?)

    **Tags**: reporting

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
              "title": "(3) Does your company have a formalized ESG strategy?",
              "picture": "/tspproject/static/img/management-basics.png",
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
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
                "measured": "true"
              }, {
                "measured": "false"
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

    @extend_schema(operation_id='reporting_compare_index')
    def get(self, request, *args, **kwargs):
        return super(CompareIndexAPIView, self).get(
            request, *args, **kwargs)


class PortfolioAccessibleSamplesMixin(TimersMixin,
                                      AccountsNominativeQuerysetMixin):
    schema = None
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

    @property
    def period(self):
        if not hasattr(self, '_period'):
            self._period = self.get_query_param('period', 'monthly')
        return self._period

    @property
    def segments_candidates(self):
        """
        Returns a list of top-level segments that can have a ScorecardCache
        associated.
        """
        if not hasattr(self, '_segments_candidates'):
            self._segments_candidates = get_segments_candidates(self.campaign)
        return self._segments_candidates


    def get_serializer_context(self):
        context = super(
            PortfolioAccessibleSamplesMixin, self).get_serializer_context()
        context.update({
            'account': self.account,
            'segments_candidates': self.segments_candidates
        })
        return context

    def get_queryset(self):
        queryset = get_accessible_accounts(
            [self.account], campaign=self.campaign)
        # XXX Add missing suppliers that are invited but no response yet.
        #     This could be done by creating "dummy" survey_portfolio
        #     where survey_portfolio.ends_at = account.created_at
        #     (query set is `django.db.models.query.QuerySet`)
        return queryset

    def as_sample(self, key, requested_by_keys, created_at=None):
        """
        Fills a cell for column `key` with generated content since we do not
        have a completed sample. `state` could either be 'declined' when the
        profile has been invited, or 'no-data' in all cases.
        """
        state = humanize.REPORTING_NO_DATA
        if key in requested_by_keys:
            state = humanize.REPORTING_NO_RESPONSE
        elif created_at and created_at > key:
            state = humanize.REPORTING_NO_PROFILE
        sample = Sample(created_at=key)
        sample.state = state
        return sample

    def decorate_queryset(self, page):
        #pylint:disable=too-many-locals
        samples_by_account_ids = {}
        samples = []
        if page:
            samples = get_latest_frozen_by_portfolio_by_period(self.campaign,
                [self.account], period=self.period, accounts=page,
                start_at=self.start_at, ends_at=self.ends_at).prefetch_related(
            'scorecard_cache')

        for sample in samples:
            if sample.account_id not in samples_by_account_ids:
                samples_by_account_ids[sample.account_id] = []
            samples_by_account_ids[sample.account_id] += [sample]

        # We want the range of years consistent between different pages
        # returned. As a result we use `self.get_queryset()` here to compute
        # a range of dates.
        if self.start_at and self.ends_at:
            first_year = self.start_at
            last_year = self.ends_at
        else:
            range_dates = Sample.objects.filter(
                account__in=self.get_queryset(),
                is_frozen=True,
                extra__isnull=True).aggregate(
                Min('created_at'), Max('created_at'))
            first_year = datetime.datetime(
                year=datetime_or_now(range_dates.get('created_at__min')).year,
                month=1, day=1)
            last_year = datetime.datetime(
                year=datetime_or_now(range_dates.get('created_at__max')).year,
                month=12, day=31)

        if self.period == 'monthly':
            periods = construct_monthly_periods(first_year, last_year)
            self.labels = [val.strftime("%b %Y") for val in periods]
        else:
            periods = construct_yearly_periods(first_year, last_year)
            self.labels = [val.year for val in periods]

        requested_by_accounts = {}
        for optin in get_requested_by_accounts_by_period(
                self.campaign, page, self.account, period=self.period):
            if optin.account_id not in requested_by_accounts:
                requested_by_accounts[optin.account_id] = set([])
            requested_by_accounts[optin.account_id] |= set([
                optin.created_at])

        for account in page:
            if hasattr(account, '_extra'):
                #pylint:disable=protected-access
                account.extra = account._extra
            account_created_at = account.created_at
            values = []
            key = None
            sample = None
            keys_iterator = iter(periods)
            samples_iterator = iter(samples_by_account_ids.get(account.pk, []))
            try:
                sample = next(samples_iterator)
            except StopIteration:
                pass
            try:
                key = self.as_sample(next(keys_iterator),
                    requested_by_accounts.get(account.pk, []),
                    account_created_at)
            except StopIteration:
                pass
            try:
                while sample and key:
                    if period_less_than(sample.created_at, key.created_at,
                                        period_type=self.period):
                        values += [sample]
                        sample = None
                        sample = next(samples_iterator)
                    elif period_less_than(key.created_at, sample.created_at,
                                          period_type=self.period):
                        values += [key]
                        key = None
                        key = self.as_sample(next(keys_iterator),
                            requested_by_accounts.get(account.pk, []),
                            account_created_at)
                    else:
                        values += [sample]
                        try:
                            sample = next(samples_iterator)
                        except StopIteration:
                            sample = None
                        try:
                            key = self.as_sample(next(keys_iterator),
                                requested_by_accounts.get(account.pk, []),
                                account_created_at)
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
                    key = self.as_sample(next(keys_iterator),
                        requested_by_accounts.get(account.pk, []),
                        account_created_at)
            except StopIteration:
                pass

            # Merge portfolio extra field into account extra field.
            extra = {}
            for val in values:
                extra.update(extra_as_internal(val))
            account.extra = extra_as_internal(account)
            try:
                account.extra.update(extra)
            except AttributeError:
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
    Lists accessible samples for reporting profiles

    Lists accessible samples for reporting profiles by period (either yearly
    or monthly)

    **Tags**: sharing

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
                        ["2021-01-01T00:00:00Z", "declined", null],
                        ["2020-01-01T00:00:00Z", "no-data", null],
                        ["2019-01-01T00:00:00Z", "no-data", null],
                        ["2018-01-01T00:00:00Z", "no-data", null]
                    ]
                },
                {
                    "slug": "supplier-1",
                    "printable_name": "Supplier 1",
                    "values": [
                        ["2023-01-01T00:00:00Z", "complete", 82],
                        ["2022-01-01T00:00:00Z", "complete", 82],
                        ["2021-01-01T00:00:00Z", "declined", null],
                        ["2020-01-01T00:00:00Z", "no-data", null],
                        ["2019-01-01T00:00:00Z", "no-data", null],
                        ["2018-01-01T00:00:00Z", "no-data", null]
                    ]
                }
          ]
        }
    """
    title = "Accessibles"
    pagination_class = AccessiblesPagination
    serializer_class = AccessiblesSerializer

    def get(self, request, *args, **kwargs):
        self._start_time()
        resp = self.list(request, *args, **kwargs)
        self._report_queries("http response created")
        return resp


class PortfolioAccessiblesDeleteAPIView(generics.GenericAPIView):

    def delete(self, request, *args, **kwargs):
        """
        Removes access to a profile samples

        **Tags**: sharing

        **Examples

        .. code-block:: http

            DELETE /api/energy-utility/reporting/sustainability/accessibles\
/supplier-1 HTTP/1.1

        responds

        204 No Content
        """
        profile_slug = self.kwargs.get('profile')
        campaign_slug = self.kwargs.get('campaign')
        account_slug = self.kwargs.get('account')
        queryset = Portfolio.objects.filter(
            Q(campaign__slug=campaign_slug) |
            Q(campaign__isnull=True),
            grantee__slug=profile_slug,
            account__slug=account_slug)
        LOGGER.info("remove %s from %s accessibles in campaign %s",
            account_slug,  profile_slug, campaign_slug)
        queryset.delete()
        return http.Response(status=status.HTTP_204_NO_CONTENT)


class PortfolioEngagementMixin(AccountsNominativeQuerysetMixin):

    ordering_param = api_settings.ORDERING_PARAM

    search_fields = (
        'slug',
        'full_name',
        'email',
    )
    ordering_fields = (
        ('full_name', 'full_name'),
        ('last_activity_at', 'last_activity_at'),
        # XXX We cannot sort by `last_reminder_at` as these are added
        # in `decorate_queryset`.
        # ('last_reminder_at', 'last_reminder_at'),
        ('requested_at', 'requested_at'),
    )

    ordering = ('full_name',)

    filter_backends = (SearchFilter,) # XXX When `OrderingFilter` is listed
                                      # here, Django will attempt to call
                                      # and `order_by` method on a `RawQuerySet`

    @property
    def segments(self):
        if not hasattr(self, '_segments'):
            self._segments = get_segments_candidates(self.campaign)
        return self._segments

    def decorate_queryset(self, queryset):
        latest_reminders = {val.pk: val for val
            in get_latest_reminders(queryset)}
        scores = ScorecardCache.objects.filter(sample__in={
            val.sample_id for val in queryset}, path__in=[
            seg['path'] for seg in self.segments_available]).order_by('path')
        scores = {val.sample_id: val for val in scores}

        extras_queryset = Portfolio.objects.filter(
            grantee_id__in=[val.grantee_id for val in queryset],
            account_id__in=[val.account_id for val in queryset])
        extras = {(val.grantee_id, val.account_id): extra_as_internal(val)
            for val in extras_queryset}

        # adds meta information not found in main queryset.
        for account in queryset:
            scorecard_cache = scores.get(account.sample_id)
            if scorecard_cache:
                account.normalized_score = scorecard_cache.normalized_score
            reminder = latest_reminders.get(account.account_id)
            if reminder:
                account.last_reminder_at = reminder.last_reminder_at
            # Merge portfolio extra field into account extra field.
            extra = extras.get((account.grantee_id, account.account_id))
            if extra:
                account.extra = extra_as_internal(account)
                account.extra.update(extra)
        return queryset

    def get_filtering(self):
        param_states = []
        params = self.get_query_param('status')
        if params:
            if isinstance(params, six.string_types):
                params = params.split(',')
            param_states = [param.strip() for param in params]
        # validate states
        states = []
        valid_states = {status[1]
            for status in humanize.REPORTING_STATUSES}
        inverted_valid_states = {slugify(val): key
            for key, val in humanize.REPORTING_STATUSES}
        for state in param_states:
            if state in valid_states:
                states += [inverted_valid_states[state]]
        return states

    def get_ordering(self):
        fields = []
        params = self.get_query_param(self.ordering_param)
        if params:
            if isinstance(params, six.string_types):
                params = params.split(',')
            fields = [param.strip() for param in params]
        ordering_fields = []
        valid_fields = {val[1]: val[0] for val in self.ordering_fields}
        for field_ordering in fields + list(self.ordering):
            field = field_ordering.lstrip('-')
            if field in valid_fields:
                db_field_ordering = valid_fields[field]
                if (db_field_ordering not in ordering_fields and
                    ('-' + db_field_ordering) not in ordering_fields):
                    rev_prefix = '-' if field_ordering.startswith('-') else ''
                    ordering_fields += [rev_prefix + db_field_ordering]
        return ordering_fields

    def get_grantees(self):
        return [self.account]

    def get_queryset(self):
        if not self.requested_accounts:
            return PortfolioDoubleOptIn.objects.none()
        queryset = get_engagement(self.campaign, self.requested_accounts,
            grantees=self.get_grantees(), start_at=self.start_at,
            ends_at=self.ends_at, filter_by=self.get_filtering(),
            order_by=self.get_ordering())
        return queryset

    def paginate_queryset(self, queryset):
        page = super(
            PortfolioEngagementMixin, self).paginate_queryset(queryset)
        return self.decorate_queryset(page if page else queryset)


class PortfolioEngagementAPIView(PortfolioEngagementMixin,
                                 generics.ListAPIView):
    """
    Lists engagement for reporting profiles


    reporting_status can be one of:
      - invited
      - updated / work-in-progress
      - completed
      - declined (to respond)
      - completed declined to share

    **Tags**: reporting

    **Examples

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/engaged HTTP/1.1

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

    def get_serializer_context(self):
        context = super(
            PortfolioEngagementAPIView, self).get_serializer_context()
        context.update({'account': self.account})
        return context


class CompletionRateMixin(DashboardAggregateMixin):

    def get_aggregate(self, account=None, labels=None,
                      aggregate_set=False, years=0):
        #pylint:disable=unused-argument,too-many-locals
        # XXX Use the *labels* instead of recomputing weekly periods?
        last_date = datetime_or_now(self.accounts_ends_at)
        if self.accounts_start_at:
            first_date = self.accounts_start_at
        else:
            first_date = last_date - relativedelta(months=4)
        weekends_at = construct_weekly_periods(
            first_date, last_date, years=years)
        if len(weekends_at) < 2:
            # Not enough time periods
            return []

        values = []
        account_model = get_account_model()
        requested_accounts = self.get_engaged_accounts(
            account, aggregate_set=aggregate_set)
        nb_requested_accounts = len(requested_accounts)
        start_at = weekends_at[0]
        for ends_at in weekends_at[1:]:
            queryset = account_model.objects.filter(
                samples__extra__isnull=True,
                samples__is_frozen=True,
                samples__created_at__gte=start_at,
                samples__created_at__lt=ends_at,
                samples__account_id__in=requested_accounts
            ).distinct()
            nb_frozen_samples = queryset.count()
            if self.is_percentage:
                rate = as_percentage(nb_frozen_samples, nb_requested_accounts)
            else:
                rate = nb_frozen_samples
            values += [(ends_at, rate)]
        return values

    def get_response_data(self, request, *args, **kwargs):
        table = [{
            'slug': "% completion" if self.is_percentage else "nb completed",
            'title': "% completion" if self.is_percentage else "nb completed",
            'values': self.get_aggregate(self.account)
        }]
        table += [{
            'slug': "vs. last year",
            'title': "vs. last year",
            'values': self.get_aggregate(self.account, years=-1)
        }]
        for account in list(get_alliances(self.account)):
            table += [{
                'slug': account.slug,
                'title': account.printable_name,
                'values': self.get_aggregate(account, aggregate_set=True)
            }]
        return  {
            'title': "Completion rate (%s)" % (
                '%' if self.is_percentage else "nb"),
            'scale': self.scale,
            'unit': self.unit,
            'results': table
        }


class CompletionRateAPIView(CompletionRateMixin, generics.RetrieveAPIView):
    """
    Retrieves week-by-week completion rate

    Returns the week-by-week percentage of requested accounts
    that have completed a scorecard.

    **Tags**: reporting

    **Examples**

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/completion-rate HTTP/1.1

    responds

    .. code-block:: json

        {
          "title":"Completion rate (%)",
          "scale":1,
          "unit":"percentage",
          "results":[{
            "slug": "completion-rate",
            "printable_name": "% completion",
            "values":[
              ["2020-09-13T00:00:00Z",0],
              ["2020-09-20T00:00:00Z",0],
              ["2020-09-27T00:00:00Z",0],
              ["2020-10-04T00:00:00Z",0],
              ["2020-10-11T00:00:00Z",0],
              ["2020-10-18T00:00:00Z",0],
              ["2020-10-25T00:00:00Z",0],
              ["2020-11-01T00:00:00Z",0],
              ["2020-11-08T00:00:00Z",0],
              ["2020-11-15T00:00:00Z",0],
              ["2020-11-22T00:00:00Z",0],
              ["2020-11-29T00:00:00Z",0],
              ["2020-12-06T00:00:00Z",0],
              ["2020-12-13T00:00:00Z",0],
              ["2020-12-20T00:00:00Z",0],
              ["2020-12-27T00:00:00Z",0],
              ["2021-01-03T00:00:00Z",0]
            ]
          }, {
            "slug":"last-year",
            "printable_name": "vs. last year",
            "values":[
              ["2019-09-15T00:00:00Z",0],
              ["2019-09-22T00:00:00Z",0],
              ["2019-09-29T00:00:00Z",0],
              ["2019-10-06T00:00:00Z",0],
              ["2019-10-13T00:00:00Z",0],
              ["2019-10-20T00:00:00Z",0],
              ["2019-10-27T00:00:00Z",0],
              ["2019-11-03T00:00:00Z",0],
              ["2019-11-10T00:00:00Z",0],
              ["2019-11-17T00:00:00Z",0],
              ["2019-11-24T00:00:00Z",0],
              ["2019-12-01T00:00:00Z",0],
              ["2019-12-08T00:00:00Z",0],
              ["2019-12-15T00:00:00Z",0],
              ["2019-12-22T00:00:00Z",0],
              ["2019-12-29T00:00:00Z",0],
              ["2020-01-05T00:00:00Z",0]
            ]
          }, {
            "slug":"alliance",
            "printable_name": "Alliance",
            "values":[
              ["2020-09-13T00:00:00Z",0],
              ["2020-09-20T00:00:00Z",0],
              ["2020-09-27T00:00:00Z",0],
              ["2020-10-04T00:00:00Z",0],
              ["2020-10-11T00:00:00Z",0],
              ["2020-10-18T00:00:00Z",0],
              ["2020-10-25T00:00:00Z",0],
              ["2020-11-01T00:00:00Z",0],
              ["2020-11-08T00:00:00Z",0],
              ["2020-11-15T00:00:00Z",0],
              ["2020-11-22T00:00:00Z",0],
              ["2020-11-29T00:00:00Z",0],
              ["2020-12-06T00:00:00Z",0],
              ["2020-12-13T00:00:00Z",0],
              ["2020-12-20T00:00:00Z",0],
              ["2020-12-27T00:00:00Z",0],
              ["2021-01-03T00:00:00Z",0]
            ]
          }]
        }
    """
    def retrieve(self, request, *args, **kwargs):
        return http.Response(self.get_response_data(request, *args, **kwargs))


class EngagementStatsMixin(DashboardAggregateMixin):

    title = "Engagement"

    def get_aggregate(self, account=None, labels=None,
                      aggregate_set=False):
        #pylint:disable=unused-argument,too-many-locals
        requested_accounts = self.get_engaged_accounts(
            account, aggregate_set=aggregate_set)
        grantees = None # XXX should be all members for alliances but no more
        if account == self.account:
            grantees = [account]

        last_date = datetime_or_now(self.accounts_ends_at)
        if self.accounts_start_at:
            first_date = self.accounts_start_at
        else:
            first_date = last_date - relativedelta(months=4)
        weekends_at = construct_weekly_periods(
            first_date, last_date)

        engagement = get_engagement_by_reporting_status(
            self.campaign, requested_accounts,
            grantees=grantees, start_at=weekends_at[0], ends_at=weekends_at[-1])

        stats = {key: 0
            for key in humanize.COLLAPSED_REPORTING_ENGAGE_STATUSES.values()}
        for reporting_status, val in six.iteritems(engagement):
            humanized_status = \
                humanize.COLLAPSED_REPORTING_STATUSES[reporting_status]
            stats[humanized_status] += val

        if self.unit == 'percentage':
            total = 0
            for val in six.itervalues(stats):
                total += val
            prev_stats = stats
            stats = {}
            for key, val in six.iteritems(prev_stats):
                stats.update({key: as_percentage(val, total)})

        return list(stats.items())


class EngagementStatsAPIView(EngagementStatsMixin, generics.RetrieveAPIView):
    """
    Retrieves up-to-date engagement rate

    Returns the engagement as of Today

    **Tags**: reporting

    **Examples**

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/engaged/stats HTTP/1.1

    responds

    .. code-block:: json

        {
          "title":"Completion rate (%)",
          "scale":1,
          "unit":"percentage",
          "results":[{
            "slug": "completion-rate",
            "printable_name": "% completion",
            "values":[
              ["2020-09-13T00:00:00Z",0],
              ["2020-09-20T00:00:00Z",0],
              ["2020-09-27T00:00:00Z",0],
              ["2020-10-04T00:00:00Z",0],
              ["2020-10-11T00:00:00Z",0],
              ["2020-10-18T00:00:00Z",0],
              ["2020-10-25T00:00:00Z",0],
              ["2020-11-01T00:00:00Z",0],
              ["2020-11-08T00:00:00Z",0],
              ["2020-11-15T00:00:00Z",0],
              ["2020-11-22T00:00:00Z",0],
              ["2020-11-29T00:00:00Z",0],
              ["2020-12-06T00:00:00Z",0],
              ["2020-12-13T00:00:00Z",0],
              ["2020-12-20T00:00:00Z",0],
              ["2020-12-27T00:00:00Z",0],
              ["2021-01-03T00:00:00Z",0]
            ]
          }, {
            "slug":"last-year",
            "printable_name": "vs. last year",
            "values":[
              ["2019-09-15T00:00:00Z",0],
              ["2019-09-22T00:00:00Z",0],
              ["2019-09-29T00:00:00Z",0],
              ["2019-10-06T00:00:00Z",0],
              ["2019-10-13T00:00:00Z",0],
              ["2019-10-20T00:00:00Z",0],
              ["2019-10-27T00:00:00Z",0],
              ["2019-11-03T00:00:00Z",0],
              ["2019-11-10T00:00:00Z",0],
              ["2019-11-17T00:00:00Z",0],
              ["2019-11-24T00:00:00Z",0],
              ["2019-12-01T00:00:00Z",0],
              ["2019-12-08T00:00:00Z",0],
              ["2019-12-15T00:00:00Z",0],
              ["2019-12-22T00:00:00Z",0],
              ["2019-12-29T00:00:00Z",0],
              ["2020-01-05T00:00:00Z",0]
            ]
          }, {
            "slug":"alliance",
            "printable_name": "Alliance",
            "values":[
              ["2020-09-13T00:00:00Z",0],
              ["2020-09-20T00:00:00Z",0],
              ["2020-09-27T00:00:00Z",0],
              ["2020-10-04T00:00:00Z",0],
              ["2020-10-11T00:00:00Z",0],
              ["2020-10-18T00:00:00Z",0],
              ["2020-10-25T00:00:00Z",0],
              ["2020-11-01T00:00:00Z",0],
              ["2020-11-08T00:00:00Z",0],
              ["2020-11-15T00:00:00Z",0],
              ["2020-11-22T00:00:00Z",0],
              ["2020-11-29T00:00:00Z",0],
              ["2020-12-06T00:00:00Z",0],
              ["2020-12-13T00:00:00Z",0],
              ["2020-12-20T00:00:00Z",0],
              ["2020-12-27T00:00:00Z",0],
              ["2021-01-03T00:00:00Z",0]
            ]
          }]
        }
    """
    def retrieve(self, request, *args, **kwargs):
        resp = self.get_response_data(request, *args, **kwargs)
        return http.Response(resp)
