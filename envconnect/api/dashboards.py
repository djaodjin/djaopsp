# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

import datetime, json, logging, re
from collections import OrderedDict

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.db.models import Count, Max, Q
from django.http import Http404
from django.utils import six
from django.utils.encoding import force_text
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _
from deployutils.helpers import datetime_or_now
from deployutils.crypt import JSONEncoder
from extra_views.contrib.mixins import SearchableListMixin, SortableListMixin
from pages.models import PageElement
from rest_framework import generics, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from saas.models import Plan, Subscription
from survey.api.matrix import MatrixDetailAPIView
from survey.models import Answer, EditableFilter, Matrix, Sample
from survey.utils import get_account_model

from .benchmark import BenchmarkMixin
from .. import signals
from ..helpers import freeze_scores, get_testing_accounts
from ..mixins import ReportMixin
from ..models import _show_query_and_result, Consumption
from ..serializers import AccountSerializer, NoModelSerializer
from ..suppliers import get_supplier_managers


LOGGER = logging.getLogger(__name__)

#AccountType = namedtuple('AccountType',
#    ['pk', 'slug', 'printable_name', 'email', 'request_key', 'extra'])

class AccountType(object):

    def __init__(self, pk=None, slug=None, printable_name=None, email=None,
        request_key=None, extra=None):
        #pylint:disable=invalid-name
        self.pk = pk
        self.slug = slug
        self.printable_name = printable_name
        self.email = email
        self.request_key = request_key
        self.grant_key = request_key # XXX
        self.extra = extra
        self.reports_to = []

    @classmethod
    def _make(cls, val):
        return cls(pk=val[0], slug=val[1], printable_name=val[2],
            email=val[3], request_key=val[4], extra=val[5])


def get_reporting_status(account, expired_at):
    #pylint:disable=too-many-return-statements
    last_activity_at = account.get('last_activity_at', None)
    if last_activity_at:
        if account.get('assessment_completed', False):
            if account.get('improvement_completed', False):
                if last_activity_at < expired_at:
                    return AccountSerializer.REPORTING_EXPIRED
                return AccountSerializer.REPORTING_COMPLETED
            if last_activity_at < expired_at:
                return AccountSerializer.REPORTING_ABANDONED
            return AccountSerializer.REPORTING_PLANNING_PHASE
        if last_activity_at < expired_at:
            return AccountSerializer.REPORTING_ABANDONED
        return AccountSerializer.REPORTING_ASSESSMENT_PHASE
    return AccountSerializer.REPORTING_NOT_STARTED


class CompletionSummaryPagination(PageNumberPagination):
    """
    Decorate the results of an API call with stats on completion of assessment
    and improvement planning.
    """

    def paginate_queryset(self, queryset, request, view=None):
        self.no_assessment = 0
        self.abandoned = 0
        self.expired = 0
        self.assessment_phase = 0
        self.improvement_phase = 0
        self.completed = 0
        for account in queryset:
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
        if hasattr(queryset, 'reporting_publicly'):
            self.reporting_publicly_count = queryset.reporting_publicly
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
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class DashboardMixin(BenchmarkMixin):

    account_model = get_account_model()

    def _get_scored_answers(self, population, metric_id,
                            includes=None, questions=None, prefix=None):
        """
        Returns a list of tuples with the following fields:

        - account_id
        - sample_id
        - is_completed
        - is_planned
        - numerator
        - denominator
        - last_activity_at
        - answer_id
        - question_id
        - path
        - (dummy) implemented
        - environmental_value
        - business_value
        - profitability
        - implementation_ease
        - avg_value
        - (dummy) nb_respondents
        - (dummy) rate
        - opportunity
        """
        #pylint:disable=too-many-arguments
        scored_answers = """
WITH samples AS (
SELECT survey_sample.* FROM survey_sample
INNER JOIN (
    SELECT survey_sample.account_id, MAX(survey_sample.created_at) as created_at
    FROM survey_answer
    INNER JOIN survey_question
      ON survey_answer.question_id = survey_question.id
    INNER JOIN survey_sample
      ON survey_answer.sample_id = survey_sample.id
    WHERE survey_question.path LIKE '%(prefix)s%%'
      AND survey_sample.extra IS NULL
      AND survey_sample.is_frozen = %(true)s
      GROUP BY survey_sample.account_id) AS last_frozen_assessments
    ON survey_sample.account_id = last_frozen_assessments.account_id
      AND survey_sample.created_at = last_frozen_assessments.created_at
),
expected_opportunities AS (
SELECT
    survey_question.id AS question_id,
    survey_question.path AS path,
    '' AS implemented,
    survey_question.environmental_value AS environmental_value,
    survey_question.business_value AS business_value,
    survey_question.profitability AS profitability,
    survey_question.implementation_ease AS implementation_ease,
    survey_question.avg_value AS avg_value,
    0 AS nb_respondents,
    0 AS rate,
    survey_question.default_metric_id AS default_metric_id,
    survey_question.opportunity AS opportunity,
    samples.account_id AS account_id,
    samples.id AS sample_id,
    samples.is_frozen AS is_completed,
    samples.extra AS is_planned
FROM samples
INNER JOIN survey_enumeratedquestions
    ON samples.survey_id = survey_enumeratedquestions.campaign_id
INNER JOIN survey_question
    ON survey_question.id = survey_enumeratedquestions.question_id
WHERE survey_question.path LIKE '%(prefix)s%%'
)
SELECT
    expected_opportunities.question_id AS id,
    expected_opportunities.account_id AS account_id,
    expected_opportunities.sample_id AS sample_id,
    expected_opportunities.is_completed AS is_completed,
    expected_opportunities.is_planned AS is_planned,
    CAST(survey_answer.measured AS FLOAT) AS numerator,
    CAST(survey_answer.denominator AS FLOAT) AS denominator,
    survey_answer.created_at AS last_activity_at,
    survey_answer.id AS answer_id,
    survey_answer.rank AS rank,
    expected_opportunities.path AS path,
    expected_opportunities.implemented AS implemented,
    expected_opportunities.environmental_value AS environmental_value,
    expected_opportunities.business_value AS business_value,
    expected_opportunities.profitability AS profitability,
    expected_opportunities.implementation_ease AS implementation_ease,
    expected_opportunities.avg_value AS avg_value,
    expected_opportunities.nb_respondents AS nb_respondents,
    expected_opportunities.rate AS rate,
    expected_opportunities.default_metric_id AS default_metric_id,
    expected_opportunities.opportunity AS opportunity
FROM expected_opportunities
LEFT OUTER JOIN survey_answer
    ON expected_opportunities.question_id = survey_answer.question_id
    AND expected_opportunities.sample_id = survey_answer.sample_id
WHERE survey_answer.id IS NULL OR survey_answer.metric_id = 2""" % {
    'true': "1" if self._is_sqlite3() else "'t'",
    'prefix': prefix}
#        scored_answers = super(DashboardMixin, self)._get_scored_answers(
#            population, metric_id,
#            includes=includes, questions=questions, prefix=prefix)
        _show_query_and_result(scored_answers)
        return scored_answers

    @property
    def requested_accounts(self):
        if not hasattr(self, '_requested_accounts'):
            ends_at = datetime_or_now()
            self._requested_accounts = []
            level = set([self.account.pk])
            next_level = level | set([rec['organization']
                for rec in Subscription.objects.filter(
                        plan__organization__in=level).exclude(
                        organization__in=get_testing_accounts()).values(
                        'organization').distinct()])
            try:
                extra = json.loads(self.account.extra)
            except (TypeError, ValueError):
                extra = None
            if extra and extra.get('supply_chain', None):
                while len(level) < len(next_level):
                    level = next_level
                    next_level = level | set([rec['organization']
                        for rec in Subscription.objects.filter(
                            plan__organization__in=level).exclude(
                            organization__in=get_testing_accounts()).values(
                            'organization').distinct()])
            prev = None
            self._requested_accounts = []
            for val in Subscription.objects.filter(
                    ends_at__gt=ends_at, # from `SubscriptionMixin.get_queryset`
                    plan__organization__in=level).select_related(
                    'organization').values_list('organization__pk',
                    'organization__slug', 'organization__full_name',
                    'organization__email', 'grant_key', 'extra',
                    'plan__organization__slug', 'plan__organization__full_name'
                    ).order_by('organization__full_name', 'organization__pk'):
                account = AccountType._make(val)
                # XXX deals with grant_key and extra
                if prev and prev.pk != account.pk:
                    self._requested_accounts += [prev]
                    prev = account
                elif not prev:
                    prev = account
                else:
                    if not prev.extra:
                        prev.extra = []
                prev.reports_to += [(val[6], val[7])]
            if prev:
                self._requested_accounts += [prev]
        return self._requested_accounts

    def get_accounts(self):
        return [val for val in self.requested_accounts if not val.grant_key]


class SupplierQuerySet(object):
    """
    Proxy object that acts like a QuerySet on a list of *items*.

    This was specially crafted for the `SupplierListAPIView`.
    It is not suitable for other kinds of lists at this point.
    """

    def __init__(self, items, reporting_publicly=None):
        self.items = items
        self._reporting_publicly = reporting_publicly

    def __getattr__(self, name):
        return getattr(self.items, name)

    def __getitem__(self, idx):
        return self.items[idx]

    def __len__(self):
        return len(self.items)

    def order_by(self, field):
        """
        returns the list ordered by *field*.
        """
        reverse_order = False
        if field.startswith('-'):
            reverse_order = True
            field = field[1:]
        val = None
        for item in self.items:
            val = item.get(field, None)
            if val is not None:
                break

        #pylint:disable=redefined-variable-type
        if isinstance(val, (six.integer_types, float)):
            key_func = lambda rec: rec.get(field) if rec.get(field, None) else 0
        elif isinstance(val, datetime.datetime):
            default = datetime.datetime.min
            if default.tzinfo is None:
                default = default.replace(tzinfo=utc)
            key_func = lambda rec: (rec.get(field)
                if rec.get(field, None) else default)
        elif isinstance(val, list):
            if reverse_order:
                key_func = lambda rec: min([score[0] for score in (
                    rec.get(field) if rec.get(field, None) else [[0]])])
            else:
                key_func = lambda rec: max([score[0] for score in (
                    rec.get(field) if rec.get(field, None) else [[100]])])
        else:
            key_func = lambda rec: rec.get(field, "").lower()
        return SupplierQuerySet(sorted(self.items,
            key=key_func, reverse=reverse_order),
            reporting_publicly=self.reporting_publicly)

    def filter(self, *args, **kwargs): #pylint:disable=unused-argument
        items = []
        for arg in args:
            if isinstance(arg, Q):
                if arg.connector == arg.AND:
                    items = self.items
                    for child in arg.children:
                        filter_items = items
                        items = []
                        if isinstance(child, tuple):
                            name, _ = child[0].split('__')
                            pat = child[1].upper()
                            items += [item for item in filter_items
                                if pat in item[name].upper()]
                        else:
                            items += [item for item in self.filter(child)
                                if item in filter_items]
                elif arg.connector == arg.OR:
                    for child in arg.children:
                        if isinstance(child, tuple):
                            name, _ = child[0].split('__')
                            pat = child[1].upper()
                            items += [item for item in self.items
                                if pat in item[name].upper()]
                        else:
                            items += self.filter(child)
        return SupplierQuerySet(items,
            reporting_publicly=self.reporting_publicly)

    def distinct(self):
        pk_field = 'printable_name'
        items = []
        for new_item in self.items:
            found = False
            for item in items:
                if new_item[pk_field] == item[pk_field]:
                    found = True
                    break
            if not found:
                items += [new_item]
        return SupplierQuerySet(items,
            reporting_publicly=self.reporting_publicly)

    @property
    def reporting_publicly(self):
        return self._reporting_publicly


class SupplierListMixin(DashboardMixin):
    """
    Scores for all reporting entities in a format that can be used by the API
    and spreadsheet downloads.
    """

    @property
    def requested_accounts_pk(self):
        return [account.pk for account in self.requested_accounts]

    @staticmethod
    def get_nb_questions_per_segment():
        # XXX This is Postgres-specific code
        raw_query = "SELECT distinct(substring(survey_question.path"\
" from '.*/sustainability-[^/]+/')) FROM survey_question;"
        nb_questions_per_segment = {}
        with connection.cursor() as cursor:
            cursor.execute(raw_query)
            for row in cursor.fetchall():
                nb_questions = Consumption.objects.filter(
                    path__startswith=row[0]).count()
                nb_questions_per_segment.update({row[0]: nb_questions})
        return nb_questions_per_segment

    @staticmethod
    def get_segments(sample_ids):
        results = []
        raw_query = ("SELECT distinct(substring(survey_question.path from"\
" '.*/sustainability-[^/]+/')) FROM survey_question INNER JOIN survey_answer"\
" ON survey_question.id = survey_answer.question_id WHERE sample_id IN (%s);" %
            ", ".join([str(sample_id) for sample_id in sample_ids]))
        with connection.cursor() as cursor:
            cursor.execute(raw_query)
            for row in cursor.fetchall():
                results += [row[0]]
        return results

    @property
    def complete_assessments(self):
        if not hasattr(self, '_complete_assessments'):
            self._complete_assessments = set([])
            # We have to get complete assessments separately from complete
            # improvements the sample is always not frozen by definition.
            for rec in Sample.objects.filter(
                    extra__isnull=True, is_frozen=True,
                    account__in=self.requested_accounts_pk).values(
                        'account').annotate(Max('created_at')):
                self._complete_assessments |= set([rec['account']])

            # Using per-segment method, within 10% of completion
            #for segment_path, segment_nb_questions in six.iteritems(
            #        self.get_nb_questions_per_segment()):
            #    assessement_completed = Sample.objects.filter(
            #        answers__question__path__startswith=segment_path,
# We don't keep the actual answer, just the score.
#                    answers__metric_id=self.default_metric_id,
            #        extra__isnull=True, is_frozen=True,
            #        account__in=self.requested_accounts_pk).values(
            #                'account').annotate(
            #        Max('created_at'), Count('answers__pk'))
            #    for rec in assessement_completed:
            #        within_10_percent = int(0.9 * segment_nb_questions)
            #        if rec['answers__pk__count'] >= within_10_percent:
            #            self._complete_assessments |= set([rec['account']])

        return self._complete_assessments

    @property
    def complete_improvements(self):
        if not hasattr(self, '_complete_improvements'):
            self._complete_improvements = set([])
            # We have to get complete assessments separately from complete
            # improvements the sample is always not frozen by definition.
            improvements_planned = Sample.objects.filter(
                    extra='is_planned', is_frozen=True,
                    account__in=self.requested_accounts_pk).values(
                    'account').annotate(Max('created_at'))
            # XXX counts only improvement plans with an actual item selected.
            #improvements_planned = Sample.objects.filter(
            #    extra='is_planned', is_frozen=True,
            #    answers__metric_id=self.default_metric_id,
            #    answers__measured=Consumption.NEEDS_SIGNIFICANT_IMPROVEMENT,
            #    account__in=self.requested_accounts_pk).values(
            #        'account').annotate(
            #        Max('created_at'), Count('answers__pk'))
            for rec in improvements_planned:
                self._complete_improvements |= set([rec['account']])
        return self._complete_improvements

    @staticmethod
    def _prepare_account(account):
        """
        Returns the initial dictionnary used to populate results.

        Overriding this method and setting `request_key` to `None`
        enables to show scores for all accounts.
        """
        return {
            'slug': account.slug,
            'printable_name': account.printable_name,
            'email': account.email,
            'request_key': account.request_key,
            'extra': account.extra,
            'reports_to': account.reports_to}

    def get_scores(self, account, segments, actives,
                  complete_assessments, complete_improvements, expired_at):
        #pylint:disable=too-many-arguments
        result = self._prepare_account(account)
        last_activity_at = None
        account_scores = []
        for segment_key, segment_val in six.iteritems(segments):
            segment = segment_val[0]
            scores = segment['accounts']
            score = scores.get(account.pk, None)
            if score is None:
                continue
            created_at = score.get('created_at', None)
            if not last_activity_at or (
                    created_at and last_activity_at < created_at):
                last_activity_at = created_at
            if not result['request_key']:
                nb_answers = score.get('nb_answers', 0)
                nb_questions = score.get('nb_questions', 0)
                if nb_answers == nb_questions and nb_questions != 0:
                    normalized_score = score.get('normalized_score', None)
                else:
                    normalized_score = None
                if segment['slug'].startswith('framework'):
                    score_url = reverse('envconnect_assess_organization',
                        args=(account.slug,
                              '/sustainability-%s' % str(segment['slug'])))
                else:
                    score_url = reverse('benchmark_organization',
                        args=(account.slug,
                              '/sustainability-%s' % str(segment['slug'])))
                if (segment['slug'].startswith('framework') or
                    normalized_score is not None):
                    account_scores += [
                        (normalized_score, score_url, segment['title'])]
                # XXX We should really compute a score here.
                improvement_score = score.get('improvement_numerator', None)
                if improvement_score is not None:
                    result.update({'improvement_score': improvement_score})

        if not last_activity_at:
            last_activity_at = actives.get(account.pk, None)
        result.update({
            'scores': account_scores,
            'last_activity_at': last_activity_at,
            'assessment_completed': (
                account.pk in complete_assessments),
            'improvement_completed': (
                account.pk in complete_improvements),
        })
        result.update({
            # `get_reporting_status` uses fields set previously in `result`.
            'reporting_status': get_reporting_status(result, expired_at)})
        if account.extra and '"originator"' in account.extra:
            # XXX Hacky way to detect supplier initiated share of scorecard.
            # that works for now.
            result.update({'supplier_initiated': True})
        return result

    def get_queryset(self):
        return self.get_suppliers(self.rollup_scores()) #SupplierListMixin

    def get_suppliers(self, rollup_tree):
        results = []
        expired_at = datetime_or_now() - relativedelta(year=1)

        # XXX currently a subset query of ``get_active_by_accounts`` because
        # ``get_active_by_accounts`` returns unfrozen samples.
        actives = Sample.objects.filter(
            account_id__in=self.requested_accounts_pk,
            extra=None).values(
            'account_id').annotate(Max('created_at'))
        actives_d = dict([(act['account_id'], act['created_at__max'])
            for act in list(actives)])

        # Suppliers reporting publicly
        CATEGORIZED_MEASUREMENTS = [4]
        nb_suppliers_reporting_publicly = Answer.objects.filter(
           question__path=Consumption.objects.filter(
               default_metric_id__in=CATEGORIZED_MEASUREMENTS).values('path'),
           measured=Consumption.YES,
           sample__in=actives.values_list('pk', flat=True)).count()

        for account in self.requested_accounts:
            try:
                results += [self.get_scores(account, rollup_tree[1], actives_d,
                    self.complete_assessments, self.complete_improvements,
                    expired_at)]
            except self.account_model.DoesNotExist:
                pass
        return SupplierQuerySet(results,
            reporting_publicly=nb_suppliers_reporting_publicly)


class SupplierListBaseAPIView(SupplierListMixin, generics.ListAPIView):
    """
    List of suppliers accessible by the request user
    with normalized (total) score when the supplier completed
    an assessment.

    GET /api/:organization/suppliers

    Example Response:

        {
          "count":1,
          "next":null
          "previous":null,
          "results":[{
             "slug":"andy-shop",
             "printable_name":"Andy's Shop",
             "created_at": "2017-01-01",
             "scores": ["boxes-and-enclosures", 94, "Boxes & enclosures"]
             "normalized_score":94
          }]
        }
    """
    serializer_class = AccountSerializer
    pagination_class = CompletionSummaryPagination


class SupplierSmartListMixin(SortableListMixin, SearchableListMixin):
    """
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
    search_fields = ['printable_name',
                     'email']

    sort_fields_aliases = [('printable_name', 'printable_name'),
                           ('last_activity_at', 'last_activity_at'),
                           ('assessment_completed', 'assessment_completed'),
                           ('scores', 'scores'),
                           ('improvement_completed', 'improvement_completed')]


class SupplierListAPIView(SupplierSmartListMixin, SupplierListBaseAPIView):

    pass



class TotalScoreBySubsectorAPIView(DashboardMixin, MatrixDetailAPIView):
    """
    A table of scores for cohorts against a metric.

    Uses the total score for each organization as recorded
    by the assessment surveys and present aggregates
    by industry sub-sectors (Boxes & enclosures, etc.)

    **Examples**:

    .. sourcecode:: http

        GET /api/matrix/totals

        Response:

        [{
           "slug": "totals",
           "title": "Average scores by supplier industry sub-sector"
           "tag": ["scorecard"],
           "cohorts": [{
               "slug": "/portfolio-a",
               "title":"Portfolio A",
               "likely_metric":"http://localhost/app/energy-utility/portfolios/portfolio-a/"
           },
           "values": [{
               "portfolio-a": "0.1",
               "portfolio-b": "0.5",
           }
        }
        ...
        ]
    """
    @staticmethod
    def as_metric_candidate(cohort_slug):
        look = re.match(r"(\S+)(-\d+)$", cohort_slug)
        if look:
            return look.group(1)
        return cohort_slug

    def aggregate_scores(self, metric, cohorts, cut=None, accounts=None):
        #pylint:disable=unused-argument
        if accounts is None:
            accounts = get_account_model().objects.all()
        scores = {}
        rollup_tree = self.rollup_scores()#TotalScoreBySubsectorAPIView
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
                    EditableFilter.objects.get(slug=look.group(1)).slug,))
            except EditableFilter.DoesNotExist:
                pass
        if likely_metric is None:
            likely_metric = reverse('scorecard_organization',
                args=(cohort_slug, "/sustainability-%s" % default))
        if likely_metric:
            likely_metric = self.request.build_absolute_uri(likely_metric)
        return likely_metric

    def decorate_with_scores(self, rollup_tree, accounts=None, prefix=""):
        if accounts is None:
            accounts = dict([(account.pk, account)
                for account in self.get_accounts()])

        for key, values in six.iteritems(rollup_tree[1]):
            self.decorate_with_scores(values, accounts=accounts, prefix=key)

        score = {}
        cohorts = []
        accounts_with_score = rollup_tree[0].get('accounts', {})
        for account_id, account_score in six.iteritems(accounts_with_score):
            if account_id in accounts:
                n_score = account_score.get('normalized_score', 0)
                if n_score > 0:
                    account = accounts.get(account_id, None)
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
            accounts = dict([(account.pk, account)
                for account in self.get_accounts()])
        score = {}
        cohorts = []
        for path, values in six.iteritems(rollup_tree[1]):
            self.decorate_with_scores(values, accounts=accounts, prefix=path)
            nb_accounts = 0
            normalized_score = 0
            for account_id, account_score in six.iteritems(
                    values[0].get('accounts', {})):
                if account_id in accounts:
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
            values[0]['tag'] = [settings.TAG_SCORECARD]
        rollup_tree[0]['values'] = score
        rollup_tree[0]['cohorts'] = cohorts

    def get(self, request, *args, **kwargs):
        #pylint:disable=unused-argument,too-many-locals
        try:
            from_root, trail = self.breadcrumbs
        except Http404:
            from_root = ''
            trail = []
        roots = [trail[-1][0]] if trail else None
        # calls rollup_scores from TotalScoreBySubsectorAPIView
        rollup_tree = self.rollup_scores(roots, from_root)
        if roots:
            for node in six.itervalues(rollup_tree[1]):
                rollup_tree = node
                break
            self.decorate_with_scores(rollup_tree, prefix=from_root)
            excludes = None
            parts = from_root.split("/")
            if len(parts) > 1:
                if not parts[1].startswith('sustainability-'):
                    excludes = ['sustainability-%s' % parts[1]]
                else:
                    excludes = [parts[1]]
            charts = self.get_charts(rollup_tree, excludes=excludes)
            charts += [rollup_tree[0]]
        else:
            self.decorate_with_cohorts(rollup_tree, prefix=from_root)
            natural_charts = OrderedDict()
            for cohort in rollup_tree[0]['cohorts']:
                natural_chart = (rollup_tree[1][cohort['slug']][0], {})
                natural_charts.update({cohort['slug']: natural_chart})
            rollup_tree = (rollup_tree[0], natural_charts)
            charts = self.get_charts(rollup_tree)
            for chart in charts:
                element = PageElement.objects.filter(slug=chart['slug']).first()
                tag = element.tag if element is not None else ""
                chart.update({
                    'breadcrumbs': [chart['title']],
                    'icon': element.text if element is not None else "",
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

        self.create_distributions(rollup_tree)
        self.decorate_with_breadcrumbs(rollup_tree)
        distribution_charts, complete = self.flatten_distributions(
            rollup_tree, prefix=from_root)

        for chart in charts:
            if 'accounts' in chart:
                del chart['accounts']

        return Response(charts)


class ShareScorecardSerializer(NoModelSerializer):

    full_name = serializers.CharField()
    slug = serializers.SlugField(required=False)
    email = serializers.EmailField(required=False)
    message = serializers.CharField(required=False)

    def validate(self, attrs):
        if not (attrs.get('slug', None) or attrs.get('email', None)):
            raise ValidationError({'detail': _("An organization profile must"\
            " exist on TSP or a contact e-mail provided.")})
        return attrs


class ShareScorecardAPIView(ReportMixin, generics.CreateAPIView):
    """
    Share a supplier assessment, scorecard and improvement planning
    with customers, clients and/or investors.
    """
    serializer_class = ShareScorecardSerializer

    @property
    def improvement_sample(self):
        # duplicate from `ImprovementQuerySetMixin.improvement_sample`
        if not hasattr(self, '_improvement_sample'):
            self._improvement_sample = Sample.objects.filter(
                extra='is_planned',
                survey=self.survey,
                account=self.account).order_by('-created_at').first()
        return self._improvement_sample

    def create(self, request, *args, **kwargs):
        #pylint:disable=too-many-locals,too-many-statements
        if request.data:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            supplier_managers = [serializer.validated_data]
        else:
            supplier_managers = get_supplier_managers(self.account)

        last_activity_at = Answer.objects.filter(
            sample=self.assessment_sample).aggregate(Max('created_at')).get(
                'created_at__max', None)
        if not last_activity_at:
            raise ValidationError({'detail': "You cannot share a scorecard"\
            " before completing the assessment."})
        last_scored_assessment = Sample.objects.filter(
            is_frozen=True,
            extra__isnull=True,
            survey=self.survey,
            account=self.account).order_by('-created_at').first()
        if (not last_scored_assessment
            or last_scored_assessment.created_at < last_activity_at):
            # New activity since last record, let's freeze the assessment
            # and planning.
            with transaction.atomic():
                last_scored_assessment = freeze_scores(self.assessment_sample,
                    includes=self.get_included_samples(),
                    excludes=self._get_filter_out_testing(),
                    collected_by=self.request.user)
                if self.improvement_sample:
                    freeze_scores(self.improvement_sample,
                        includes=self.get_included_samples(),
                        excludes=self._get_filter_out_testing(),
                        collected_by=self.request.user)

        # send assessment updated and invite notifications
        data = supplier_managers
        status_code = None
        for supplier_manager in supplier_managers:
            supplier_manager_slug = supplier_manager.get('slug', None)
            if supplier_manager_slug:
                try:
                    matrix = Matrix.objects.filter(
                        account__slug=supplier_manager_slug,
                        metric__slug='totals').select_related('account').get()
                    # Supplier manager already has a dashboard
                    LOGGER.info("%s shared %s assessment (%s) with %s",
                        self.request.user, self.account, last_scored_assessment,
                        supplier_manager_slug)

                    # Update or create dashboard entry
                    ends_at = datetime_or_now() + relativedelta(years=1)
                    subscription_query = Subscription.objects.filter(
                        organization=self.account,
                        plan=Plan.objects.get(organization=matrix.account))
                    if subscription_query.exists():
                        # The Subscription already exists. The metadata (
                        # either requested by supplier manager or pro-actively
                        # shared) was set on creation. We thus just need to
                        # extend the end date and clear the grant_key.
                        subscription_query.update(
                            grant_key=None, ends_at=ends_at)
                    else:
                        # Create the subscription with a request_key, and
                        # a extra tag to keep track of originator.
                        Subscription.objects.create(
                            organization=self.account,
                            plan=Plan.objects.get(organization=matrix.account),
                            ends_at=ends_at,
                            extra='{"originator":"supplier"}')
                    # send assessment updated.
                    reason = supplier_manager.get('message', None)
                    if reason:
                        reason = force_text(reason)
                    signals.assessment_completed.send(sender=__name__,
                        assessment=last_scored_assessment,
                        notified=matrix.account,
                        reason=reason, request=self.request)
                    if status_code is None:
                        status_code = status.HTTP_201_CREATED

                except Matrix.DoesNotExist:
                    # Registered supplier manager but no dashboard
                    # XXX send hint to get paid version.
                    LOGGER.error("%s shared %s assessment (%s) with matrix %s",
                        self.request.user, self.account, last_scored_assessment,
                        supplier_manager_slug)
                    # XXX Should technically add all managers
                    # of `supplier_manager_slug`
                    account_model = get_account_model()
                    try:
                        dashboard_account = account_model.objects.get(
                            slug=supplier_manager_slug)
                        data = {}
                        data.update(supplier_manager)
                        data.update({
                            'slug': dashboard_account.email,
                            'email': dashboard_account.email
                        })
                        if status_code is None:
                            status_code = status.HTTP_404_NOT_FOUND
                    except account_model.DoesNotExist:
                        raise ValidationError({
                            'detail': _("Cannot find account '%s'") %
                            supplier_manager_slug})
            else:
                # Organization profile cannot be found.
                contact_email = supplier_manager.get('email', None)
                LOGGER.error("%s shared %s assessment (%s) with %s",
                    self.request.user, self.account, last_scored_assessment,
                    contact_email)
                data = {}
                data.update(supplier_manager)
                data.update({'slug': contact_email})
                if status_code is None:
                    status_code = status.HTTP_404_NOT_FOUND
        return Response(data, status=status_code)
