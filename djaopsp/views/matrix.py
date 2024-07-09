# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

import datetime, logging, re

from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from django.db import connection
from django.http import HttpResponse
from survey.helpers import get_extra
from survey.models import Campaign, Sample, Unit, UnitEquivalences
from survey.utils import get_engaged_accounts
from survey.views.matrix import CompareView as CompareBaseView
from rest_framework.generics import get_object_or_404

from ..api.campaigns import CampaignContentMixin
from ..api.serializers import EngagementSerializer
from ..compat import force_str, gettext_lazy as _, reverse
from ..mixins import AccountsNominativeQuerysetMixin
from ..models import ScorecardCache
from ..queries import get_completed_assessments_at_by, get_coalesce_engagement
from .downloads import PracticesSpreadsheetView
from .portfolios import UpdatedMenubarMixin

LOGGER = logging.getLogger(__name__)


class CompareView(UpdatedMenubarMixin, CompareBaseView):
    """
    Compare samples side-by-side
    """
    breadcrumb_url = 'matrix_compare_path'

    def get_context_data(self, **kwargs):
        context = super(CompareView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_version': site_url("/api"),
            'api_account_candidates': site_url("/api/accounts/profiles"),
            'api_plans': site_url("/api/profile/%(profile)s/plans" % {
                'profile': self.account}),
            'api_subscriptions': site_url(
                "/api/profile/%(profile)s/subscriptions" % {
                    'profile': self.account}),
            'api_units': reverse('survey_api_units'),
            'api_account_groups': reverse('survey_api_accounts_filter_list',
                args=(self.account,)),
            'api_question_typeahead': reverse(
                'api_campaign_questions', args=(self.campaign,)),
            'pages_index': reverse('pages_index'),
            'api_benchmarks_index': reverse(
                'survey_api_benchmarks_index', args=(
                self.account,)),
        })
        url_kwargs = self.get_url_kwargs()
        if 'path' in self.kwargs:
            url_kwargs.update({'path': self.kwargs.get('path')})
            update_context_urls(context, {
                'download': reverse(
                    'download_matrix_compare_path', kwargs=url_kwargs),
            })
        else:
            update_context_urls(context, {
                'download': reverse(
                    'download_matrix_compare', kwargs=url_kwargs),
            })
        return context


class CompareXLSXView(AccountsNominativeQuerysetMixin, CampaignContentMixin,
                      PracticesSpreadsheetView):
    """
    Download a spreadsheet of answers/comments with questions as rows
    and accounts as columns.
    """
    #pylint:disable=too-many-instance-attributes
    basename = 'answers'
    show_comments = True
    add_expanded_styles = False

#    ordering = ('full_name',)
    ordering = ('account_id',)

    def __init__(self, *args):
        super(CompareXLSXView, self).__init__( *args)
        self.comments_unit = Unit.objects.get(slug='freetext')
        self.points_unit = Unit.objects.get(slug='points')
        self.target_by_unit = Unit.objects.get(slug='ends-at')

    @property
    def show_planned(self):
        return self.get_query_param('planned', False)

    @staticmethod
    def _get_consumption(element):
        return element.get('consumption', None)

    @staticmethod
    def _get_tag(element):
        return element.get('tag', "")

    @staticmethod
    def _get_title(element):
        title = element.get('title', "")
        default_unit = element.get('default_unit', {})
        if default_unit and default_unit.get('system') in Unit.METRIC_SYSTEMS:
            title += " (in %s)" % default_unit.get('title')
        return title

    @property
    def verified_campaign(self):
        if not hasattr(self, '_verified_campaign'):
            #pylint:disable=attribute-defined-outside-init
            self._verified_campaign = self.campaign
            look = re.match(r'(\S+)-verified$', self._verified_campaign.slug)
            if look:
                self._verified_campaign = get_object_or_404(
                    Campaign.objects.all(), slug=look.group(1))
        return self._verified_campaign

    @property
    def latest_assessments(self):
        if not hasattr(self, '_latest_assessments'):
            #pylint:disable=attribute-defined-outside-init
            if self.accounts_with_engagement:
                self._latest_assessments = get_completed_assessments_at_by(
                    self.verified_campaign,
                    ends_at=self.ends_at, prefix=self.db_path,
                    # create a list to prevent RawQuerySet if-condition later on
                    accounts=[account.pk for account
                        in self.accounts_with_engagement])
            else:
                self._latest_assessments = Sample.objects.none()
        return self._latest_assessments

    @property
    def latest_improvements(self):
        if not hasattr(self, '_improvements'):
            #pylint:disable=attribute-defined-outside-init
            self._improvements = get_completed_assessments_at_by(
                self.verified_campaign,
                ends_at=self.ends_at, prefix=self.db_path,
                extra='is_planned',
                # create a list to prevent RawQuerySet if-condition later on
                accounts=[account.pk for account
                    in self.accounts_with_engagement])
        return self._improvements

    @property
    def accounts_with_engagement(self):
        #pylint:disable=attribute-defined-outside-init
        if not hasattr(self, '_accounts_with_engagement'):
            self._accounts_with_engagement = get_coalesce_engagement(
                self.verified_campaign, self.requested_accounts,
                start_at=self.start_at, ends_at=self.ends_at,
                order_by=self.ordering,
                grantees=[self.account]) # XXX forces a single grantee
        return self._accounts_with_engagement

    @property
    def by_paths(self):
        """
        By paths returns a dictionnary of accounts indexed by a question
        path. Each account is itself a dictionnary of `{answer:, comments:}`
        indexed by an account id.
        """
        #pylint:disable=attribute-defined-outside-init
        if not hasattr(self, '_by_paths'):
            self._by_paths = self.get_answers_by_paths(self.latest_assessments)
            if self.show_planned:
                planned_by_paths = self.get_answers_by_paths(
                    self.latest_improvements)
                for path, row in planned_by_paths.items():
                    by_paths_row = self._by_paths.get(path)
                    if row and by_paths_row:
                        assert len(row) == len(by_paths_row)
                        for by_paths_cell, cell in zip(by_paths_row, row):
                            assert by_paths_cell.get('account_id') == \
                                cell.get('account_id')
                            by_paths_cell.update({
                                'planned': cell.get('measured', '')})
        return self._by_paths


    def get_engaged_accounts(self, grantee, aggregate_set=False):
        """
        All accounts which ``grantee`` has requested a scorecard from.
        """
        # XXX Why do we override
        # `AccountsAggregatedQuerysetMixin.get_engaged_accounts`?
        if not grantee:
            grantee = self.account
        return get_engaged_accounts([grantee],
            campaign=self.verified_campaign, aggregate_set=aggregate_set,
            start_at=self.accounts_start_at, ends_at=self.accounts_ends_at,
            search_terms=self.search_terms)


    def add_datapoint(self, account, row):
        # account_id = row[1]
        measured = row[2]
        unit_id = row[3]
        default_unit_id = row[4]
        text = row[6]
        if unit_id == default_unit_id:
            # if we have already resolve `measured` to text value
            # (ex: because the unit is an enum), let's use that.
            if unit_id == self.target_by_unit.pk:
                try:
                    text = int(text)
                except ValueError:
                    pass
            account.update({'measured': text if text else measured})
        elif unit_id == self.points_unit.pk:
            account.update({'score': measured})
        elif unit_id == self.comments_unit.pk:
            account['comments'] += str(text) if text else ""
        else:
            unit = Unit.objects.get(pk=unit_id)
            if unit.system in (Unit.SYSTEM_STANDARD, Unit.SYSTEM_IMPERIAL):
                default_unit = Unit.objects.get(pk=default_unit_id)
                try:
                    equiv = UnitEquivalences.objects.get(
                        source=unit, target=default_unit)
                    account.update({
                        'measured': equiv.as_target_unit(measured)})
                except UnitEquivalences.DoesNotExist:
                    account.update({'measured': ""})
                    LOGGER.error("cannot convert '%s' to '%s' for %s:%s",
                        unit, default_unit, row[1], row[0])


    def as_account(self, key):
        """
        Fills a cell for column `key` with generated content since we do not
        have an item for it.
        """
        return {'account_id': key.pk,
            'reporting_status': key.reporting_status,
            'measured': "", 'comments': "", 'score': ""}

    @staticmethod
    def before_account(datapoint, account):
        """
        returns True if left < right
        """
        account_id = datapoint[1]
        return account_id < account.get('account_id')

    @staticmethod
    def after_account(datapoint, account):
        """
        returns True if left > right
        """
        account_id = datapoint[1]
        return account_id > account.get('account_id')

    @staticmethod
    def equals(aggregate, account):
        return aggregate.get('account_id') == account.get('account_id')


    def tabularize(self, datapoints, keys):
        """
        `datapoints` is a list of (account_id, value) sorted by account_id.
        `keys` is a list of accounts sorted using the same account_id criteria.

        This function returns a sorted list of (account_id, {values}) where
        for each account in `keys`, there is a matching account in the results,
        inserting empty values where necessary.
        """
        results = []
        keys_iterator = iter(keys)
        datapoints_iterator = iter(datapoints)
        try:
            datapoint = next(datapoints_iterator)
            # path = datapoint[0]
        except StopIteration:
            datapoint = None
        prev_key = None
        try:
            key = self.as_account(next(keys_iterator))
        except StopIteration:
            key = None
        try:
            while datapoint and key:
                if not results or not self.equals(results[-1], key):
                    results += [key]
                if self.before_account(datapoint, key):
                    # This condition should never hold as datapoints' keys
                    # are a subset of keys, correct?
                    raise RuntimeError("Impossibility for "\
                      " before_account(datapoint=%s, key=%s)."\
                      " Maybe datapoints and/or keys are not sorted properly."
                      % (datapoint, key))
                if self.after_account(datapoint, key):
                    prev_key = key
                    key = None
                    key = self.as_account(next(keys_iterator))
                    if prev_key and prev_key == key:
                        raise RuntimeError(
                            "We have a duplicate key for %s" % str(key))
                else:
                    # equals
                    account = results[-1]
                    if (key.get('reporting_status') in
                        EngagementSerializer.REPORTING_ACCESSIBLE_ANSWERS):
                        self.add_datapoint(account, datapoint)
                    try:
                        datapoint = next(datapoints_iterator)
                    except StopIteration:
                        datapoint = None
        except StopIteration:
            pass
        # We should have gone through all the datapoints since their
        # keys are a subset of `keys`.
        assert datapoint is None
        try:
            while key:
                if not results or not self.equals(results[-1], key):
                    results += [key]
                prev_key = key
                key = self.as_account(next(keys_iterator))
                if prev_key and prev_key == key:
                    raise RuntimeError(
                        "We have a duplicate key for %s" % str(key))
        except StopIteration:
            pass
        assert len(results) == len(keys)
        return results


    def merge_tabularized(self, orig_tab, tab, path=""):
        for orig_account, account in zip(orig_tab, tab):
            for orig_key, orig_val in orig_account.items():
                if orig_key == 'score':
                    continue
                val = account.get(orig_key)
                if False and orig_val and val and (orig_val != val):
                    LOGGER.debug("[%s] value for key '%s' differs (%s vs %s)",
                        path, orig_key, orig_val, val)
                if not orig_val and val:
                    orig_account[orig_key] = val


    def format_row(self, entry, key=None):
        row = [self._get_title(entry)]
        slug = entry.get('slug')
        by_accounts = self.by_paths.get(slug)
        if by_accounts:
            for account in by_accounts:
                row += [account.get(key, "")]
            row += [slug]
        return row

    def get_answers_by_paths(self, latest_samples):
        answers_by_paths = {}
        question_clause = ""
        if self.kwargs.get('path'):
            question_clause = ("WHERE survey_question.path ILIKE '/%s%%'"
                % self.kwargs.get('path'))
        if self.requested_accounts:
            reporting_answers_sql = """
WITH samples AS (
    %(latest_assessments)s
),
answers AS (
SELECT
    survey_question.path,
    samples.account_id,
    survey_answer.measured,
    survey_answer.unit_id,
    survey_question.default_unit_id,
    survey_unit.title
FROM survey_answer
INNER JOIN survey_question
  ON survey_answer.question_id = survey_question.id
INNER JOIN samples
  ON survey_answer.sample_id = samples.id
INNER JOIN survey_unit
  ON survey_answer.unit_id = survey_unit.id
%(question_clause)s
)
SELECT
  answers.path,
  answers.account_id,
  answers.measured,
  answers.unit_id,
  answers.default_unit_id,
  answers.title,
  survey_choice.text
FROM answers
LEFT OUTER JOIN survey_choice
  ON survey_choice.unit_id = answers.unit_id AND
     survey_choice.id = answers.measured
ORDER BY answers.path, answers.account_id
""" % {
            'latest_assessments': latest_samples.query.sql,
            'question_clause': question_clause
        }
            if self.campaign != self.verified_campaign:
                # When we are downloading the answers for a verification
                # campaign, we run the same query as previously, except we
                # add an indirection through `djaopsp_verifiedsample` to find
                # the account the verification answers apply to (otherwise
                # we would set the verifier account as a column label).
                reporting_answers_sql = """
WITH latest_samples AS (
    %(latest_assessments)s
),
samples AS (
SELECT survey_sample.id,
 survey_sample.slug,
 survey_sample.created_at,
 survey_sample.campaign_id,
 latest_samples.account_id AS account_id,
 survey_sample.is_frozen,
 survey_sample.extra,
 survey_sample.updated_at
FROM survey_sample
INNER JOIN djaopsp_verifiedsample
ON djaopsp_verifiedsample.verifier_notes_id = survey_sample.id
INNER JOIN latest_samples
ON djaopsp_verifiedsample.sample_id = latest_samples.id
WHERE djaopsp_verifiedsample.verified_status >= 2
),
answers AS (
SELECT
    survey_question.path,
    samples.account_id,
    survey_answer.measured,
    survey_answer.unit_id,
    survey_question.default_unit_id,
    survey_unit.title
FROM survey_answer
INNER JOIN survey_question
  ON survey_answer.question_id = survey_question.id
INNER JOIN samples
  ON survey_answer.sample_id = samples.id
INNER JOIN survey_unit
  ON survey_answer.unit_id = survey_unit.id
%(question_clause)s
)
SELECT
  answers.path,
  answers.account_id,
  answers.measured,
  answers.unit_id,
  answers.default_unit_id,
  answers.title,
  survey_choice.text
FROM answers
LEFT OUTER JOIN survey_choice
  ON survey_choice.unit_id = answers.unit_id AND
     survey_choice.id = answers.measured
ORDER BY answers.path, answers.account_id
""" % {
            'latest_assessments': latest_samples.query.sql,
            'question_clause': question_clause
        }

            # XXX should still print questions if no accounts.
            with connection.cursor() as cursor:
                cursor.execute(reporting_answers_sql, params=None)
                prev_path = None
                chunk = []
                for row in cursor:
                    # The SQL quesry is ordered by `path` so we can build
                    # the final result by chunks, path by path.
                    path = row[0]
                    if prev_path and path != prev_path:
                        # flush
                        tab = self.tabularize(
                            chunk, self.accounts_with_engagement)
                        prev_slug = prev_path.split('/')[-1] # XXX slug
                        if prev_slug in answers_by_paths:
                            self.merge_tabularized(
                                answers_by_paths[prev_slug], tab,
                                path=prev_slug)
                        else:
                            answers_by_paths.update({prev_slug: tab})
                        chunk = []
                        self._report_queries("tabularized %s" % prev_path)
                    chunk += [row]
                    prev_path = path
                if chunk:
                    tab = self.tabularize(
                        chunk, self.accounts_with_engagement)
                    prev_slug = prev_path.split('/')[-1] # XXX slug
                    if prev_slug in answers_by_paths:
                        self.merge_tabularized(
                            answers_by_paths[prev_slug], tab,
                            path=prev_slug)
                    else:
                        answers_by_paths.update({prev_slug: tab})
                    self._report_queries("tabularized %s" % prev_slug)
        return answers_by_paths

    def get(self, request, *args, **kwargs):
        #pylint: disable=unused-argument,too-many-locals

        # We need to run `get_queryset` before `get_headings` so we know
        # how many columns to display for implementation rate.
        self._start_time()
        queryset = self.get_queryset()
        self._report_queries("built list of questions")
        if self.show_planned:
            self.write_sheet(title="Planned", key='planned', queryset=queryset)
        else:
            self.write_sheet(title="Answers", key='measured', queryset=queryset)
            if self.show_comments:
                self.write_sheet(title="Comments", key='comments',
                    queryset=queryset)

        resp = HttpResponse(self.flush_writer(), content_type=self.content_type)
        resp['Content-Disposition'] = \
            'attachment; filename="{}"'.format(self.get_filename())
        return resp


    def write_headers(self):
        """
        Write table headers in the worksheet
        """
        ends_at = self.ends_at.date()
        source = "Source: %s" % self.request.build_absolute_uri(location='/')
        if not self.start_at:
            self.writerow(["Organization/profiles engaged to %s (%s)" % (
                ends_at.isoformat(), source)])
        else:
            start_at = self.start_at.date()
            self.writerow(["Organization/profiles engaged from %s to %s (%s)" %
                (start_at.isoformat(), ends_at.isoformat(), source)])
        headings = [force_str(_("Organization/profile name"))] + [
            reporting.printable_name
            for reporting in self.accounts_with_engagement]
        self.writerow(headings)
        headings = [force_str(_("Organization/profile uniqueID"))] + [
            reporting.slug
            for reporting in self.accounts_with_engagement]
        self.writerow(headings)
        headings = [force_str(_("Tags"))]
        for reporting in self.accounts_with_engagement:
            tags = get_extra(reporting, 'tags')
            if tags:
                headings += [','.join(tags)]
            else:
                headings += [""]
        self.writerow(headings)

        # creates row with last completed date
        last_activity_at_by_accounts = {}
        for sample in self.latest_assessments:
            last_activity_at_by_accounts.update({
                sample.account_id: sample.created_at})
        headings = [force_str(_("Last completed at"))]
        reporting_status_strings = dict(EngagementSerializer.REPORTING_STATUSES)
        for reporting in self.accounts_with_engagement:
            account_id = reporting.pk
            last_activity_at = last_activity_at_by_accounts.get(account_id)
            if (reporting.reporting_status not in
                EngagementSerializer.REPORTING_ACCESSIBLE_ANSWERS):
                headings += [
                    reporting_status_strings[reporting.reporting_status]
                ]
            elif last_activity_at:
                headings += [datetime.date(
                    last_activity_at.year,
                    last_activity_at.month,
                    last_activity_at.day)]
            else:
                headings += [""]
        self.writerow(headings)


class CompareScoresXLSXView(CompareXLSXView):
    """
    Download a spreadsheet of scores with segments as rows and accounts
    as columns.
    """
    basename = 'scores'

    def get(self, request, *args, **kwargs):
        #pylint: disable=unused-argument,too-many-locals

        # We need to run `get_queryset` before `get_headings` so we know
        # how many columns to display for implementation rate.
        self._start_time()
        queryset = self.get_queryset()
        self._report_queries("built list of questions")


        # XXX uncoment to print detail scores on each question.
        # self.write_sheet(title="Scores", key='score',
        #    queryset=queryset)
        self.create_writer("Scores")
        self.write_headers()
        for entry in self.segments_available:
            row = [self._get_title(entry)]
            slug = entry.get('slug')

            scores = ScorecardCache.objects.filter(
                sample__in=self.latest_assessments,
                path=entry['path']).order_by('sample__account_id').values_list(
                'pk', 'sample__account_id', 'normalized_score')
            tab = self.tabularize([(val[0], val[1], val[2],
                self.points_unit.pk, self.points_unit.pk, None, "")
                for val in scores], self.accounts_with_engagement)

            for item, reporting in zip(tab, self.accounts_with_engagement):
                if (reporting.reporting_status not in
                    EngagementSerializer.REPORTING_ACCESSIBLE_ANSWERS):
                    row += [""]
                else:
                    row += [item.get('measured', "")]

            row += [slug]
            self.writerow(row)
        self._report_queries("written sheet 'Scores'")

        resp = HttpResponse(self.flush_writer(), content_type=self.content_type)
        resp['Content-Disposition'] = \
            'attachment; filename="{}"'.format(self.get_filename())
        return resp
