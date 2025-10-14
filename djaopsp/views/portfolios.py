# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.

import io, json, logging, re

from deployutils.apps.django_deployutils.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.generic.base import (ContextMixin, RedirectView,
    TemplateResponseMixin, TemplateView)
from openpyxl import Workbook
from pages.mixins import TrailMixin
from pages.models import PageElement
from survey.helpers import datetime_or_now, extra_as_internal, get_extra
from survey.models import Campaign, Matrix
from survey.settings import URL_PATH_SEP
from survey.views.matrix import MatrixDetailView

from ..api.portfolios import CompletedAssessmentsMixin
from ..api.rollups import GraphMixin
from ..compat import reverse
from ..helpers import as_valid_sheet_title
from ..mixins import (AccountsAggregatedQuerysetMixin,
    DashboardsAvailableQuerysetMixin)
from ..models import VerifiedSample
from ..utils import get_scores_tree

LOGGER = logging.getLogger(__name__)


class DashboardRedirectView(DashboardsAvailableQuerysetMixin,
                            TemplateResponseMixin, ContextMixin,
                            RedirectView):
    """
    Redirects to the latest scorecard page
    """
    template_name = 'app/reporting/redirects.html'
    breadcrumb_url = 'portfolio_engage'

    def get_redirect_url(self, *args, **kwargs):
        return reverse(self.breadcrumb_url, kwargs=kwargs)

    def get_template_names(self):
        if self.account in self.verifier_accounts:
            # Dashboard looks quite different for the broker.
            return 'app/reporting/broker.html'
        return super(DashboardRedirectView, self).get_template_names()

    def get(self, request, *args, **kwargs):
        if self.account in self.verifier_accounts:
            # Dashboard looks quite different for broker
            # and verification partners.
            context = self.get_context_data(**kwargs)
            update_context_urls(context, {
                'profile_base': site_url("/activities/accounts/"),
                'api_accounts': site_url("/api/profile"),
                'api_users': site_url("/api/accounts/users"),
                'api_roles': site_url("/api/profile/%s/roles" % self.account),
                'api_reporting_completion_rate': reverse(
                    'api_verified_aggregate', args=(self.account,)),
                'api_portfolio_responses': reverse(
                    'api_completed_assessments', args=(self.account,)),
                'api_organizations': site_url("/api/profile"),
                'download': reverse(
                    'completed_assessments_download', args=(self.account,))
            })
            return self.render_to_response(context)

        candidates = self.dashboards_available
        if not candidates:
            raise Http404("No campaign available")

        if len(candidates) > 1:
            context = self.get_context_data(**kwargs)
            redirects = []
            redirect_kwargs = {}
            redirect_kwargs.update(kwargs)
            for campaign in candidates:
                redirect_kwargs.update({'campaign': campaign})
                url = self.get_redirect_url(*args, **redirect_kwargs)
                print_name = campaign.title
                redirects += [(url, print_name, campaign.slug)]
            context.update({'redirects': redirects})
            return self.render_to_response(context)

        kwargs.update({'campaign': candidates[0]})
        return super(DashboardRedirectView, self).get(request, *args, **kwargs)


class DashboardMixin(TrailMixin, AccountsAggregatedQuerysetMixin):

    def get_context_data(self, **kwargs):
        context = super(DashboardMixin, self).get_context_data(**kwargs)
        context.update({
            'ends_at': self.accounts_ends_at.isoformat(),
            'start_at': (self.accounts_start_at.isoformat()
                if self.accounts_start_at else None),
            'campaign': self.campaign
        })
        extra = extra_as_internal(self.account)
        if extra:
            context.update({
                'account_extra': json.dumps(extra),
            })
        return context


class MenubarMixin(object):

    def get_context_data(self, **kwargs):
        context = super(MenubarMixin, self).get_context_data(**kwargs)
        update_context_urls(context, {
            # reporting dashboards menu items
            'portfolio_responses': reverse(
                'portfolio_responses', args=(self.account, self.campaign)),
            #'reporting_organization_dashboard': reverse(
            #    'reporting_organization_dashboard', args=(
            #    self.account, self.campaign)),
            #'matrix_chart': reverse(
            #    'matrix_chart', args=(self.account, self.campaign, 'totals')),
        })
        return context


class UpdatedMenubarMixin(object):

    def get_context_data(self, **kwargs):
        context = super(UpdatedMenubarMixin, self).get_context_data(**kwargs)
        update_context_urls(context, {
            # reporting dashboards menu items
            'compare': reverse('matrix_compare',
                args=(self.account, self.campaign)),
            'engage': reverse('reporting_profile_engage',
                args=(self.account, self.campaign)),
            'accessibles': reverse('reporting_profile_accessibles',
                args=(self.account, self.campaign)),
            'insights': reverse(
                'reporting_organization_dashboard', args=(
                self.account, self.campaign)),
        })
        return context


class PortfolioAccessiblesView(UpdatedMenubarMixin, DashboardMixin,
                               TemplateView):
    """
    Lists yearly actvity for all profiles a report has either
    been requested from or granted by.

    When a report is pro-actively granted, a `granted` tag is added.
    Note though that accepting grants is done on the engagement dashboard.
    """
    template_name = 'app/reporting/accessibles/index.html'

    def get_template_names(self):
        campaign_slug = self.campaign.slug
        candidates = ['app/reporting/accessibles/%s.html' % campaign_slug]
        candidates += list(super(
            PortfolioAccessiblesView, self).get_template_names())
        return candidates

    def get_context_data(self, **kwargs):
        context = super(PortfolioAccessiblesView, self).get_context_data(
            **kwargs)
        context.update({'ends_at': None, 'start_at': None})
        update_context_urls(context, {
            'api_accessibles': reverse(
                'survey_api_portfolios_requests', args=(self.account,)),
            'api_account_candidates': site_url("/api/accounts/profiles"),
            'api_accounts': site_url("/api/profile"),
            'api_organizations': site_url("/api/profile"),
            'api_organization_profile': site_url(
                "/api/profile/%(account)s" % {'account': self.account}),
            'api_metadata': reverse(
                'survey_api_portfolio_metadata_index', args=(self.account,)),
            'api_portfolio_metadata': reverse(
                'survey_api_portfolio_metadata_index', args=(self.account,)),
            'api_portfolio_responses': reverse(
                'api_portfolio_accessible_samples',
                args=(self.account, self.campaign)),
            'download': reverse(
                'reporting_profile_accessibles_download',
                args=(self.account, self.campaign)),
            'download_long': reverse(
                'reporting_profile_accessibles_download_long',
                args=(self.account, self.campaign)),
            'download_raw': reverse(
                'download_accessibles_raw',
                args=(self.account, self.campaign)),
            'download_raw_long': reverse(
                'download_accessibles_raw_long',
                args=(self.account, self.campaign)),
            'help': site_url("/docs/guides/djaopsp/accessibles/")
        })
        if self.manages(self.account) or self.manages(settings.BROKER_NAME):
            update_context_urls(context, {
                'api_portfolios_received': reverse(
                    'survey_api_portfolios_received', args=(self.account,)),
            })
        try:
            verification_campaign = Campaign.objects.get(
                slug="%s-verified" % self.campaign)
            update_context_urls(context, {
                'download_verification': reverse(
                    'download_accessibles_raw', args=(
                        self.account, verification_campaign)),
                'download_verification_long': reverse(
                    'download_accessibles_raw_long', args=(
                        self.account, verification_campaign)),
            })
        except Campaign.DoesNotExist:
            pass
        return context


class PortfolioEngagementView(UpdatedMenubarMixin, DashboardMixin,
                              TemplateView):
    """
    Lists profiles that are currently part of an engagement effort.
    """
    template_name = 'app/reporting/engage/index.html'

    def get_context_data(self, **kwargs):
        context = super(PortfolioEngagementView, self).get_context_data(
            **kwargs)
        update_context_urls(context, {
            'api_activities_base': site_url("/api/activities"),
            'api_sample_base_url': reverse('survey_api_sample_list', args=(
                self.account,)),
            'api_accessibles': reverse(
                'survey_api_portfolios_requests', args=(self.account,)),
            'api_account_candidates': site_url("/api/accounts/profiles"),
            'api_profile': site_url("/api/profile/%s" % str(self.account)),
            'api_accounts': site_url("/api/profile"),
            'api_organizations': site_url("/api/profile"),
            'api_metadata': reverse(
                'survey_api_portfoliodoubleoptin_metadata_index',
                args=(self.account,)),
            'api_portfolio_metadata': reverse(
                'survey_api_portfolio_metadata_index', args=(self.account,)),
            'api_portfolios_requests': reverse(
                'api_portfolio_engagement', args=(
                self.account, self.campaign)),
            'api_portfolio_engagement_stats': reverse(
                'api_portfolio_engagement_stats', args=(
                self.account, self.campaign)),
            'api_reporting_completion_rate': reverse(
                'api_reporting_completion_rate', args=(
                self.account, self.campaign)),
            'download': reverse('reporting_profile_engage_download',
                args=(self.account, self.campaign)),
            'download_completion_rate': reverse(
                'reporting_download_completion_rate', args=(
                self.account, self.campaign)),
            'download_engagement_stats': reverse(
                'reporting_download_engagement_stats', args=(
                self.account, self.campaign)),
            'download_raw': reverse('download_matrix_compare',
                args=(self.account, self.campaign)),
            'download_raw_long': reverse('download_engage_raw_long',
                args=(self.account, self.campaign)),
            'help': site_url("/docs/guides/djaopsp/engage/")
        })
        try:
            verification_campaign = Campaign.objects.get(
                slug="%s-verified" % self.campaign)
            update_context_urls(context, {
                'download_verification': reverse(
                    'download_matrix_compare', args=(
                        self.account, verification_campaign)),
                'download_verification_long': reverse(
                    'download_engage_raw_long', args=(
                        self.account, verification_campaign)),
            })
        except Campaign.DoesNotExist:
            pass
        return context


class PortfolioResponsesView(MenubarMixin, DashboardMixin, TemplateView):
    """
    Manages engagement with requested reports
    """
    template_name = 'app/reporting/index.html'

    def get_template_names(self):
        campaign_slug = self.campaign.slug
        candidates = ['app/reporting/%s.html' % campaign_slug]
        candidates += list(super(
            PortfolioResponsesView, self).get_template_names())
        return candidates

    def get_context_data(self, **kwargs):
        context = super(PortfolioResponsesView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_accessibles': reverse(
                'survey_api_portfolios_requests', args=(self.account,)),
            'api_account_candidates': site_url("/api/accounts/profiles"),
            'api_organizations': site_url("/api/profile"),
            'api_organization_profile': site_url(
                "/api/profile/%(account)s" % {'account': self.account}),

            'api_portfolio_responses': reverse('api_portfolio_responses',
                args=(self.account, self.campaign)),
            'download': reverse('portfolio_responses_download',
                args=(self.account, self.campaign)),
            'download_raw': reverse('download_matrix_compare',
                args=(self.account, self.campaign)),
        })
        context.update({
            'account_extra': json.dumps(self.account.extra),
        })
        return context


class CompletedAssessmentsRawXLSXView(CompletedAssessmentsMixin, TemplateView):
    """
    Download all completed assessments
    """
    content_type = \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    basename = 'completed'

    def get(self, request, *args, **kwargs):
        # Populate the worksheet
        wbook = Workbook()
        #pylint:disable=attribute-defined-outside-init
        self.wsheet = wbook.active
        self.wsheet.title = as_valid_sheet_title("Completed")
        headings = ['Completed at', 'Name', 'Domain', 'Campaign',
            'Priority', 'Verified Status', 'Verifier']
        self.wsheet.append(headings)

        for rec in self.decorate_queryset(self.get_queryset()):
            domain = rec.email.split('@')[-1] if rec.email else ""
            priority = get_extra(rec.account, 'priority', 0)
            verified_status = (VerifiedSample.STATUSES[rec.verified_status]
                if rec.verified_status < len(VerifiedSample.STATUSES)
                else VerifiedSample.STATUSES[0])
            verified_by_full_name = (rec.verified_by.get_full_name()
                if rec.verified_by else "")
            self.wsheet.append([
                rec.last_completed_at.strftime('%Y/%m/%d'),
                rec.printable_name, domain, rec.segment,
                priority, verified_status[1], verified_by_full_name])

        # Prepares the result file
        content = io.BytesIO()
        wbook.save(content)
        content.seek(0)

        resp = HttpResponse(content, content_type=self.content_type)
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())
        return resp

    def get_filename(self):
        return "%s-%s.xlsx" % (self.basename,
            datetime_or_now().strftime('%Y%m%d'))


class ReportingDashboardView(UpdatedMenubarMixin, DashboardMixin, TemplateView):

    template_name = 'app/reporting/dashboard/index.html'

    def get_template_names(self):
        candidates = ['app/reporting/dashboard/%s.html' % self.campaign]
        candidates += list(super(
            ReportingDashboardView, self).get_template_names())
        return candidates

    def get_context_data(self, **kwargs):
        context = super(ReportingDashboardView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_benchmarks_index': reverse(
                'api_reporting_benchmarks_index', args=(
                self.account, self.campaign)),
            'api_reporting_completion_rate': reverse(
                'api_reporting_completion_rate', args=(
                self.account, self.campaign)),
            'api_portfolio_engagement_stats': reverse(
                'api_portfolio_engagement_stats', args=(
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
            'download': reverse('reporting_download_full_report', args=(
                self.account, self.campaign)),
            'download_completion_rate': reverse(
                'reporting_download_completion_rate', args=(
                self.account, self.campaign)),
            'download_engagement_stats': reverse(
                'reporting_download_engagement_stats', args=(
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


class PortfoliosDetailView(GraphMixin, MenubarMixin, DashboardMixin,
                           MatrixDetailView):

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
        candidate = candidate.lstrip(URL_PATH_SEP)
        return get_object_or_404(queryset, slug=candidate)

    def get_context_data(self, **kwargs):
        #pylint:disable=too-many-locals,too-many-statements
        context = super(PortfoliosDetailView, self).get_context_data(**kwargs)
        try:
            segment_prefix = self.full_path
            segment_element = self.element
            scores_tree = get_scores_tree(
                [segment_element], prefix=segment_prefix)
            # Remove sgement chart that would otherwise be added.
            charts = self.get_charts(
                scores_tree, excludes=[segment_element.slug])
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
                    'slug': element.slug,
                    'breadcrumbs': [cohort.title],
                    'picture': element.picture if element is not None else None,
                }]
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


class ByCampaignAccessiblesView(DashboardRedirectView):
    """
    Lists latest campaign response by accessible profiles.
    """
    template_name = 'app/reporting/index.html'

    def get_context_data(self, **kwargs):
        context = super(ByCampaignAccessiblesView, self).get_context_data(
            **kwargs)
        update_context_urls(context, {
            'api_portfolio_responses': reverse(
                'api_last_by_campaign_accessibles', args=(self.account,)),
        })
        return context
