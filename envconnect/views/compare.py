# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

import io, logging, json, re

from collections import OrderedDict
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import six
from django.views.generic import TemplateView
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_prefixed)
from deployutils.helpers import datetime_or_now
from openpyxl import Workbook
from pages.models import PageElement
from survey.models import Matrix
from survey.views.matrix import MatrixDetailView

from ..api.benchmark import BenchmarkMixin
from ..api.dashboards import SupplierListMixin
from ..helpers import as_valid_sheet_title
from ..mixins import AccountMixin, PermissionMixin


LOGGER = logging.getLogger(__name__)


class SuppliersView(AccountMixin, PermissionMixin, TemplateView):

    template_name = 'envconnect/reporting/index.html'

    def get_context_data(self, **kwargs):
        context = super(SuppliersView, self).get_context_data(**kwargs)
        accounts = self.managed_accounts
        if len(accounts) == 1:
            totals = get_object_or_404(
                Matrix, account__slug=accounts[0], metric__slug='totals')
            totals_chart_url = reverse('matrix_chart',
                args=(accounts[0], '/%s' % totals.slug))
        else:
            totals_chart_url = reverse('envconnect_portfolio',
                args=('/totals',))
        urls = {
            'api_suppliers': reverse('api_suppliers', args=(self.account,)),
            'api_accessibles': site_prefixed(
                "/api/profile/%(account)s/plans/%(account)s-report/"\
                "subscriptions/" % {'account': self.account}),
            'api_organizations': site_prefixed("/api/profile/"),
            'api_organization_profile': site_prefixed(
                "/api/profile/%(account)s/" % {'account': self.account}),
            'totals_chart': totals_chart_url,
        }
        context.update({
            'score_toggle': True,
            'account_extra': self.account.extra
        })
        self.update_context_urls(context, urls)
        return context


class PortfoliosDetailView(BenchmarkMixin, MatrixDetailView):

    matrix_url_kwarg = 'path'

    def get_available_matrices(self):
        return Matrix.objects.filter(account=self.account)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        candidate = self.kwargs.get(self.matrix_url_kwarg)
        if candidate.startswith('/'):
            candidate = candidate[1:]
        return get_object_or_404(queryset, slug=candidate)

    def get_context_data(self, **kwargs):
        #pylint:disable=too-many-locals,too-many-statements
        candidate = self.kwargs.get(self.matrix_url_kwarg)
        if candidate.startswith("/"):
            candidate = candidate[1:]
        parts = candidate.split("/")
        if len(parts) > 1:
            candidate = parts[0]
        try:
            PageElement.objects.get(slug=candidate)
        except PageElement.DoesNotExist:
            # It is not a breadcrumb path (ex: totals).
            #pylint:disable=unsubscriptable-object
            del self.kwargs[self.matrix_url_kwarg]

        context = super(PortfoliosDetailView, self).get_context_data(**kwargs)
        context.update({'available_matrices': self.get_available_matrices()})

        from_root, trail = self.breadcrumbs
        parts = from_root.split("/")
        if len(parts) > 1:
            root = self._build_tree(trail[-1][0], from_root)
            self.decorate_with_breadcrumbs(root)
            if not parts[1].startswith('sustainability-'):
                excludes = ['sustainability-%s' % parts[1]]
            else:
                excludes = [parts[1]]
            charts = self.get_charts(root, excludes=excludes)
        else:
            # totals
            charts = []
            industries = set([])
            for extra in self.account_queryset.filter(
                    subscription__plan__slug='%s-report' % self.account).values(
                        'extra'):
                try:
                    extra = extra.get('extra')
                    if extra:
                        extra = json.loads(extra.replace("'", '"'))
                        industries |= set([extra.get('industry')])
                except (IndexError, TypeError, ValueError) as _:
                    pass
            flt = None
            for industry in industries:
                if flt is None:
                    flt = Q(slug__startswith=industry)
                else:
                    flt |= Q(slug__startswith=industry)
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
                tag = element.tag if element is not None else ""
                charts += [{
                    'slug': cohort.slug,
                    'breadcrumbs': [cohort.title],
                    'icon': element.text if element is not None else "",
                    'icon_css':
                        'grey' if (tag and 'management' in tag) else 'orange'
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
        context.update({'charts': charts})
        return context


class SuppliersXLSXView(SupplierListMixin, TemplateView):
    """
    Download scores of all reporting entities as an Excel spreadsheet.
    """
    content_type = \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    basename = 'dashboard'

    headings = ['Supplier name', 'Contact name', 'Email',
        'Telephone number', 'Mobile number', 'Industry segment', 'Last updated',
        'Total score']

    def get_headings(self):
        return self.headings

    def get_filename(self):
        return datetime_or_now().strftime(self.basename + '-%Y%m%d.xlsx')

    def writerow(self, rec):
        last_activity_at = ""
        normalized_score = "N/A"
        if rec['request_key']:
            normalized_score = "Requested"
        else:
            last_activity_at = rec.get('last_activity_at', None)
            if last_activity_at:
                last_activity_at = last_activity_at.isoformat()
            if rec.get('assessment_completed', False):
                normalized_score = rec.get('normalized_score', "N/A")
        row = [rec['printable_name'], "", rec['email'], "", "", "",
            last_activity_at, normalized_score]
        for score in rec.get('scores', []):
            row += [score[1]]
        self.wsheet.append(row)

    def get(self, request, *args, **kwargs):
        #pylint: disable=unused-argument,too-many-locals,too-many-nested-blocks
        #pylint: disable=too-many-statements
        rollup_tree = self.rollup_scores()
        account_scores = rollup_tree[0]['accounts']
        wbook = Workbook()

        # Populate the Total sheet
        self.wsheet = wbook.active
        self.wsheet.title = as_valid_sheet_title("Total scores")
        self.wsheet.append(self.get_headings())
        for account in self.requested_accounts:
            self.writerow(self.get_score(account, account_scores,
                    self.complete_assessments, self.complete_improvements))

        # Populate industry segments sheet
        industries = [elem['slug'] for elem in PageElement.objects.filter(
            slug__startswith='sustainability-').values('slug')]
        for industry in industries:
            trail = self.get_full_element_path(industry)
            from_root = "/" + "/".join([element.slug for element in trail])
            try:
                rollup_industry = self.get_rollup_at_path_prefix(
                    from_root, rollup_tree)
            except KeyError:
                # We don't have any score for that industry segment
                continue
            account_rows = OrderedDict()
            headings = [] + self.get_headings()
            account_scores = rollup_industry[0]['accounts']
            for account in self.requested_accounts:
                if account.pk in account_scores:
                    account_rows[account.pk] = self.get_score(
                        account, account_scores,
                        self.complete_assessments, self.complete_improvements)
            for icon_nodes in six.itervalues(rollup_industry[1]):
                # These are icon-level scores
                icon_node = icon_nodes[0]
                icon_slug = icon_node['slug']
                icon_title = icon_node['title']
                headings += [icon_title]
                icon_account_scores = icon_node['accounts']
                for account in self.requested_accounts:
                    if account.pk in account_rows:
                        meta = self.get_score(
                            account, icon_account_scores,
                            self.complete_assessments,
                            self.complete_improvements)
                        score = meta.get('normalized_score', "N/A")
                        if 'scores' not in account_rows[account.pk]:
                            account_rows[account.pk]['scores'] = []
                        account_rows[account.pk]['scores'] += [
                            (icon_slug, score)]
                for system_nodes in six.itervalues(icon_nodes[1]):
                    # These are system-level scores
                    system_slug = system_nodes[0]['slug']
                    system_title = system_nodes[0]['title']
                    headings += [system_title]
                    system_account_scores = system_nodes[0]['accounts']
                    for account in self.requested_accounts:
                        if account.pk in account_rows:
                            meta = self.get_score(
                                account, system_account_scores,
                                self.complete_assessments,
                                self.complete_improvements)
                            score = meta.get('normalized_score', "N/A")
                            if 'scores' not in account_rows[account.pk]:
                                account_rows[account.pk]['scores'] = []
                            account_rows[account.pk]['scores'] += [
                                (system_slug, score)]

            if account_rows:
                self.wsheet = wbook.create_sheet(
                    title=as_valid_sheet_title(rollup_industry[0]['title']))
                self.wsheet.append(headings)
                for rec in six.itervalues(account_rows):
                    self.writerow(rec)

        content = io.BytesIO()
        wbook.save(content)
        content.seek(0)

        resp = HttpResponse(content, content_type=self.content_type)
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())
        return resp
