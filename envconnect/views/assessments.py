# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import csv, datetime, json, logging, io

from django.utils import six
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView
from deployutils.crypt import JSONEncoder
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.styles.borders import BORDER_THIN
from openpyxl.styles.fills import FILL_SOLID
from survey.models import Choice

from ..mixins import ReportMixin
from ..models import Consumption


LOGGER = logging.getLogger(__name__)


class AssessmentBaseView(ReportMixin, TemplateView):

    pass


class AssessmentView(AssessmentBaseView):

    template_name = 'envconnect/self_assessment.html'
    breadcrumb_url = 'assess'

    def get_breadcrumb_url(self, path):
        organization = self.kwargs.get('organization', None)
        if organization:
            return reverse('envconnect_assess_organization',
                args=(organization, path))
        return super(AssessmentView, self).get_breadcrumb_url(path)

    def get_context_data(self, **kwargs):
        context = super(AssessmentView, self).get_context_data(**kwargs)
        self.get_or_create_assessment_sample()
        root = self.get_report_tree()
        if root:
            context.update({
                'root': root,
                'entries': json.dumps(root, cls=JSONEncoder)
            })
        context.update({
            'page_icon': self.icon,
            'sample': self.sample,
            'survey': self.sample.survey,
            'role': "tab",
            'score_toggle': self.request.GET.get('toggle', False)})
        organization = context['organization']
        self.update_context_urls(context, {
            'api_assessment_sample': reverse(
                'survey_api_sample', args=(organization, self.sample)),
            'api_assessment_sample_new': reverse(
                'survey_api_sample_new', args=(organization,)),
        })
        return context

    def get(self, request, *args, **kwargs):
        from_root, _ = self.breadcrumbs
        if not from_root or from_root == "/":
            return HttpResponseRedirect(reverse('homepage'))
        return super(AssessmentView, self).get(request, *args, **kwargs)


class AssessmentSpreadsheetView(AssessmentBaseView):

    basename = 'assessment'
    indent_step = '    '

    @staticmethod
    def _get_consumption(element):
        return element.get('consumption', None)

    @staticmethod
    def _get_tag(element):
        return element.get('tag', "")

    @staticmethod
    def _get_title(element):
        return element.get('title', "")

    def insert_path(self, tree, parts=None):
        if not parts:
            return tree
        if not parts[0] in tree:
            tree[parts[0]] = {}
        return self.insert_path(tree[parts[0]], parts[1:])

    def writerow(self, row, leaf=False):
        pass

    def write_tree(self, root, indent=''):
        """
        The *root* parameter looks like:
        (PageElement, [(PageElement, [...]), (PageElement, [...]), ...])
        """
        if not root[1]:
            # We reached a leaf
            consumption = self._get_consumption(root[0])
            row = [indent + self._get_title(root[0])]
            if consumption:
                for heading in self.get_headings(self._get_tag(root[0])):
                    if consumption.get('implemented', "") == heading:
                        row += ['X']
                    else:
                        row += ['']
            self.writerow(row, leaf=True)
        else:
            self.writerow([indent + self._get_title(root[0])])
            for element in six.itervalues(root[1]):
                self.write_tree(element, indent=indent + self.indent_step)

    def get(self, *args, **kwargs): #pylint: disable=unused-argument
        # All assessment questions for an industry, regardless
        # of the actual from_path.
        # XXX if we do that, we shouldn't use from_root (i.e. system pages)
        _, trail = self.breadcrumbs
        trail_head = ("/"
            + trail[0][0].slug.decode('utf-8') if six.PY2 else trail[0][0].slug)
        from_trail_head = "/" + "/".join([
            element.slug.decode('utf-8') if six.PY2 else element.slug
            for element in self.get_full_element_path(trail_head)])
        # We use cut=None here so we print out the full assessment
        root = self._build_tree(trail[0][0], from_trail_head, cut=None)

        self.create_writer(
            self.get_headings(self._get_tag(root[0])),
            title=self._get_title(root[0]))
        self.writerow(
            ["Assessment - Environmental practices"], leaf=True)
        self.writerow(
            ["Practice", "Implemented as a standard practice?"], leaf=True)
        self.writerow(
            [""] + self.get_headings(self._get_tag(root[0])), leaf=True)
        indent = self.indent_step
        for nodes in six.itervalues(root[1]):
            self.writerow([indent + self._get_title(nodes[0])])
            for elements in six.itervalues(nodes[1]):
                self.write_tree(elements, indent=indent + self.indent_step)
        resp = HttpResponse(self.flush_writer(), content_type=self.content_type)
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())
        return resp

    @staticmethod
    def get_headings(tag):
        return [str(choice) for choice in Choice.objects.filter(
            pk__in=Consumption.ASSESSMENT_CHOICES.get(tag,
                Consumption.ASSESSMENT_CHOICES.get('default'))).order_by('pk')]


class AssessmentCSVView(AssessmentSpreadsheetView):

    content_type = 'text/csv'

    def writerow(self, row, leaf=False):
        self.csv_writer.writerow([
            rec.encode('utf-8') if six.PY2 else rec
            for rec in row])

    def create_writer(self, headings, title=None):
        #pylint:disable=unused-argument
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


class AssessmentXLSXView(AssessmentSpreadsheetView):

    content_type = \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    def writerow(self, row, leaf=False):
        #pylint:disable=protected-access
        self.wsheet.append(row)
        if leaf:
            if len(row) >= 6:
                for row_cells in self.wsheet.iter_rows(
                        min_row=self.wsheet._current_row,
                        max_row=self.wsheet._current_row):
                    row_cells[0].alignment = self.heading_alignment
                self.wsheet.row_dimensions[self.wsheet._current_row].height = 0
        else:
            for row_cells in self.wsheet.iter_rows(
                    min_row=self.wsheet._current_row,
                    max_row=self.wsheet._current_row):
                row_cells[0].font = self.heading_font
                row_cells[0].alignment = self.heading_alignment

    def create_writer(self, headings, title=None):
        col_scale = 11.9742857142857
        self.wbook = Workbook()
        self.wsheet = self.wbook.active
        if title:
            self.wsheet.title = title
        self.wsheet.row_dimensions[1].height = 0.36 * (6 * col_scale)
        self.wsheet.column_dimensions['A'].width = 6.56 * col_scale
        for col_num in range(0, len(headings)):
            self.wsheet.column_dimensions[chr(ord('B') + col_num)].width \
                = 0.99 * col_scale
        self.heading_font = Font(
            name='Calibri', size=12, bold=False, italic=False,
            vertAlign='baseline', underline='none', strike=False,
            color='FF0071BB')
        self.heading_alignment = Alignment(wrap_text=True)

    def flush_writer(self):
        border = Border(
            left=Side(border_style=BORDER_THIN, color='FF000000'),
            right=Side(border_style=BORDER_THIN, color='FF000000'),
            top=Side(border_style=BORDER_THIN, color='FF000000'),
            bottom=Side(border_style=BORDER_THIN, color='FF000000'))
        alignment = Alignment(
            horizontal='center', vertical='center',
            text_rotation=0, wrap_text=False,
            shrink_to_fit=False, indent=0)
        title_fill = PatternFill(fill_type=FILL_SOLID, fgColor='FFDDD9C5')
        subtitle_fill = PatternFill(fill_type=FILL_SOLID, fgColor='FFEEECE2')
        subtitle_font = Font(
            name='Calibri', size=12, bold=False, italic=False,
            vertAlign='baseline', underline='none', strike=False,
            color='FF000000')
        row = self.wsheet.row_dimensions[1]
        row.fill = title_fill
        row.font = Font(
            name='Calibri', size=20, bold=False, italic=False,
            vertAlign='baseline', underline='none', strike=False,
            color='FF000000')
        row.alignment = alignment
        row.border = border
        self.wsheet.merge_cells('A1:F1')
        row = self.wsheet.row_dimensions[2]
        row.fill = subtitle_fill
        row.font = subtitle_font
        row.alignment = alignment
        row.border = border
        row = self.wsheet.row_dimensions[3]
        row.fill = subtitle_fill
        row.font = subtitle_font
        row.alignment = alignment
        row.border = border
        self.wsheet.merge_cells('B2:F2')
        self.wsheet.merge_cells('A2:A3')
        content = io.BytesIO()
        self.wbook.save(content)
        content.seek(0)
        return content

    def get_filename(self):
        return datetime.datetime.now().strftime(self.basename + '-%Y%m%d.xlsx')
