# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import csv, datetime, logging, io

from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponse
from django.views.generic.list import ListView
from pages.models import PageElement
from survey.models import Answer, Question
from survey.views.response import (
    ResponseUpdateView as BaseResponseUpdateView)
from extended_templates.backends.pdf import PdfTemplateResponse

from ..mixins import BestPracticeMixin, ImprovementQuerySetMixin
from ..models import Consumption
from .self_assessment import SelfAssessmentView

LOGGER = logging.getLogger(__name__)


class ImproveView(SelfAssessmentView):

    template_name = 'envconnect/improve.html'
    breadcrumb_url = 'envconnect_improve'

    def get_breadcrumb_url(self, path):
        organization = self.kwargs.get('organization', None)
        if organization:
            return reverse(
                'envconnect_improve_organization', args=(organization, path))
        return super(ImproveView, self).get_breadcrumb_url(path)


class ResponseUpdateView(ImprovementQuerySetMixin, BaseResponseUpdateView):
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


class ImprovementCSVView(ImprovementQuerySetMixin,
                         BestPracticeMixin, # for get_breadcrumbs
                         ListView):

    basename = 'improvements'
    headings = ['Practice', 'Savings', 'Cost', 'Payback',
                'Implementation rate', 'Opportunity score']

    def insert_path(self, tree, parts=None):
        if not parts:
            return tree
        if not parts[0] in tree:
            tree[parts[0]] = {}
        return self.insert_path(tree[parts[0]], parts[1:])

    def write_tree(self, root, csv_writer, indent=''):
        for element in sorted(list(root.keys()), cmp=lambda left, right:
                (left.tag < right.tag)
                or (left.tag == right.tag and left.pk < right.pk)):
            # XXX sort won't exactly match the web presentation
            # which uses RelationShip order
            # (see ``BreadcrumbMixin._build_tree``).
            nodes = root[element]
            if 'opportunity' in nodes:
                # We reached a leaf
                csv_writer.writerow([
                    indent + element.title,
                    nodes['avg_energy_saving'],
                    nodes['capital_cost'],
                    nodes['payback_period'],
                    nodes['rate'],
                    nodes['opportunity']
                ])
            else:
                csv_writer.writerow([indent + element.title])
                self.write_tree(nodes, csv_writer, indent=indent + '  ')

    def get(self, *args, **kwargs): #pylint: disable=unused-argument
        opportunities = {}
        for consumption in Consumption.objects.with_opportunity():
            opportunities[consumption.pk] = consumption

        tree = {}
        for improvement in self.get_queryset():
            _, parts = self.get_breadcrumbs(improvement.consumption.path)
            leaf = self.insert_path(tree, [part[0] for part in parts])
            details = opportunities[improvement.consumption.pk]
            leaf.update({
                'path': improvement.consumption.path,
                'avg_energy_saving': improvement.consumption.avg_energy_saving,
                'capital_cost': improvement.consumption.capital_cost,
                'payback_period': improvement.consumption.payback_period,
                'rate': improvement.consumption.get_rate(),
                'opportunity': details.opportunity
            })

        content = io.StringIO()
        csv_writer = csv.writer(content)
        csv_writer.writerow(["The Sustainability Project"\
            " - Practices selected for improvement"])
        csv_writer.writerow(self.get_headings())
        self.write_tree(tree, csv_writer)
        content.seek(0)
        resp = HttpResponse(content, content_type='text/csv')
        resp['Content-Disposition'] = \
            'attachment; filename="{}"'.format(
                self.get_filename())
        return resp

    def get_headings(self):
        return self.headings

    def get_filename(self):
        return datetime.datetime.now().strftime(self.basename + '-%Y%m%d.csv')


class ReportPDFView(ImprovementQuerySetMixin, ListView):

    model = Question
    http_method_names = ['get']
    template_name = 'envconnect/best_practice_pdf.html'

    def get_queryset(self):
        survey = self.get_survey()
        return self.model.objects.filter(
            survey=survey).exclude(answer__text=Consumption.NOT_APPLICABLE)

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
