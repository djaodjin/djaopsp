# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import csv, datetime, json, logging, io

from django.utils import six
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from openpyxl import Workbook
from survey.models import Response, SurveyModel

from .benchmark import BenchmarkBaseView
from ..mixins import BestPracticeMixin
from ..models import Consumption


LOGGER = logging.getLogger(__name__)


class SelfAssessmentBaseView(BenchmarkBaseView):

    def attach_benchmarks(self, root, view_response=None):
        if not view_response:
            self._sample = Response.objects.create(account=self.account,
                survey=SurveyModel.objects.get(title=self.report_title))
        super(SelfAssessmentBaseView, self).attach_benchmarks(
            root, view_response=self._sample)


class SelfAssessmentView(BestPracticeMixin, SelfAssessmentBaseView):

    template_name = 'envconnect/self_assessment.html'
    breadcrumb_url = 'report'

    def get_breadcrumb_url(self, path):
        organization = self.kwargs.get('organization', None)
        if organization:
            return reverse('report_organization', args=(organization, path))
        return super(SelfAssessmentView, self).get_breadcrumb_url(path)

    def get_context_data(self, **kwargs):
        context = super(SelfAssessmentView, self).get_context_data(**kwargs)
        if self.root:
            self.attach_benchmarks(self.root, view_response=self.sample)
            context.update({
                'entries': json.dumps(self.to_representation(self.root))
            })
        organization = context['organization']
        context.update({
            'page_icon': self.icon,
            'response': self.sample,
            'survey': self.sample.survey,
            'role': "tab",
            'score_toggle': self.request.GET.get('toggle', False)})
        self.update_context_urls(context, {
            'api_self_assessment_response': reverse(
                'survey_api_response', args=(organization, self.sample)),
        })
        return context

    def get(self, request, *args, **kwargs):
        from_root, _ = self.breadcrumbs
        if not from_root or from_root == "/":
            return HttpResponseRedirect(reverse('homepage'))
        return super(SelfAssessmentView, self).get(request, *args, **kwargs)


class SelfAssessmentSpreadsheetView(SelfAssessmentBaseView):

    basename = 'self-assessment'

    def insert_path(self, tree, parts=None):
        if not parts:
            return tree
        if not parts[0] in tree:
            tree[parts[0]] = {}
        return self.insert_path(tree[parts[0]], parts[1:])

    def writerow(self, row):
        self.csv_writer.writerow([
            rec.encode('utf-8') if six.PY2 else rec
            for rec in row])

    def write_tree(self, root, indent=''):
        """
        The *root* parameter looks like:
        (PageElement, [(PageElement, [...]), (PageElement, [...]), ...])
        """
        if not root[1]:
            # We reached a leaf
            consumption = getattr(root[0], 'consumption', None)
            row = [indent + root[0].title]
            if consumption:
                for heading in self.get_headings(root[0].tag):
                    if consumption.implemented == heading:
                        row += ['X']
                    else:
                        row += ['']
            self.writerow(row)
        else:
            self.writerow([indent + root[0].title])
            for element in root[1]:
                self.write_tree(element, indent=indent + '  ')

    def get(self, *args, **kwargs): #pylint: disable=unused-argument
        # All self-assessment questions for an industry, regardless
        # of the actual from_path.
        # XXX if we do that, we shouldn't use from_root (i.e. system pages)
        _, trail = self.breadcrumbs
        trail_head = ("/"
            + trail[0][0].slug.decode('utf-8') if six.PY2 else trail[0][0].slug)
        from_trail_head = "/" + "/".join([
            element.slug.decode('utf-8') if six.PY2 else element.slug
            for element in self.get_full_element_path(trail_head)])
        self.root = self._build_tree(trail[0][0], from_trail_head, cut=None)
        self.attach_benchmarks(self.root, view_response=self.sample)

        self.create_writer()
        self.writerow(["The Sustainability Project - Self-assessment"])
        self.writerow([self.root[0].title])
        indent = ' '
        for nodes in self.root[1]:
            self.writerow([indent + nodes[0].title]
                + self.get_headings(nodes[0].tag))
            for elements in nodes[1]:
                self.write_tree(elements, indent=indent + ' ')
        resp = HttpResponse(self.flush_writer(), content_type=self.content_type)
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())
        return resp

    @staticmethod
    def get_headings(tag):
        return list(Consumption.ASSESSMENT_CHOICES.get(tag,
            Consumption.ASSESSMENT_CHOICES.get('default')))


class SelfAssessmentCSVView(SelfAssessmentSpreadsheetView):

    content_type = 'text/csv'

    def writerow(self, row):
        self.csv_writer.writerow(row)

    def create_writer(self):
        if six.PY2:
            self.content = io.BytesIO()
        else:
            self.content = io.StringIO()
        self.csv_writer = csv.writer(self.content)

    def flush_writer(self):
        self.content.seek(0)
        return self.content

    def get_filename(self):
        return datetime.datetime.now().strftime(self.basename + '-%Y%m%d.csv')


class SelfAssessmentXLSXView(SelfAssessmentSpreadsheetView):

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
