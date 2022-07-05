# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.
#pylint:disable=too-many-lines

import datetime, json, re
from collections import OrderedDict

from dateutil.relativedelta import relativedelta
from deployutils.crypt import JSONEncoder
from deployutils.helpers import datetime_or_now, parse_tz
from django.contrib.auth import get_user_model
from django.db import connection
import pytz
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from pages.models import PageElement
from survey.api.matrix import MatrixDetailAPIView
from survey.api.serializers import MetricsSerializer
from survey.helpers import get_extra
from survey.models import EditableFilter
from survey.utils import get_account_model, get_question_model

from ..compat import reverse, six
from ..mixins import AccountMixin
from ..models import ScorecardCache
from ..utils import (TransparentCut, get_reporting_accounts,
    get_requested_accounts, get_segments_candidates)
from .rollups import GraphMixin, RollupMixin, ScoresMixin
from .serializers import AccountSerializer


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

        GET /api/energy-utility/reporting/sustainability/ HTTP/1.1

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

        for key, values in six.iteritems(rollup_tree):
            self.decorate_with_scores(values[1], accounts=accounts, prefix=key)
            score = {}
            cohorts = []
            for account_id, account_score in six.iteritems(
                    values[0].get('accounts', {})):
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
            values[0]['values'] = score
            values[0]['cohorts'] = cohorts

    def decorate_with_cohorts(self, rollup_tree, accounts=None, prefix=""):
        #pylint:disable=unused-argument
        if accounts is None:
            accounts = self.requested_accounts

        for path, values in six.iteritems(rollup_tree):
            self.decorate_with_scores(values[1], accounts=accounts, prefix=path)
            score = {}
            cohorts = []
            for node_path, node in six.iteritems(values[1]):
                nb_accounts = 0
                normalized_score = 0
                for account_id, account_score in six.iteritems(
                        node[0].get('accounts', {})):
                    account = accounts.get(account_id, None)
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
            self.decorate_with_cohorts(rollup_tree)
            self._report_queries("decorate_with_cohorts completed")
            if False:
                natural_charts = OrderedDict()
                segments = rollup_tree.get(self.DB_PATH_SEP)[1]
                for key, values in six.iteritems(segments):
                    for cohort in values[0]['cohorts']:
                        natural_chart = (values[1][cohort['slug']][0], {})
                        natural_charts.update({cohort['slug']: natural_chart})
                    rollup_tree.update({key: (values[0], natural_charts)})

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

        return Response(charts)
