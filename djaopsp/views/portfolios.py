# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import datetime, io, json, logging, os, re
from collections import OrderedDict

from dateutil.relativedelta import relativedelta
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import datetime_or_now, update_context_urls
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.generic.base import (ContextMixin, RedirectView,
    TemplateResponseMixin, TemplateView)
from openpyxl import Workbook
from pages.mixins import TrailMixin
from pages.models import PageElement
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.shapes.autoshape import Shape
from pptx.shapes.graphfrm import GraphicFrame
from survey.helpers import get_extra
from survey.models import Campaign, Matrix
from survey.mixins import CampaignMixin
from survey.utils import get_question_model
from survey.views.matrix import MatrixDetailView

from ..compat import reverse, six
from ..helpers import as_valid_sheet_title
from ..api.portfolios import SupplierListMixin
from ..api.serializers import AccountSerializer
from ..mixins import AccountMixin
from ..utils import get_segments_candidates


LOGGER = logging.getLogger(__name__)


class DashboardRedirectView(AccountMixin, TemplateResponseMixin, ContextMixin,
                            RedirectView):
    """
    Redirects to the latest scorecard page
    """
    template_name = 'app/reporting/redirects.html'
    breadcrumb_url = 'reporting'

    @property
    def dashboards_available(self):
        """
        Returns a list of campaign dashboards available to the request user.
        """
        if not hasattr(self, '_dashboards_available'):
            filtered_in = Q(account__slug=self.account)
            for visible in set(['public']):
                filtered_in |= Q(extra__contains=visible)
            self._dashboards_available = Campaign.objects.filter(filtered_in)
        return self._dashboards_available

    def get_redirect_url(self, *args, **kwargs):
        return reverse(self.breadcrumb_url, kwargs=kwargs)

    def get(self, request, *args, **kwargs):
        candidates = self.dashboards_available
        if not candidates:
            raise Http404("No campaign available")

        if len(candidates) > 1:
            redirects = []
            for campaign in candidates:
                kwargs.update({'campaign': campaign})
                url = self.get_redirect_url(*args, **kwargs)
                print_name = campaign.title
                redirects += [(url, print_name, campaign.slug)]

            context = self.get_context_data(**kwargs)
            context.update({
                'redirects': redirects,
            })
            return self.render_to_response(context)

        kwargs.update({'campaign': candidates[0]})
        return super(DashboardRedirectView, self).get(request, *args, **kwargs)


class DashboardMixin(TrailMixin, CampaignMixin, AccountMixin):

    def get_context_data(self, **kwargs):
        context = super(DashboardMixin, self).get_context_data(**kwargs)
        update_context_urls(context, {
            # reporting dashboards menu items
            'portfolio_responses': reverse(
                'portfolio_responses', args=(self.account, self.campaign)),
            'reporting_organization_dashboard': reverse(
                'reporting_organization_dashboard', args=(
                self.account, self.campaign)),
            'matrix_chart': reverse(
                'matrix_chart', args=(self.account, self.campaign, 'totals')),
        })
        return context


class ActiveReportingEntitiesView(DashboardMixin, TemplateView):

    template_name = 'app/reporting/active.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expires_at = datetime_or_now('2021-09-01')
        context.update({
            'expires_at': expires_at
        })
        update_context_urls(context, {
            'api_active_reporting_entities': site_url(
                '/api/profile/%s/subscribers/engaged' % self.account),
            'api_inactive_reporting_entities': site_url(
                '/api/profile/%s/subscribers/unengaged' % self.account),
            'api_organizations': site_url("/api/profile/"),
        })
        return context


class PortfolioResponsesView(DashboardMixin, TemplateView):
    """
    Tracking requested reports
    """
    template_name = 'app/reporting/index.html'

    def get_template_names(self):
        candidates = ['app/reporting/%s.html' % self.campaign]
        candidates += list(super(
            PortfolioResponsesView, self).get_template_names())
        return candidates

    def get_context_data(self, **kwargs):
        context = super(PortfolioResponsesView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_accessibles': site_url(
                "/api/profile/%(account)s/plans/%(account)s-report/"\
                "subscriptions/" % {'account': self.account}),
            'api_account_candidates': site_url("/api/profile/"),
            'api_organizations': site_url("/api/profile/"),
            'api_organization_profile': site_url(
                "/api/profile/%(account)s/" % {'account': self.account}),

            'api_portfolio_responses': reverse('api_portfolio_responses',
                args=(self.account, self.campaign)),
            'download': reverse('portfolio_responses_download',
                args=(self.account, self.campaign)),
            'download_raw': reverse('portfolio_responses_download_raw',
                args=(self.account, self.campaign)),
        })
        start_at = get_extra(self.account, 'start_at', None)
        context.update({
            'account_extra': self.account.extra,
            'start_at': start_at,
            'ends_at': (datetime_or_now() + relativedelta(days=1)).isoformat(),
        })
        return context


class PortfolioResponsesXLSXView(SupplierListMixin, TemplateView):
    """
    Download scores of all reporting entities as an Excel spreadsheet.
    """
    content_type = \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    basename = 'dashboard'

    headings = OrderedDict([
        ('printable_name', 'Supplier name'),
        ('categories', 'Categories'),
        ('contact_name', 'Contact name'),
        ('email', 'Contact email'),
        ('phone', 'Contact phone'),
        ('last_activity_at', 'Last activity'),
        ('reporting_status', 'Status'),
        ('last_completed_at', 'Last completed'),
        ('segment', 'Industry segment'),
        ('normalized_score', 'Score'),
        ('nb_na_answers', '# N/A'),
        ('reporting_publicly', 'Reporting publicly'),
        ('reporting_fines', 'Environmental fines'),
        ('nb_planned_improvements', '# Planned actions'),

        ('reporting_energy_consumption', 'Energy measured'),
        ('reporting_ghg_generated', 'GHG Emissions measured'),
        ('reporting_water_consumption', 'Water measured'),
        ('reporting_waste_generated', 'Waste measured'),
        ('reporting_energy_target', 'Energy targets'),
        ('reporting_ghg_target', 'GHG Emissions targets'),
        ('reporting_water_target', 'Water targets'),
        ('reporting_waste_target', 'Waste targets'),
    ])

    def get_headings(self):
        return self.headings

    @staticmethod
    def get_indent_bestpractice(depth=0):
        return "  " * depth

    @staticmethod
    def get_indent_heading(depth=0):
        return "  " * depth

    def get_filename(self):
        return datetime_or_now().strftime(
            self.account.slug + '-' + self.basename + '-%Y%m%d.xlsx')

    def _writerecord(self, rec, categories, last_activity_at, reporting_status,
                     last_completed_at, report_to):
        #pylint:disable=too-many-arguments,too-many-locals
        row = []
        for field_name in self.headings:
            if field_name == 'categories':
                val = categories
            elif field_name in (
                    'printable_name', 'contact_name', 'email', 'phone',
                    'last_activity_at', 'reporting_status'):
                if field_name == 'reporting_status':
                    val = reporting_status
                elif field_name == 'last_activity_at':
                    val = last_activity_at
                else:
                    val = getattr(rec, field_name)
            else:
                val = 'Requested'
                if not rec.requested_at:
                    if (last_completed_at and
                        field_name in ('reporting_publicly', 'reporting_fines',
                        'reporting_energy_consumption',
                        'reporting_ghg_generated',
                        'reporting_water_consumption',
                        'reporting_waste_generated',
                        'reporting_energy_target',
                        'reporting_ghg_target',
                        'reporting_water_target',
                        'reporting_waste_target')):
                        val = ("Yes" if getattr(rec, field_name) else "No")
                    elif field_name == 'last_completed_at':
                        val = last_completed_at
                    else:
                        val = getattr(rec, field_name)
            row += [val]
        if not rec.contact_name:
            LOGGER.warning("supplier '%s', contact e-mail '%s' not found!",
                rec.printable_name, rec.email)
        self.wsheet.append(row)

    def writerow(self, rec, headings=None):
        last_activity_at = rec.last_activity_at
        if last_activity_at and isinstance(last_activity_at, datetime.datetime):
            last_activity_at = last_activity_at.strftime("%Y-%m-%d")
        reporting_status = rec.reporting_status
        if reporting_status < len(AccountSerializer.REPORTING_STATUS):
            reporting_status = (
                AccountSerializer.REPORTING_STATUS[reporting_status][1])
        else:
            reporting_status = ""
        last_completed_at = rec.last_completed_at
        if last_completed_at and isinstance(last_completed_at,
                                            datetime.datetime):
            last_completed_at = last_completed_at.strftime("%Y-%m-%d")
        extra = rec.extra if hasattr(rec, 'extra') else None
        if extra and isinstance(extra, six.string_types):
            try:
                extra = json.loads(extra)
            except (TypeError, ValueError):
                extra = {}
        categories = ','.join(extra.keys()) if extra else ""
        if headings:
            self._writerecord(rec, categories, last_activity_at,
                reporting_status, last_completed_at)
        else:
#            reports_to = rec.reports_to if hasattr(rec, 'reports_to') else [(
#                self.account.slug, self.account.full_name)]
            reports_to = [(self.account.slug, self.account.full_name)]
            for rep in reports_to:
                report_to = "" if rep[0] == self.account.slug else rep[1]
                self._writerecord(rec, categories, last_activity_at,
                    reporting_status, last_completed_at,
                    report_to=report_to)
                segment_slug = None
                if segment_slug:
                    if segment_slug not in self.suppliers_per_segment:
                        self.suppliers_per_segment[segment_slug] = set(
                            [])
                    self.suppliers_per_segment[segment_slug] |= set(
                        [rec['slug']])

    def get(self, request, *args, **kwargs):
        #pylint: disable=unused-argument
        self._start_time()
        wbook = Workbook()

        # Populate the Total sheet
        self.wsheet = wbook.active
        self.wsheet.title = as_valid_sheet_title("Suppliers invited to TSP")
        self.wsheet.append(["Utility member", self.account.full_name])
        contact_model = get_user_model()
        contact_name = ""
        try:
            contact = contact_model.objects.get(
                email__iexact=self.account.email)
            contact_name = contact.get_full_name()
        except contact_model.DoesNotExist:
            LOGGER.warning("member '%s', contact e-mail '%s' not found!",
                self.account.full_name, self.account.email)
        self.wsheet.append(["Utility contact name", contact_name])
        self.wsheet.append(["Utility contact email", self.account.email])
        self.wsheet.append(["Utility contact phone", self.account.phone])
        self.wsheet.append([])
        self.wsheet.append(list(six.itervalues(self.headings)))

        queryset = self.get_queryset()
        self.decorate_queryset(queryset)
        for account in queryset:
            self.writerow(account)

        # Prepares the result file
        content = io.BytesIO()
        wbook.save(content)
        content.seek(0)

        resp = HttpResponse(content, content_type=self.content_type)
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())
        self._report_queries("http response created")
        return resp


class PortfolioResponsesRawXLSXView(SupplierListMixin, TemplateView):
    """
    Download detailed answers of each suppliers
    """
    content_type = \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    basename = 'dashboard-assessments'

    indent_step = '    '
    show_comments = False
    show_planned = False

    @property
    def query_supply_chain(self):
        return False

    @staticmethod
    def _get_consumption(element):
        return element.get('consumption', None)

    @staticmethod
    def _get_tag(element):
        return element.get('tag', "")

    @staticmethod
    def _get_title(element):
        return element.get('title', "")

    def writerow(self, row, leaf=False):
        #pylint:disable=unused-argument
        self.wsheet.append(row)

    def write_tree(self, root, indent=''):
        """
        The *root* parameter looks like:
        (PageElement, [(PageElement, [...]), (PageElement, [...]), ...])
        """
        if not root[1]:
            # We reached a leaf
            row = [indent + self._get_title(root[0])]
            path = root[0]['path'].split('/')[-1] # XXX slug
            by_accounts = self.by_paths.get(path)
            if by_accounts:
                for account_id, reporting in self.accounts_with_response:
                    if reporting.grant_key:
                        row += [""]
                        if self.show_comments:
                            row += [""]
                    else:
                        answer = by_accounts[account_id]
                        measured = answer['measured']
                        if measured and self.show_planned:
                            measured = 'X'
                        row += [measured]
                        if self.show_comments:
                            row += [answer['comments']]
            self.writerow(row, leaf=True)
        else:
            self.writerow([indent + self._get_title(root[0])])
            for element in six.itervalues(root[1]):
                self.write_tree(element, indent=indent + self.indent_step)

    def get_latest_samples(self, from_root):
        return get_question_model().objects.get_latest_samples_by_prefix(
            before=self.ends_at, prefix=from_root)

    def get_tiles(self):
        """
        Returns a list of tiles that will be used as roots for the rows
        in the spreadsheet.
        """
        from_root, trail = self.breadcrumbs
        if from_root:
            segments = [{
                'title': trail[-1][0].title, 'path': from_root, 'indent': 0}]
        else:
            segments = get_segments_candidates(self.campaign)
        tiles = []
        for segment in segments:
            path = segment['path']
            if path:
                slug = path.split('/')[-1]
                segment_tiles = PageElement.objects.filter(
                    to_element__orig_element__slug=slug).order_by(
                    'to_element__rank')
                insert_point = None
                for segment_tile in segment_tiles:
                    found = None
                    for index, tile in enumerate(tiles):
                        if segment_tile.title == tile.title:
                            found = index
                            break
                    if found is not None:
                        insert_point = found + 1
                    else:
                        if insert_point:
                            tiles = (tiles[:insert_point] + [segment_tile] +
                                tiles[insert_point:])
                            insert_point = insert_point + 1
                        else:
                            tiles = tiles + [segment_tile]
        return tiles

    def get(self, request, *args, **kwargs):
        #pylint:disable=too-many-statements,too-many-locals
        latest_assessments = self.get_latest_samples(self.db_path)
        reporting_answers_sql = """
WITH samples AS (
    %(latest_assessments)s
),
answers AS (SELECT
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
WHERE samples.account_id IN %(accounts)s)
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
""" % {
            'latest_assessments': latest_assessments,
            'accounts': self.requested_accounts_pk_as_sql
        }
        self.by_paths = {}
        accounts_with_response = set([])
        if self.requested_accounts:
            with connection.cursor() as cursor:
                cursor.execute(reporting_answers_sql, params=None)
                for row in cursor:
                    path = row[0].split('/')[-1] # XXX slug
                    account_id = row[1]
                    measured = row[2]
                    unit_id = row[3]
                    default_unit_id = row[4]
                    #XXX unit_title = row[5]
                    text = row[6]
                    if path not in self.by_paths:
                        by_accounts = OrderedDict()
                        for account in self.requested_accounts_pk:
                            by_accounts[account] = {
                                'measured': "", 'comments': ""}
                        self.by_paths[path] = by_accounts
                    if measured:
                        accounts_with_response |= set([account_id])
                    if unit_id == default_unit_id:
                        self.by_paths[path][account_id]['measured'] = (
                            text if text else measured)
                    else:
                        self.by_paths[path][account_id]['comments'] += str(
                            text if text else measured)

        # Use only accounts with a response otherwise we pick all suppliers
        # that are connected to a dashboard but not necessarly invited to
        # answer on a specific segment.
        # Here the code to get all suppliers, in case:
        # ```self.accounts_with_response = sorted(
        #    list(self.requested_accounts.items()),
        #    key=lambda val: val[1].organization.printable_name)```
        self.accounts_with_response = sorted([
            (account_id, self.requested_accounts[account_id])
            for account_id in accounts_with_response],
            key=lambda val: val[1].printable_name)

        # Populate the worksheet
        wbook = Workbook()
        self.wsheet = wbook.active
        self.wsheet.title = as_valid_sheet_title("Answers")
        headings = [''] + [reporting.printable_name
            for account_id, reporting in self.accounts_with_response]
        self.wsheet.append(headings)

        by_accounts = OrderedDict()
        for account in self.requested_accounts_pk:
            by_accounts[account] = ""
        with connection.cursor() as cursor:
            cursor.execute(latest_assessments, params=None)
            for sample in cursor:
                last_activity_at = sample[2]
                account_id = sample[4]
                by_accounts[account_id] = last_activity_at
        headings = ['Last completed at']
        for account_id, reporting in self.accounts_with_response:
            last_activity_at = by_accounts.get(account_id)
            if reporting.grant_key:
                headings += ["Requested"]
            elif last_activity_at:
                headings += [last_activity_at.strftime("%Y-%m-%d")]
            else:
                headings += [""]
            if self.show_comments:
                headings += ["Comments"]
        self.wsheet.append(headings)

        # We use cut=None here so we print out the full assessment
        root = self._build_tree(self.get_tiles(), self.db_path, cut=None)

        indent = ''
        for nodes in six.itervalues(root[1]):
            self.writerow([self._get_title(nodes[0])])
            for elements in six.itervalues(nodes[1]):
                self.write_tree(elements, indent=indent + self.indent_step)

        # Prepares the result file
        content = io.BytesIO()
        wbook.save(content)
        content.seek(0)

        resp = HttpResponse(content, content_type=self.content_type)
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())
        return resp

    def get_filename(self):
        return datetime_or_now().strftime(
            self.account.slug + '-' + self.basename + '-%Y%m%d.xlsx')


class ReportingDashboardView(DashboardMixin, TemplateView):

    template_name = 'app/reporting/dashboard/index.html'

    default_ends_at = '2022-01-01'

    def get_template_names(self):
        candidates = ['app/reporting/dashboard/%s.html' % self.campaign]
        candidates += list(super(
            ReportingDashboardView, self).get_template_names())
        return candidates

    def get_context_data(self, **kwargs):
        context = super(ReportingDashboardView, self).get_context_data(**kwargs)
        context.update({
            'ends_at': datetime_or_now(self.default_ends_at).isoformat()
        })
        update_context_urls(context, {
            'api_active_reporting_entities': site_url(
                '/api/profile/%s/subscribers/engaged' % self.account),
            'active_reporting_entities': reverse(
                'active_reporting_entities', args=(
                self.account, self.campaign)),

            'api_reporting_completion_rate': reverse(
                'api_reporting_completion_rate', args=(
                self.account, self.campaign)),
            'api_reporting_goals': reverse(
                'api_reporting_goals', args=(
                self.account, self.campaign)),
            'api_reporting_by_segments': reverse(
                'api_reporting_by_segments', args=(
                self.account, self.campaign)),
            'api_reporting_ghg_emissions_rate': reverse(
                'api_reporting_ghg_emissions_rate', args=(
                self.account, self.campaign)),
            'api_reporting_ghg_emissions_amount': reverse(
                'api_reporting_ghg_emissions_amount', args=(
                self.account, self.campaign)),
            'download_completion_rate': reverse(
                'reporting_download_completion_rate', args=(
                self.account, self.campaign)),
            'download_goals': reverse(
                'reporting_download_goals', args=(self.account, self.campaign)),
            'download_by_segments': reverse(
                'reporting_download_by_segments', args=(
                self.account, self.campaign)),
            'download_ghg_emissions_rate': reverse(
                'reporting_download_ghg_emissions_rate', args=(
                self.account, self.campaign)),
            'download_ghg_emissions_amount': reverse(
                'reporting_download_ghg_emissions_amount', args=(
                self.account, self.campaign)),
        })
        return context


class ReportingHistoricalView(DashboardMixin, TemplateView):

    template_name = 'app/reporting/historical.html'

    default_ends_at = '2022-01-01'

    def get_context_data(self, **kwargs):
        context = super(
            ReportingHistoricalView, self).get_context_data(**kwargs)
        context.update({
            'ends_at': datetime_or_now(self.default_ends_at).isoformat()
        })
        update_context_urls(context, {
            'api_reporting_invited_by_plans': reverse(
                'api_reporting_invited_by_plans', args=(self.account,)),
            'api_reporting_shared_profiles': reverse(
                'api_reporting_shared_profiles', args=(self.account,)),
            'api_reporting_alltime': reverse(
                'api_reporting_alltime', args=(self.account,)),
        })
        return context




class PortfoliosDetailView(DashboardMixin, MatrixDetailView):

    matrix_url_kwarg = 'path'

    def get_reverse_kwargs(self):
        return super(PortfoliosDetailView, self).get_reverse_kwargs() + [
            'campaign']

    def get_available_matrices(self):
        return Matrix.objects.filter(account=self.account)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        candidate = self.kwargs.get(self.matrix_url_kwarg)
        candidate = candidate.lstrip(self.URL_PATH_SEP)
        return get_object_or_404(queryset, slug=candidate)

    def get_context_data(self, **kwargs):
        #pylint:disable=too-many-locals,too-many-statements
        context = super(PortfoliosDetailView, self).get_context_data(**kwargs)
        try:
            segment_prefix = self.full_path
            segment_element = self.element
            root = self.get_scores_tree(
                [segment_element], root_prefix=segment_prefix)
            root = root[1].get(segment_prefix)
            self.decorate_with_breadcrumbs(root)
            # Remove sgement chart that would otherwise be added.
            charts = self.get_charts(root, excludes=[segment_element.slug])
        except Http404:
            # With have a matrix but not corresponding PageElement (ex: totals).
            charts = []
            segments = set([])
            for extra in self.account_queryset.filter(
                    subscribes_to__slug='%s-report' % self.account).values(
                        'extra'):
                try:
                    extra = extra.get('extra')
                    if extra:
                        extra = json.loads(extra.replace("'", '"'))
                        segments |= set([extra.get('industry')])
                except (IndexError, TypeError, ValueError) as _:
                    pass
            flt = None
            for segment in segments:
                if flt is None:
                    flt = Q(slug__startswith=segment)
                else:
                    flt |= Q(slug__startswith=segment)
            if True: #pylint:disable=using-constant-test
                # XXX `flt is None:` not matching the totals columns
                queryset = self.object.cohorts.all()
            else:
                queryset = self.object.cohorts.filter(flt)
            for cohort in queryset.order_by('title'):
                candidate = cohort.slug
                look = re.match(r"(\S+)(-\d+)$", candidate)
                if look:
                    candidate = look.group(1)
                element = PageElement.objects.filter(slug=candidate).first()
                charts += [{
                    'slug': cohort.slug,
                    'breadcrumbs': [cohort.title],
                    'picture': element.text if element is not None else "",
                    'icon_css': 'orange'
                }]
            charts = []
        url_kwargs = self.get_url_kwargs()
        url_kwargs.update({self.matrix_url_kwarg: self.object})
        for chart in charts:
            candidate = chart['slug']
            look = re.match(r"(\S+)(-\d+)$", candidate)
            if look:
                matrix_slug = '/'.join([look.group(1)])
            else:
                matrix_slug = '/'.join([str(self.object), candidate])
            url_kwargs.update({self.matrix_url_kwarg: matrix_slug})
            api_urls = {'matrix_api': reverse('matrix_api', kwargs=url_kwargs)}
            chart.update({'urls': api_urls})

        context.update({
            'available_matrices': self.get_available_matrices(),
            'charts': charts
        })
        return context


class ReportingDashboardPPTXView(DashboardMixin, TemplateView):
    """
    Download reporting dashboard as an .pptx spreadsheet.
    """
    content_type = \
     'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    basename = 'dashboard'

    def get_filename(self):
        return datetime_or_now().strftime(
            self.account.slug + '-' + self.basename + '-%Y%m%d.pptx')

    def get(self, request, *args, **kwargs):
        #pylint: disable=unused-argument,too-many-locals,too-many-nested-blocks

        # Prepares the result file
        content = io.BytesIO()
        candidate = None
        for template_dir in settings.TEMPLATES_DIRS:
            candidate = os.path.join(template_dir,
                'envconnect', 'reporting', '%s.pptx' % self.basename)
            if os.path.exists(candidate):
                break
        if candidate:
            data = self.get_response_data(request, *args, **kwargs)
            with open(candidate, 'rb') as reporting_file:
                prs = Presentation(reporting_file)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if isinstance(shape, Shape):
                        if (self.defaults_to_percent and
                            shape.text == "(nb suppliers)"):
                            shape.text = "(% of suppliers)"
                        if shape.text.startswith("(outer: member"):
                            alliance = "Alliance"
                            series = data.get('table', [])
                            if len(series) > 1:
                                alliance = series[-1].get('key', alliance)
                            shape.text = "(outer: %s, inner: %s)" % (
                                self.account.printable_name, alliance)
                    elif isinstance(shape, GraphicFrame):
                        # We found the chart's container
                        try:
                            chart = shape.chart
                            chart_data = CategoryChartData()
                            labels = False
                            for serie in data.get('table', []):
                                if not labels:
                                    for point in serie.get('values'):
                                        label = point[0]
                                        if isinstance(label, datetime.datetime):
                                            label = label.date()
                                        chart_data.add_category(label)
                                    labels = True
                                chart_data.add_series(
                                serie.get('key'),
                                    [point[1] for point in serie.get('values')])

                            chart.replace_data(chart_data)
                        except ValueError:
                            pass
            prs.save(content)
        content.seek(0)

        resp = HttpResponse(content, content_type=self.content_type)
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())

        return resp
