# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

import io, json, logging, re
from collections import OrderedDict

from dateutil.relativedelta import relativedelta
from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.utils import six
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
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
from ..models import Consumption


LOGGER = logging.getLogger(__name__)


class SuppliersView(AccountMixin, PermissionMixin, TemplateView):

    template_name = 'envconnect/reporting/index.html'

    def get_context_data(self, **kwargs):
        context = super(SuppliersView, self).get_context_data(**kwargs)
        self.update_context_urls(context, {
            'api_suppliers': reverse('api_suppliers', args=(self.account,)),
            'api_accessibles': site_prefixed(
                "/api/profile/%(account)s/plans/%(account)s-report/"\
                "subscriptions/" % {'account': self.account}),
            'api_organizations': site_prefixed("/api/profile/"),
            'api_organization_profile': site_prefixed(
                "/api/profile/%(account)s/" % {'account': self.account}),
        })
        context.update({
            'score_toggle': True,
            'account_extra': self.account.extra
        })
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

    @staticmethod
    def get_indent_bestpractice(depth=0):
        return "  " * depth

    @staticmethod
    def get_indent_heading(depth=0):
        return "  " * depth

    def get_filename(self):
        return datetime_or_now().strftime(self.basename + '-%Y%m%d.xlsx')

    def writerow(self, rec, headings=None):
        last_activity_at = rec.get('last_activity_at', "")
        if last_activity_at:
            last_activity_at = last_activity_at.isoformat()
        if headings:
            if rec['request_key']:
                self.wsheet.append([
                    rec['printable_name'], "", rec['email'], "", "", "",
                    last_activity_at] + ["Requested" for val in headings])
            else:
                scores = []
                for heading in headings:
                    section_score = "N/A"
                    for score in rec.get('scores', []):
                        if score[2] == heading:
                            section_score = score[0]
                            break
                    scores += [section_score]
                self.wsheet.append([
                    rec['printable_name'], "", rec['email'], "", "", "",
                    last_activity_at] + scores)
        else:
            for rep in rec.get('reports_to', [(
                    self.account.slug, self.account.full_name)]):
                report_to = "" if rep[0] == self.account.slug else rep[1]
                if rec['request_key']:
                    self.wsheet.append([
                        rec['printable_name'], "", rec['email'], "", "", "",
                        last_activity_at, "Requested", report_to])
                else:
                    for score in rec.get('scores', [("N/A", "", "")]):
                        normalized_score = score[0]
                        segment_slug = score[1]
                        segment = score[2]
                        row = [rec['printable_name'], "",
                            rec['email'], "", "", segment,
                            last_activity_at, normalized_score, report_to]
                        self.wsheet.append(row)
                        if segment_slug:
                            if segment_slug not in self.suppliers_per_segment:
                                self.suppliers_per_segment[segment_slug] = set(
                                    [])
                            self.suppliers_per_segment[segment_slug] |= set(
                                [rec['slug']])

    def get(self, request, *args, **kwargs):
        #pylint: disable=unused-argument,too-many-locals,too-many-nested-blocks
        #pylint: disable=too-many-statements
        rollup_tree = self.rollup_scores()
        self.suppliers_per_segment = {}
        wbook = Workbook()

        # Populate the Total sheet
        self.wsheet = wbook.active
        self.wsheet.title = as_valid_sheet_title("Total scores")
        self.wsheet.append(self.get_headings())
        for account in self.get_suppliers(rollup_tree):
            self.writerow(account)

        # Populate per-segment sheets
        for container in six.itervalues(rollup_tree[1]):
            segment_suppliers = self.suppliers_per_segment.get(
                container[0]['slug'], set([]))
            if not segment_suppliers:
                continue
            for segment in six.itervalues(container[1]):
                headings = [val[0]['title']
                    for val in six.itervalues(segment[1])]
                all_headings = self.get_headings()[:-1] + headings
                suppliers_per_segment = self.get_suppliers(segment)
                if suppliers_per_segment:
                    self.wsheet = wbook.create_sheet(
                        title=as_valid_sheet_title(segment[0]['title']))
                    self.wsheet.append(all_headings)
                    for account in suppliers_per_segment:
                        if account['slug'] in segment_suppliers:
                            self.writerow(account, headings=headings)

        # Populate improvements planned sheet
        practices = Consumption.objects.filter(
            answer__sample__extra='is_planned',
            answer__sample__is_frozen=True,
            answer__metric_id=self.default_metric_id,
            answer__measured=Consumption.NEEDS_SIGNIFICANT_IMPROVEMENT
        ).annotate(nb_suppliers=Count('answer__sample')).values(
            'path', 'nb_suppliers')

        depth = 2
        root = (OrderedDict({}), OrderedDict({}))
        for practice in practices:
            node = self._insert_path(root, practice['path'], depth=depth)
            node[0].update({'nb_suppliers': practice['nb_suppliers']})
        root = self._natural_order(root)
        rows = self.flatten_answers(root, '')

        self.wsheet = wbook.create_sheet(
            title=as_valid_sheet_title("Improvements"))
        self.wsheet.append(('Best practice',
            'Nb suppliers who have selected the practice for improvement.'))
        for row in rows:
            if row[2].slug.startswith('sustainability-'):
                # Avoids double back-to-back rows with same title
                continue
            indent = row[0]
            title = row[2].title
            nb_suppliers = row[3].get('nb_suppliers', "")
            self.wsheet.append([indent + title, nb_suppliers])

        # Prepares the result file
        content = io.BytesIO()
        wbook.save(content)
        content.seek(0)

        resp = HttpResponse(content, content_type=self.content_type)
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())
        return resp
