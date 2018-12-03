# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

import datetime, logging, re
from collections import namedtuple, OrderedDict

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q, Max
from django.http import Http404
from django.utils import six
from django.utils.encoding import force_text
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _
from deployutils.helpers import datetime_or_now
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
from ..helpers import freeze_scores
from ..mixins import ReportMixin
from ..models import (_show_query_and_result, _additional_filters,
    get_scored_answers)
from ..serializers import AccountSerializer, NoModelSerializer
from ..suppliers import get_supplier_managers


LOGGER = logging.getLogger(__name__)

AccountType = namedtuple('AccountType',
    ['pk', 'slug', 'printable_name', 'email', 'request_key'])


def get_reporting_status(account, expired_at):
    #pylint:disable=too-many-return-statements
    last_activity_at = account.get('last_activity_at', None)
    if last_activity_at:
        if account.get('assessment_completed', False):
            if account.get('improvement_completed', False):
                if last_activity_at < expired_at:
                    return AccountSerializer.REPORTING_EXPIRED
                else:
                    return AccountSerializer.REPORTING_COMPLETED
            else:
                if last_activity_at < expired_at:
                    return AccountSerializer.REPORTING_ABANDONED
                else:
                    return AccountSerializer.REPORTING_PLANNING_PHASE
        else:
            if last_activity_at < expired_at:
                return AccountSerializer.REPORTING_ABANDONED
            else:
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
    WHERE survey_question.path ILIKE '%(prefix)s%%'
      AND survey_sample.extra IS NULL
      AND survey_sample.is_frozen = 't'
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
    survey_question.requires_measurements AS requires_measurements,
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
WHERE survey_question.path ILIKE '%(prefix)s%%'
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
    expected_opportunities.requires_measurements AS requires_measurements,
    expected_opportunities.opportunity AS opportunity
FROM expected_opportunities
LEFT OUTER JOIN survey_answer
    ON expected_opportunities.question_id = survey_answer.question_id
    AND expected_opportunities.sample_id = survey_answer.sample_id
WHERE survey_answer.id IS NULL OR survey_answer.metric_id = 2""" % {
    'prefix': prefix}
#        scored_answers = super(DashboardMixin, self)._get_scored_answers(
#            population, metric_id,
#            includes=includes, questions=questions, prefix=prefix)
        _show_query_and_result(scored_answers, show=False)
        return scored_answers

    @property
    def requested_accounts(self):
        if not hasattr(self, '_requested_accounts'):
            ends_at = datetime_or_now()
            self._requested_accounts = [AccountType._make(val)
                for val in Subscription.objects.filter(
                    ends_at__gt=ends_at, # from `SubscriptionMixin.get_queryset`
                    plan__organization=self.account).select_related(
                    'organization').values_list('organization__pk',
                    'organization__slug', 'organization__full_name',
                    'organization__email', 'grant_key')]
        return self._requested_accounts

    def get_accounts(self):
        ends_at = datetime_or_now()
        return [AccountType._make(val) for val in Subscription.objects.filter(
            ends_at__gt=ends_at, # from `SubscriptionMixin.get_queryset`
            grant_key__isnull=True,
            plan__organization=self.account).select_related(
            'organization').values_list('organization__pk',
            'organization__slug', 'organization__full_name',
            'organization__email', 'grant_key')]


class SupplierQuerySet(object):
    """
    Proxy object that acts like a QuerySet on a list of *items*.

    This was specially crafted for the `SupplierListAPIView`.
    It is not suitable for other kinds of lists at this point.
    """

    def __init__(self, items):
        self.items = items

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
            key_func = lambda rec: rec.get(field, 0)
        elif isinstance(val, datetime.datetime):
            default = datetime.datetime.min
            if default.tzinfo is None:
                default = default.replace(tzinfo=utc)
            key_func = lambda rec: rec.get(field, default)
        else:
            key_func = lambda rec: rec.get(field, "").lower()
        return SupplierQuerySet(sorted(self.items,
            key=key_func, reverse=reverse_order))

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
        return SupplierQuerySet(items)

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
        return SupplierQuerySet(items)


class SupplierListMixin(DashboardMixin):
    """
    Scores for all reporting entities in a format that can be used by the API
    and spreadsheet downloads.
    """

    @property
    def complete_assessments(self):
        if not hasattr(self, '_complete_assessments'):
            self._complete_assessments = set([])
            # We have to get complete assessments separately from complete
            # improvements the sample is always not frozen by definition.
            for rec in Sample.objects.filter(
                    extra__isnull=True, is_frozen=True,
                    account__in=self.requested_accounts).values(
                        'account').annotate(Max('created_at')):
                self._complete_assessments |= set([rec['account']])
        return self._complete_assessments

    @property
    def complete_improvements(self):
        if not hasattr(self, '_complete_improvements'):
            self._complete_improvements = set([])
            # We have to get complete assessments separately from complete
            # improvements the sample is always not frozen by definition.
            for rec in Sample.objects.filter(
                    extra='is_planned', is_frozen=True,
                    account__in=self.requested_accounts).values(
                    'account').annotate(Max('created_at')):
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
            'request_key': account.request_key}

    def get_score(self, account, scores,
                  complete_assessments, complete_improvements, expired_at):
        #pylint:disable=too-many-arguments
        score = scores.get(account.pk, None)
        result = self._prepare_account(account)
        if score is not None and not result['request_key']:
            created_at = score.get('created_at', None)
            if created_at:
                result.update({'last_activity_at': created_at})
            nb_answers = score.get('nb_answers', 0)
            nb_questions = score.get('nb_questions', 0)
            result.update({
                'nb_answers': nb_answers,
                'nb_questions': nb_questions,
                'assessment_completed': (
                    account.pk in complete_assessments),
                'improvement_completed': (
                    account.pk in complete_improvements),
            })
            reporting_status = get_reporting_status(result, expired_at)
            result.update({'reporting_status': reporting_status})
            if nb_answers == nb_questions and nb_questions != 0:
                normalized_score = score.get('normalized_score', None)
            else:
                normalized_score = None
            if normalized_score is not None:
                result.update({'normalized_score': normalized_score})
            # XXX We should really compute a score here.
            improvement_score = score.get('improvement_numerator', None)
            if improvement_score is not None:
                result.update({'improvement_score': improvement_score})
        return result

    def get_queryset(self):
        results = []
        rollup_tree = self.rollup_scores()
        account_scores = rollup_tree[0]['accounts']
        expired_at = datetime_or_now() - relativedelta(year=1)
        for account in self.requested_accounts:
            try:
                results += [self.get_score(account, account_scores,
                    self.complete_assessments, self.complete_improvements,
                    expired_at)]
            except self.account_model.DoesNotExist:
                pass
        return SupplierQuerySet(results)


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
                           ('normalized_score', 'normalized_score'),
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
           "scores":[{
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
        rollup_tree = self.rollup_scores()
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
        for account_id, account_score in six.iteritems(rollup_tree[0].get(
                'accounts', {})):
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
        roots = [trail[-1][0]] if len(trail) > 0 else None
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
                    'icon_css':
                        'grey' if (tag and 'management' in tag) else 'orange'
                })

        for chart in charts:
            if 'accounts' in chart:
                del chart['accounts']

        # XXX
        if False and charts[0].get('slug') == 'totals':
            us_suppliers = charts[0].copy()
            us_suppliers['slug'] = "aggregates-%s" % us_suppliers['slug']
            us_suppliers['title'] = "US suppliers"
            us_suppliers['cohorts'] = [{
                'slug': "us-suppliers", 'title': "US suppliers"}]
            us_suppliers['values'] = OrderedDict({})
            sum_scores = 0
            for _, val in six.iteritems(charts[0]['values']):
                sum_scores += val
            us_suppliers['values'] = OrderedDict({
                'us-suppliers': sum_scores / len(charts[0]['values'])})
            charts += [us_suppliers]

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
        #pylint:disable=too-many-locals
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
        data = {}
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
                    Subscription.objects.update_or_create(
                        organization=self.account,
                        plan=Plan.objects.get(organization=matrix.account),
                        defaults={'grant_key': None, 'ends_at':ends_at})
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
                    LOGGER.error("%s shared %s assessment (%s) with %s",
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
                data.update(supplier_manager)
                data.update({'slug': contact_email})
                if status_code is None:
                    status_code = status.HTTP_404_NOT_FOUND
        return Response(data, status=status_code)
