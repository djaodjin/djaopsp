# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import csv, datetime, json, logging, io

from deployutils.crypt import JSONEncoder
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from openpyxl import Workbook
from pages.models import PageElement
from survey.models import Answer, Question
from survey.views.sample import SampleUpdateView as BaseSampleUpdateView
from extended_templates.backends.pdf import PdfTemplateResponse

from ..mixins import ReportMixin, ImprovementQuerySetMixin
from ..models import Consumption


LOGGER = logging.getLogger(__name__)


class ImproveView(ReportMixin, TemplateView):

    template_name = 'envconnect/improve.html'
    breadcrumb_url = 'envconnect_improve'

    @staticmethod
    def get_scorecard_path(path):
        parts = path.split('/')
        for idx, part in enumerate(parts):
            if part.startswith('sustainability-'):
                return '/'.join(parts[:idx + 1])
        return path

    def get_breadcrumb_url(self, path):
        organization = self.kwargs.get('organization', None)
        if organization:
            return reverse(
                'envconnect_improve_organization', args=(organization, path))
        return super(ImproveView, self).get_breadcrumb_url(path)

    def get_context_data(self, **kwargs):
        context = super(ImproveView, self).get_context_data(**kwargs)
        root = self.get_report_tree()
        if root:
            self.decorate_with_breadcrumbs(root)
            context.update({
                'root': root,
                'entries': json.dumps(root, cls=JSONEncoder)
            })
        context.update({
            'role': "tab",
            'sample': self.sample
        })
        urls = {'api_account_benchmark': reverse('api_benchmark',
                args=(self.kwargs.get('organization'), self.get_scorecard_path(
                    self.kwargs.get('path'))))}
        self.update_context_urls(context, urls)
        return context


class ResponseUpdateView(ImprovementQuerySetMixin, BaseSampleUpdateView):
    """
    All ``BestPractice`` selected by a ``User`` on a single html page.
    """
    template_name = 'envconnect/response_update.html'
    next_step_url = 'envconnect_report'

    def get_context_data(self, **kwargs):
        context = super(ResponseUpdateView, self).get_context_data(**kwargs)
        context.update({'answers': self.object.answers.all()})
        return context

    def get_success_url(self):
        messages.info(
            self.request, 'Your answers have been recorded. Thank you.')
        return reverse(self.next_step_url, kwargs=self.get_url_context())


class ImprovementSpreadsheetView(ImprovementQuerySetMixin, ListView):

    basename = 'improvements'
    headings = ['Practice', 'Implementation rate', 'Opportunity score']

    def insert_path(self, tree, parts=None):
        if not parts:
            return tree
        if not parts[0] in tree:
            tree[parts[0]] = {}
        return self.insert_path(tree[parts[0]], parts[1:])

    def write_tree(self, root, indent=''):
        for element in sorted(
                list(root.keys()), key=lambda node: (node.tag, node.pk)):
            # XXX sort won't exactly match the web presentation
            # which uses RelationShip order
            # (see ``BreadcrumbMixin._build_tree``).
            nodes = root[element]
            if 'opportunity' in nodes:
                # We reached a leaf
                self.writerow([
                    indent + element.title,
                    nodes['rate'],
                    nodes['opportunity']
                ])
            else:
                self.writerow([indent + element.title])
                self.write_tree(nodes, indent=indent + '  ')

    def get(self, request, *args, **kwargs): #pylint: disable=unused-argument
        opportunities = {}
        for consumption in Consumption.objects.with_opportunity(
                filter_out_testing=self._get_filter_out_testing()):
            opportunities[consumption.pk] = consumption

        tree = {}
        for improvement in self.get_queryset():
            consumption = improvement.question.consumption
            _, parts = self.get_breadcrumbs(consumption.path)
            leaf = self.insert_path(tree, [part[0] for part in parts])
            details = opportunities[consumption.pk]
            leaf.update({
                'path': consumption.path,
                'avg_energy_saving': consumption.avg_energy_saving,
                'capital_cost': consumption.capital_cost,
                'payback_period': consumption.payback_period,
                'rate': consumption.rate,
                'opportunity': details.opportunity
            })

        self.create_writer()
        self.writerow(["The Sustainability Project"\
            " - Practices selected for improvement"])
        self.writerow(self.get_headings())
        self.write_tree(tree)
        resp = HttpResponse(self.flush_writer(), content_type=self.content_type)
        resp['Content-Disposition'] = \
            'attachment; filename="{}"'.format(self.get_filename())
        return resp

    def get_headings(self):
        return self.headings

    def get_filename(self):
        return datetime.datetime.now().strftime(self.basename + '-%Y%m%d.csv')


class ImprovementCSVView(ImprovementSpreadsheetView):

    content_type = 'text/csv'

    def writerow(self, row):
        self.csv_writer.writerow(row)

    def create_writer(self):
        self.content = io.StringIO()
        self.csv_writer = csv.writer(self.content)

    def flush_writer(self):
        self.content.seek(0)
        return self.content

    def get_filename(self):
        return datetime.datetime.now().strftime(self.basename + '-%Y%m%d.csv')


class ImprovementXLSXView(ImprovementSpreadsheetView):

    content_type = \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    def writerow(self, row):
        self.wsheet.append(row)

    def create_writer(self):
        self.wbook = Workbook()
        self.wsheet = self.wbook.active

    def flush_writer(self):
        content = io.BytesIO()
        self.wbook.save(content)
        content.seek(0)
        return content

    def get_filename(self):
        return datetime.datetime.now().strftime(self.basename + '-%Y%m%d.xlsx')


class ReportPDFView(ImprovementQuerySetMixin, ListView):

    model = Question
    http_method_names = ['get']
    template_name = 'envconnect/best_practice_pdf.html'

    def get_queryset(self):
        return self.model.objects.filter(survey=self.sample).exclude(
            answer__text=Consumption.NOT_APPLICABLE)

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        report_items = []

        for question in self.object_list:
            report_items += [
                {
                    'answer': Answer.objects.get(question_id=question.id),
                    'consumption': Consumption.objects.get(id=question.text)
                }
            ]
        context = self.get_context_data(**kwargs)
        industry = PageElement.objects.get(slug=self.kwargs.get('industry'))
        context.update({'industry':industry})
        context.update({'report_items':report_items})
        return PdfTemplateResponse(request, self.template_name, context)
