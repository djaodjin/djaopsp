# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

import datetime, json, logging, re
from collections import OrderedDict

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Max, Q
from django.http import Http404
from django.utils import six
from django.utils.encoding import force_text
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _
from deployutils.helpers import datetime_or_now
from pages.models import PageElement
from rest_framework import generics, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from saas.models import Plan, Subscription
from survey.api.matrix import MatrixDetailAPIView
from survey.models import Answer, EditableFilter, Matrix, Sample
from survey.utils import get_account_model

from .. import signals
from ..compat import reverse
from ..helpers import get_segments, get_testing_accounts
from ..mixins import AccountMixin, BreadcrumbMixin, ReportMixin
from ..models import get_frozen_scored_answers, Consumption
from ..scores import populate_rollup
from ..serializers import AccountSerializer, NoModelSerializer
from ..suppliers import get_supplier_managers


LOGGER = logging.getLogger(__name__)


class AccountType(object):

    def __init__(self, pk=None, slug=None, printable_name=None, email=None,
        phone=None, request_key=None, extra=None):
        #pylint:disable=invalid-name,too-many-arguments
        self.pk = pk
        self.slug = slug
        self.printable_name = printable_name
        self.email = email
        self.phone = phone
        self.request_key = request_key
        self.grant_key = request_key # XXX
        self.extra = extra
        self.reports_to = []

    @classmethod
    def _make(cls, val):
        return cls(pk=val[0], slug=val[1], printable_name=val[2],
            email=val[3], phone=val[4], request_key=val[5], extra=val[6])


def get_reporting_status(account, expired_at):
    #pylint:disable=too-many-return-statements
    last_activity_at = account.get('last_activity_at', None)
    if last_activity_at:
        if account.get('assessment_completed', False):
            if account.get('improvement_completed', False):
                if expired_at and last_activity_at < expired_at:
                    return AccountSerializer.REPORTING_EXPIRED
                return AccountSerializer.REPORTING_COMPLETED
            if expired_at and last_activity_at < expired_at:
                return AccountSerializer.REPORTING_ABANDONED
            return AccountSerializer.REPORTING_PLANNING_PHASE
        if expired_at and last_activity_at < expired_at:
            return AccountSerializer.REPORTING_ABANDONED
        return AccountSerializer.REPORTING_ASSESSMENT_PHASE
    return AccountSerializer.REPORTING_NOT_STARTED


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


class DashboardMixin(BreadcrumbMixin, AccountMixin):
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
        'segment': 'segment',
        'normalized_score': 'normalized_score',
        'nb_na_answers': 'nb_na_answers',
        'reporting_publicly': 'reporting_publicly',
        'reporting_fines': 'reporting_fines',
        'nb_planned_improvements': 'nb_planned_improvements'}

    valid_sort_dir = {
        'asc': 'asc',
        'desc': 'desc'
    }

    @property
    def ends_at(self):
        if not hasattr(self, '_ends_at'):
            self._ends_at = self.request.GET.get('ends_at', None)
            if self._ends_at:
                self._ends_at = self._ends_at.strip('"')
            try:
                self._ends_at = datetime_or_now(self._ends_at)
            except ValueError:
                self._ends_at = datetime_or_now()
        return self._ends_at

    @property
    def expired_at(self):
        if not hasattr(self, '_expired_at'):
            self._expired_at = self.request.GET.get('start_at', None)
            if self._expired_at:
                try:
                    self._expired_at = datetime_or_now(
                        self._expired_at.strip('"'))
                except ValueError:
                    self._expired_at = None
        return self._expired_at

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

    def get_queryset(self):
        frozen_assessments_query = None
        frozen_improvements_query = None
        # XXX requested_accounts
        if self.path:
            segments = [{'title': self.element.title, 'path': str(self.path),
                'indent': 0}]
        else:
            segments = [segment for segment in get_segments() if segment['path']
                and not segment['path'].startswith('/euissca-rfx')]
        for segment in segments:
            prefix = segment['path']
            segment_query = Consumption.objects.get_latest_assessments(
                prefix, before=self.ends_at, title=segment['title'])
            if not frozen_assessments_query:
                frozen_assessments_query = segment_query
            else:
                frozen_assessments_query = "(%s) UNION (%s)" % (
                    frozen_assessments_query, segment_query)
            segment_query = Consumption.objects.get_latest_improvements(
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
  _frozen_assessments.time_spent AS time_spent,
  _frozen_assessments.is_frozen AS is_frozen,
  _frozen_assessments.extra AS extra,
  _frozen_assessments.segment_path AS segment_path,
  _frozen_assessments.segment_title AS segment_title,
  _frozen_assessments.nb_na_answers AS nb_na_answers,
  _frozen_assessments.reporting_publicly AS reporting_publicly,
  _frozen_assessments.reporting_fines AS reporting_fines,
  %(reporting_clause)s AS reporting_status
FROM (%(query)s) AS _frozen_assessments""" % {
    'query': frozen_assessments_query.replace('%', '%%'),
    'reporting_clause': reporting_clause}

        if self.expired_at:
            reporting_clause = \
"""  CASE WHEN _frozen_improvements.created_at < '%(expired_at)s'
       THEN %(reporting_expired)d
       ELSE %(reporting_completed)d END""" % {
               'expired_at': self.expired_at.isoformat(),
               'reporting_completed': AccountSerializer.REPORTING_COMPLETED,
               'reporting_expired': AccountSerializer.REPORTING_EXPIRED
       }
        else:
            reporting_clause = "%d" % AccountSerializer.REPORTING_COMPLETED
        frozen_improvements_query = """SELECT
  _frozen_improvements.id AS id,
  _frozen_improvements.slug AS slug,
  _frozen_improvements.created_at AS created_at,
  _frozen_improvements.campaign_id AS campaign_id,
  _frozen_improvements.account_id AS account_id,
  _frozen_improvements.time_spent AS time_spent,
  _frozen_improvements.is_frozen AS is_frozen,
  _frozen_improvements.extra AS extra,
  _frozen_improvements.segment_path AS segment_path,
  _frozen_improvements.segment_title AS segment_title,
  _frozen_improvements.nb_planned_improvements AS nb_planned_improvements,
  %(reporting_clause)s AS reporting_status
FROM (%(query)s) AS _frozen_improvements""" % {
    'query': frozen_improvements_query.replace('%', '%%'),
    'reporting_clause': reporting_clause}

        frozen_query = """
WITH frozen_assessments AS (%(frozen_assessments_query)s),
frozen_improvements AS (%(frozen_improvements_query)s)
SELECT
  frozen_assessments.id AS id,
  frozen_assessments.slug AS slug,
  frozen_assessments.created_at AS created_at,
  frozen_assessments.campaign_id AS campaign_id,
  frozen_assessments.account_id AS account_id,
  frozen_assessments.time_spent AS time_spent,
  frozen_assessments.is_frozen AS is_frozen,
  frozen_assessments.extra AS extra,
  frozen_assessments.segment_path AS segment_path,
  frozen_assessments.segment_title AS segment_title,
  frozen_assessments.nb_na_answers AS nb_na_answers,
  frozen_assessments.reporting_publicly AS reporting_publicly,
  frozen_assessments.reporting_fines AS reporting_fines,
  CASE WHEN frozen_assessments.created_at < frozen_improvements.created_at
       THEN frozen_improvements.nb_planned_improvements
       ELSE 0 END AS nb_planned_improvements,
  CASE WHEN frozen_assessments.created_at < frozen_improvements.created_at
       THEN COALESCE(frozen_improvements.reporting_status,
                frozen_assessments.reporting_status)
       ELSE frozen_assessments.reporting_status END AS reporting_status
FROM frozen_assessments
LEFT OUTER JOIN frozen_improvements
ON frozen_assessments.account_id = frozen_improvements.account_id AND
   frozen_assessments.segment_path = frozen_improvements.segment_path""" % {
       'frozen_assessments_query': frozen_assessments_query,
       'frozen_improvements_query': frozen_improvements_query}
        # Implementation Note: frozen_improvements will always pick the latest
        # improvement plan which might not be the ones associated with
        # the latest assessment if in a subsequent year no plan is created.

        if self.expired_at:
            reporting_clause = \
"""  CASE WHEN active_assessments.created_at < '%(expired_at)s'
       THEN %(reporting_expired)d
       ELSE %(reporting_completed)d END""" % {
               'expired_at': self.expired_at.isoformat(),
               'reporting_completed':
                   AccountSerializer.REPORTING_ASSESSMENT_PHASE,
               'reporting_expired': AccountSerializer.REPORTING_ABANDONED
       }
        else:
            reporting_clause = \
                "%d" % AccountSerializer.REPORTING_ASSESSMENT_PHASE
        if self.path:
            assessments_query = frozen_query
        else:
            assessments_query = """
WITH frozen AS (%(frozen_query)s)
SELECT
  COALESCE(frozen.id, active_assessments.id) AS id,
  COALESCE(frozen.slug, active_assessments.slug) AS slug,
  COALESCE(frozen.created_at, active_assessments.created_at) AS created_at,
  COALESCE(frozen.campaign_id, active_assessments.campaign_id) AS campaign_id,
  COALESCE(frozen.account_id, active_assessments.account_id) AS account_id,
  COALESCE(frozen.time_spent, active_assessments.time_spent) AS time_spent,
  COALESCE(frozen.is_frozen, active_assessments.is_frozen) AS is_frozen,
  COALESCE(frozen.extra, active_assessments.extra) AS extra,
  frozen.segment_path AS segment_path,
  frozen.segment_title AS segment_title,
  frozen.nb_na_answers AS nb_na_answers,
  frozen.reporting_publicly AS reporting_publicly,
  frozen.reporting_fines AS reporting_fines,
  frozen.nb_planned_improvements AS nb_planned_improvements,
  COALESCE(frozen.reporting_status, %(reporting_clause)s) AS reporting_status
FROM (SELECT
    survey_sample.id AS id,
    survey_sample.slug AS slug,
    survey_sample.created_at AS created_at,
    survey_sample.campaign_id AS campaign_id,
    survey_sample.account_id AS account_id,
    survey_sample.time_spent AS time_spent,
    survey_sample.is_frozen AS is_frozen,
    survey_sample.extra AS extra
    FROM survey_sample
    WHERE survey_sample.extra IS NULL AND
          NOT survey_sample.is_frozen
) AS active_assessments
LEFT OUTER JOIN frozen
ON active_assessments.account_id = frozen.account_id AND
   active_assessments.campaign_id = frozen.campaign_id""" % {
       'frozen_query': frozen_query,
       'reporting_clause': reporting_clause}

        accounts_clause = ""
        if self.requested_accounts_pk:
            accounts_clause = "saas_organization.id IN %s" % str(
                self.requested_accounts_pk)
            if self.search_param:
                if accounts_clause:
                    accounts_clause += "AND "
                accounts_clause += ("saas_organization.full_name ILIKE '%%%%%s%%%%'"
                    % self.search_param)
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
  assessments.time_spent AS time_spent,
  assessments.is_frozen AS is_frozen,
  assessments.extra AS extra,
  assessments.segment_path AS segment_path,
  assessments.segment_title AS segment,    -- XXX should be segment_title
  assessments.nb_na_answers AS nb_na_answers,
  assessments.reporting_publicly AS reporting_publicly,
  assessments.reporting_fines AS reporting_fines,
  assessments.nb_planned_improvements AS nb_planned_improvements,
  COALESCE(assessments.reporting_status, %(reporting_status)d) AS reporting_status,
  saas_organization.slug AS account_slug,
  saas_organization.full_name AS printable_name,
  saas_organization.email AS email,
  saas_organization.phone AS phone,
  assessments.created_at AS last_activity_at,
  '' AS score_url,                         -- updated later
  null AS normalized_score                 -- updated later
FROM saas_organization
%(join_clause)s JOIN assessments
ON saas_organization.id = assessments.account_id
%(accounts_clause)s
%(order_clause)s""" % {
    'assessments_query': assessments_query,
    'join_clause': "INNER" if self.path else "LEFT OUTER",
    'reporting_status': AccountSerializer.REPORTING_NOT_STARTED,
    'accounts_clause': accounts_clause,
    'order_clause': order_clause}

        # XXX still need to compute status and score.
        # XXX still need to add order by clause.
        return Sample.objects.raw(query)

    @property
    def query_supply_chain(self):
        if not hasattr(self, '_query_supply_chain'):
            try:
                extra = json.loads(self.account.extra)
            except (TypeError, ValueError):
                extra = None
            self._query_supply_chain = bool(
                extra and extra.get('supply_chain', None))
        return self._query_supply_chain

    @property
    def requested_accounts(self):
        if not hasattr(self, '_requested_accounts'):
            ends_at = self.ends_at
            level = set([self.account.pk])
            next_level = level | set([rec['organization']
                for rec in Subscription.objects.filter(
                        plan__organization__in=level).exclude(
                        organization__in=get_testing_accounts()).values(
                        'organization').distinct()])
            if self.query_supply_chain:
                while len(level) < len(next_level):
                    level = next_level
                    next_level = level | set([rec['organization']
                        for rec in Subscription.objects.filter(
                            plan__organization__in=level).exclude(
                            organization__in=get_testing_accounts()).values(
                            'organization').distinct()])
            self._requested_accounts = {val.organization_id: val
                for val in Subscription.objects.filter(
                    ends_at__gt=ends_at, # from `SubscriptionMixin.get_queryset`
                    plan__organization__in=level).select_related('organization')}
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

    def get_accounts(self):
        return [val for val in six.itervalues(self.requested_accounts)
            if not val.grant_key]


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
            key_func = (
                lambda rec: rec.get(field).lower()
                if rec.get(field, None) else "")
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

    def rollup_scores(self, queryset):
        try:
            from_root, trail = self.breadcrumbs
            roots = [trail[-1][0]] if trail else None
        except Http404:
            from_root = None
            roots = None
        rollup_tree = self.get_scores_tree(roots, root_prefix=from_root)
        leafs = self.get_leafs(rollup_tree=rollup_tree)
        self._report_queries("leafs loaded")

        # Populate scores in rollup_tree
        samples = tuple([sample.pk for sample in queryset if sample.pk])
        if samples:
            for prefix, values_tuple in six.iteritems(leafs):
                self.populate_leaf(values_tuple[0],
                    get_frozen_scored_answers(samples, prefix=prefix),
                    force_score=True)
        self._report_queries("leafs populated")
        populate_rollup(rollup_tree, True, force_score=True)
        self._report_queries("rollup_tree populated")
        return rollup_tree

    def decorate_queryset(self, queryset):
        """
        Updates `normalized_score` in rows of the queryset.
        """
        rollup_tree = self.rollup_scores(queryset)

        # Populate scores in report summaries
        contacts = {user.email: user
            for user in get_user_model().objects.filter(email__in=[account.email
                for account in queryset])}
        for report_summary in queryset:
            account = self.requested_accounts[report_summary.account_id]
            report_summary.extra = account.extra
            contact = contacts.get(report_summary.email)
            report_summary.contact_name = (
                contact.get_full_name() if contact else "")
            report_summary.requested_at = (
                account.created_at if account.grant_key else None)
            if report_summary.requested_at:
                report_summary.nb_na_answers = None
                report_summary.reporting_publicly = None
                report_summary.reporting_fines = None
                report_summary.nb_planned_improvements = None
            elif report_summary.segment_path:
                accounts = rollup_tree[1].get(
                    report_summary.segment_path)[0].get('accounts', {})
                report_summary.normalized_score = accounts.get(
                    report_summary.account_id, {}).get('normalized_score')
                segment_url = report_summary.segment_path
                if report_summary.normalized_score is not None:
                    if report_summary.slug:
                        report_summary.score_url = reverse(
                            'scorecard_organization', args=(
                            report_summary.account_slug,
                            report_summary.slug,
                            segment_url))
                    else:
                        report_summary.score_url = reverse(
                            'scorecard_organization_redirect', args=(
                            report_summary.account_slug, segment_url))
                else:
                    report_summary.score_url = reverse(
                        'assess_organization_redirect',
                        args=(report_summary.account_slug, segment_url))

        self._report_queries("report summaries updated with scores")


    def get_nb_questions_per_segment(self):
        nb_questions_per_segment = {}
        for segment in self.get_segments():
            nb_questions = Consumption.objects.filter(
                path__startswith=segment.path).count()
            nb_questions_per_segment.update({segment.path: nb_questions})
        return nb_questions_per_segment


    def paginate_queryset(self, queryset):
        page = super(SupplierListMixin, self).paginate_queryset(queryset)
        if page:
            queryset = page
        self.decorate_queryset(queryset)
        return page


class SupplierListAPIView(SupplierListMixin, generics.ListAPIView):
    """
    Lists of accessible supplier scorecards

    List of suppliers accessible by the request user
    with normalized (total) score when the supplier completed
    an assessment.

    **Tags**: benchmark

    **Examples

    .. code-block:: http

        GET /api/energy-utility/suppliers/ HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 1,
          "next": null,
          "previous": null,
          "results":[{
             "segment": {
               "score_url": "/andy-shop/scorecard/boxes-and-enclosures",
               "printable_name": "Boxes & enclosures"
             }
             "supplier": {
               "slug": "andy-shop",
               "printable_name": "Andy's Shop"
             }
             "created_at": "2017-01-01",
             "normalized_score": 94
          }]
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
        if icon_tag and settings.TAG_SCORECARD in icon_tag:
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

    # BenchmarkMixin.flatten_distributions
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


class TotalScoreBySubsectorAPIView(SupplierListMixin, GraphMixin,
                                   MatrixDetailAPIView):
    """
    A table of scores for cohorts against a metric.

    Uses the total score for each organization as recorded
    by the assessment surveys and present aggregates
    by industry sub-sectors (Boxes & enclosures, etc.)

    **Tags**: benchmark

    **Examples

    .. code-block:: http

        GET /api/energy-utility/matrix/totals HTTP/1.1

    responds

    .. code-block:: json

        [{
           "slug": "totals",
           "title": "Average scores by supplier industry sub-sector"
           "tag": ["scorecard"],
           "cohorts": [{
               "slug": "/portfolio-a",
               "title":"Portfolio A",
               "likely_metric":"http://localhost/app/energy-utility/portfolios/\
portfolio-a/"
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
        rollup_tree = self.rollup_scores(self.get_queryset())#TotalScoreBySubsector
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
            # XXX default is derived from `prefix` argument
            # to `decorate_with_scores`.
            likely_metric = reverse('scorecard_organization_redirect',
                args=(cohort_slug, '/%s' % default))
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
            account = accounts.get(int(account_id), None)
            if account:
                account = account.organization
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
                account = accounts.get(int(account_id), None)
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
            values[0]['tag'] = [settings.TAG_SCORECARD]
        rollup_tree[0]['values'] = score
        rollup_tree[0]['cohorts'] = cohorts

    def get(self, request, *args, **kwargs):
        #pylint:disable=unused-argument,too-many-locals
        try:
            from_root, unused = self.breadcrumbs
        except Http404:
            from_root = ''
        # calls rollup_scores from TotalScoreBySubsectorAPIView
        rollup_tree = self.rollup_scores(self.get_queryset())
        if from_root:
            for node in six.itervalues(rollup_tree[1]):
                rollup_tree = node
                break
            segment_url, segment_prefix, segment_element = self.segment
            self.decorate_with_scores(rollup_tree, prefix=segment_prefix)
            charts = self.get_charts(
                rollup_tree, excludes=[segment_prefix.split('/')[-1]])
            charts += [rollup_tree[0]]
        else:
            self.decorate_with_cohorts(rollup_tree)
            natural_charts = OrderedDict()
            for cohort in rollup_tree[0]['cohorts']:
                natural_chart = (rollup_tree[1][cohort['slug']][0], {})
                natural_charts.update({cohort['slug']: natural_chart})
            rollup_tree = (rollup_tree[0], natural_charts)
            charts = self.get_charts(rollup_tree)
            for chart in charts:
                element = PageElement.objects.filter(slug=chart['slug']).first()
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
        self.flatten_distributions(rollup_tree, prefix=from_root)

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
    Share a benchmark

    Share a supplier assessment, scorecard and improvement planning
    with customers, clients and/or investors.

    **Tags**: share

    **Examples

    .. code-block:: http

       POST /api/supplier-1/sample/46f66f70f5ad41b29c4df08f683a9a7a/\
benchmark/share/construction/ HTTP/1.1

    .. code-block:: json

       {
         "slug": "energy-utility"
       }

    """
    serializer_class = ShareScorecardSerializer

    def create(self, request, *args, **kwargs):
        #pylint:disable=too-many-locals,too-many-statements
        segment_url, segment_prefix, segment_element = self.segment
        if request.data:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            supplier_managers = [serializer.validated_data]
        else:
            supplier_managers = get_supplier_managers(self.account)

        if self.nb_required_answers < self.nb_required_questions:
            raise ValidationError({'detail':
                "You can only share an assessment after you assessed"\
                " all required practices (%d of %d) and mark your assessment"\
                " as complete." % (
                self.nb_required_answers, self.nb_required_questions)})

        if not self.assessment_sample.is_frozen:
            last_activity_at = Answer.objects.filter(
                sample=self.assessment_sample,#XXX self.get_included_samples() ?
                question__path__startswith=segment_prefix).aggregate(
                    last_activity_at=Max('created_at')).get(
                    'last_activity_at', None)
            last_scored_assessment = Sample.objects.filter(
                is_frozen=True,
                extra__isnull=True,
                campaign=self.campaign,
                account=self.account).order_by('-created_at').first()
            if (not last_scored_assessment
                or last_scored_assessment.created_at < last_activity_at):
                raise ValidationError({'detail':
                    "This assessment has been updated on %s. "\
                    "You will have to mark your assessment"\
                    " as complete before you can share it." % (
                    last_activity_at.strftime("%d %b %Y"))})

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
                    plan = Plan.objects.get(
                        slug='%s-report' % str(matrix.account),
                        organization=matrix.account)
                    subscription_query = Subscription.objects.filter(
                        organization=self.account,
                        plan=plan)
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
                            plan=plan,
                            ends_at=ends_at,
                            extra='{"originator":"supplier"}')
                    # send assessment updated.
                    reason = supplier_manager.get('message', None)
                    if reason:
                        reason = force_text(reason)
                    signals.assessment_completed.send(sender=__name__,
                        assessment=last_scored_assessment,
                        path=self.path,
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
