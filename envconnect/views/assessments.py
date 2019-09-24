# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import csv, io, json, logging, re
from collections import namedtuple

from dateutil.relativedelta import relativedelta
from django.utils import six
from django.core.urlresolvers import reverse
from django.db import connection
from django.db.models import F, Count
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView
from deployutils.crypt import JSONEncoder
from deployutils.helpers import datetime_or_now, update_context_urls
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.styles.borders import BORDER_THIN
from openpyxl.styles.fills import FILL_SOLID
from pages.models import PageElement
from survey.models import Answer, Choice, Metric, Sample, Unit

from ..helpers import get_testing_accounts
from ..mixins import ReportMixin, BestPracticeMixin
from ..models import Consumption, get_scored_answers
from ..serializers import ConsumptionSerializer
from ..suppliers import get_supplier_managers
from ..templatetags.navactive import assessment_choices


LOGGER = logging.getLogger(__name__)


class AssessmentAnswer(object):

    def __init__(self, **kwargs):
        for key, val in six.iteritems(kwargs):
            setattr(self, key, val)

    def __getattr__(self, name):
        return getattr(self.consumption, name)


class AssessmentBaseMixin(ReportMixin, BestPracticeMixin):
    # Implementation Note: uses BestPracticeMixin in order to display
    # bestpractice info through links in assess and improve pages.

    def _framework_results(self, consumptions):
        if self.survey.slug == 'framework':
            ends_at = self.sample.created_at + relativedelta(months=1)
            last_frozen_assessments = \
                Consumption.objects.get_latest_assessment_by_accounts(
                    self.survey, before=ends_at,
                    excludes=get_testing_accounts())
            results = Answer.objects.filter(
                metric_id=self.default_metric_id,
                sample_id__in=last_frozen_assessments
            ).values('question__path', 'measured').annotate(Count('sample_id'))
            totals = {}
            for row in Answer.objects.filter(
                    metric_id=self.default_metric_id,
                    sample_id__in=last_frozen_assessments
                    ).values('question__path').annotate(Count('sample_id')):
                totals[row['question__path']] = row['sample_id__count']
            choices = {}
            for choice in Choice.objects.filter(
                    unit__metric=self.default_metric_id):
                choices[choice.pk] = choice.text

            for row in results:
                path = row['question__path']
                measured = row['measured']
                count = row['sample_id__count']
                consumption = consumptions.get(path, None)
                if consumption:
                    if not isinstance(consumption.rate, dict):
                        if not isinstance(consumption, AssessmentAnswer):
                            consumptions[path] = AssessmentAnswer(
                                consumption=consumption, rate={})
                            consumption = consumptions[path]
                        else:
                            consumption.rate = {}
                    total = totals.get(path, None)
                    consumption.rate[choices[measured]] = \
                        int(count * 100 // total)

    def decorate_leafs(self, leafs):
        """
        Adds consumptions, implementation rate, number of respondents,
        assessment and improvement answers and opportunity score.

        For each answer the improvement opportunity in the total score is
        case NO / NEEDS_SIGNIFICANT_IMPROVEMENT
          numerator = (3-A) * opportunity + 3 * avg_value / nb_respondents
          denominator = 3 * avg_value / nb_respondents
        case YES / NEEDS_MODERATE_IMPROVEMENT
          numerator = (3-A) * opportunity
          denominator = 0
        """
        #pylint:disable=too-many-locals,too-many-statements
        consumptions = {}
        consumptions_planned = {}
        # The call to `get_expected_opportunities` within `get_scored_answers`
        # will insure all questions for the assessment are picked up, either
        # they have an answer or not.
        # This is done by listing all question in `get_opportunities_sql`
        # and filtering them out through the `survey_enumeratedquestions`
        # table in `get_expected_opportunities`.
        scored_answers = get_scored_answers(
            Consumption.objects.get_active_by_accounts(
                self.survey, excludes=self._get_filter_out_testing()),
            self.default_metric_id,
            includes=self.get_included_samples())

        # We are running the query a second time because we did not populate
        # all Consumption fields through the aggregate.
        with connection.cursor() as cursor:
            cursor.execute(scored_answers, params=None)
            col_headers = cursor.description
            consumption_tuple = namedtuple(
                'ConsumptionTuple', [col[0] for col in col_headers])
            for consumption in cursor.fetchall():
                consumption = consumption_tuple(*consumption)
                if consumption.is_planned:
                    if consumption.answer_id:
                        # This is part of the plan, we mark it for the planning
                        # page but otherwise don't use values stored here.
                        consumptions_planned.update({
                            consumption.path: consumption.implemented})
                else:
                    consumptions[consumption.path] = consumption

        # Get reported measures / comments
        for datapoint in Answer.objects.filter(sample=self.sample).exclude(
                    metric__in=Metric.objects.filter(
                    slug__in=Consumption.NOT_MEASUREMENTS_METRICS)
                ).select_related('question'):
            consumption = consumptions[datapoint.question.path]
            if not hasattr(consumption, 'measures'):
                consumptions[datapoint.question.path] = AssessmentAnswer(
                    consumption=consumption, measures=[])
                consumption = consumptions[datapoint.question.path]
            measured = datapoint.measured
            if datapoint.metric.unit.system not in Unit.NUMERICAL_SYSTEMS:
                try:
                    measured = Choice.objects.get(pk=datapoint.measured).text
                except Choice.DoesNotExist:
                    LOGGER.error("cannot find Choice %s for %s",
                        datapoint.measured, datapoint)
                    measured = ""
            consumption.measures += [{
                'metric': datapoint.metric,
                'unit': (datapoint.unit
                    if datapoint.unit else datapoint.metric.unit),
                'measured': measured,
                'created_at': datapoint.created_at,
#XXX                'collected_by': datapoint.collected_by,
                }]

        # Find all framework samples / answers for a time period
        self._framework_results(consumptions)

        # Populate leafs and cut nodes with data.
        for path, vals in six.iteritems(leafs):
            # First, let's split the text fields in multiple rows
            # so we can populate the choices.
            if 'text' in vals[0]:
                vals[0]['text'] = vals[0]['text'].splitlines()
            consumption = consumptions.get(path, None)
            if consumption:
                avg_value = consumption.avg_value
                opportunity = consumption.opportunity
                nb_respondents = consumption.nb_respondents
                if nb_respondents > 0:
                    added = 3 * avg_value / float(nb_respondents)
                else:
                    added = 0
                if 'accounts' not in vals[0]:
                    vals[0]['accounts'] = {}
                if self.account.pk not in vals[0]['accounts']:
                    vals[0]['accounts'][self.account.pk] = {}
                self.populate_account(vals[0]['accounts'], consumption)
                scores = vals[0]['accounts'][self.account.pk]
                if (consumption.implemented ==
                    Consumption.ASSESSMENT_ANSWERS[Consumption.YES]) or (
                    consumption.implemented ==
                Consumption.ASSESSMENT_ANSWERS[Consumption.NOT_APPLICABLE]):
                    scores.update({
                        'opportunity_numerator': 0,
                        'opportunity_denominator': 0
                    })
                elif (consumption.implemented ==
                      Consumption.ASSESSMENT_ANSWERS[
                          Consumption.NEEDS_SIGNIFICANT_IMPROVEMENT]):
                    scores.update({
                        'opportunity_numerator': opportunity,
                        'opportunity_denominator': 0
                    })
                elif (consumption.implemented ==
                      Consumption.ASSESSMENT_ANSWERS[
                          Consumption.NEEDS_MODERATE_IMPROVEMENT]):
                    scores.update({
                        'opportunity_numerator': 2 * opportunity + added,
                        'opportunity_denominator': added
                    })
                else:
                    # No and not yet answered.
                    scores.update({
                        'opportunity_numerator': 3 * opportunity + added,
                        'opportunity_denominator': added
                    })
                vals[0]['consumption'] \
                    = ConsumptionSerializer(context={
                        'campaign': self.survey,
                        'planned': consumptions_planned.get(path, None)
                    }).to_representation(consumption)
            else:
                # Cut node: loads icon url.
                vals[0]['consumption'] = None
                text = PageElement.objects.filter(
                    slug=vals[0]['slug']).values('text').first()
                if text and text['text']:
                    vals[0].update(text)


class AssessmentView(AssessmentBaseMixin, TemplateView):

    template_name = 'envconnect/assess.html'
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
        from_root, _ = self.breadcrumbs
        root = self.get_report_tree(load_text=(self.survey.slug == 'framework'))
        if root:
            context.update({
                'root': root,
                'entries': json.dumps(root, cls=JSONEncoder)
            })

        prev_samples = [(reverse('envconnect_sample_organization',
            args=(self.account, prev_sample, self.kwargs.get('path'))),
                prev_sample.created_at)
            for prev_sample in Sample.objects.filter(
                is_frozen=True,
                extra__isnull=True,
                survey=self.survey,
                account=self.account).order_by('-created_at')]
        if prev_samples:
            context.update({'prev_samples': prev_samples})
            if self.sample.is_frozen:
                selected_sample = reverse('envconnect_sample_organization',
                    args=(self.account, self.sample, self.kwargs.get('path')))
                context.update({'selected_sample': selected_sample})

        nb_questions = Consumption.objects.filter(
            path__startswith=from_root,
            default_metric_id=self.default_metric_id).count()
        nb_answers = Answer.objects.filter(sample=self.sample,
            question__default_metric=F('metric_id'),
            question__path__startswith=from_root).count()
        context.update({
            'nb_answers': nb_answers,
            'nb_questions': nb_questions,
            'page_icon': self.icon,
            'sample': self.sample,
            'survey': self.sample.survey,
            'role': "tab",
            'score_toggle': self.request.GET.get('toggle', False)})

        # Find supplier managers subscribed to this profile
        # to share scorecard with.
        if self.manages(self.account):
            context.update({
                'supplier_managers': json.dumps(
                    get_supplier_managers(self.account))})

        organization = context['organization']
        update_context_urls(context, {
            'api_assessment_sample': reverse(
                'survey_api_sample', args=(organization, self.sample)),
            'api_assessment_sample_new': reverse(
                'survey_api_sample_new', args=(organization,)),
            'api_benchmark_share': reverse('api_benchmark_share',
                args=(organization, from_root)),
        })
        return context

    def get(self, request, *args, **kwargs):
        from_root, _ = self.breadcrumbs
        if not from_root or from_root == "/":
            return HttpResponseRedirect(reverse('homepage'))
        return super(AssessmentView, self).get(request, *args, **kwargs)


class AssessmentSpreadsheetView(AssessmentBaseMixin, TemplateView):

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

    def get(self, *args, **kwargs):
        #pylint: disable=unused-argument,too-many-locals
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

        self.headings = self.get_headings(self._get_tag(root[0]))
        self.create_writer(self.headings, title=self._get_title(root[0]))
        self.writerow(
            ["Assessment - Environmental practices"], leaf=True)
        self.writerow(
            ["Practice", "Implemented as a standard practice?"], leaf=True)
        self.writerow([""] + self.headings, leaf=True)
        indent = self.indent_step
        for nodes in six.itervalues(root[1]):
            self.writerow([indent + self._get_title(nodes[0])])
            for elements in six.itervalues(nodes[1]):
                self.write_tree(elements, indent=indent + self.indent_step)
        # Environmental metrics measured/reported
        measured_metrics = self.get_measured_metrics_context()
        if measured_metrics:
            self.writerow([])
            self.measured_title_row_idx = self.writerow(
                ["Environmental metrics measured/reported"], leaf=True)
            self.writerow(["Practice", "metric"]
                + ([""] * (len(self.headings) // 2))
                + ["measured"], leaf=True)
            for measured_metric in measured_metrics:
                look = re.match(r'.*indent-header-(\d+)', measured_metric[0])
                indent = " " * int(look.group(1))
                datapoints = measured_metric[3].get('environmental_metrics', [])
                self.writerow(["%s%s" % (indent, measured_metric[2].title)],
                    leaf=bool(datapoints))
                for datapoint in datapoints:
                    self.writerow(["",
                        datapoint['metric_title']]
                        + ([""] * (len(self.headings) // 2))
                        + [str(datapoint['measured'])], leaf=True)

        resp = HttpResponse(self.flush_writer(), content_type=self.content_type)
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())
        return resp

    @staticmethod
    def get_headings(tag):
        return [str(choice) for choice in assessment_choices(tag)]


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
        return datetime_or_now().strftime(self.basename + '-%Y%m%d.csv')


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
        return self.wsheet._current_row

    def create_writer(self, headings, title=None):
        col_scale = 11.9742857142857
        self.wbook = Workbook()
        self.wsheet = self.wbook.active
        if title:
            # Prevents 'Invalid character / found in sheet title' errors
            self.wsheet.title = title.replace('/', '-')
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
        title_font = Font(
            name='Calibri', size=20, bold=False, italic=False,
            vertAlign='baseline', underline='none', strike=False,
            color='FF000000')
        subtitle_fill = PatternFill(fill_type=FILL_SOLID, fgColor='FFEEECE2')
        subtitle_font = Font(
            name='Calibri', size=12, bold=False, italic=False,
            vertAlign='baseline', underline='none', strike=False,
            color='FF000000')
        # Implementation Note: We style the cells here instead of the rows
        # otherwise opening the file on Excel leads to weird background coloring
        # (LibreOffice looks fine).
        cell = self.wsheet['A1']
        cell.fill = title_fill
        cell.font = title_font
        cell.border = border
        cell.alignment = alignment
        cell = self.wsheet['A2']
        cell.fill = subtitle_fill
        cell.font = subtitle_font
        cell.border = border
        cell.alignment = alignment
        cell = self.wsheet['B2']
        cell.fill = subtitle_fill
        cell.font = subtitle_font
        cell.border = border
        cell.alignment = alignment
        for col in ['B', 'C', 'D', 'E', 'F']:
            cell = self.wsheet['%s3' % col]
            cell.fill = subtitle_fill
            cell.font = subtitle_font
            cell.border = border
            cell.alignment = alignment
        self.wsheet.merge_cells('A1:F1')
        self.wsheet.merge_cells('B2:F2')
        self.wsheet.merge_cells('A2:A3')

        # Environmental metrics measured/reported
        if hasattr(self, 'measured_title_row_idx'):
            col_scale = 11.9742857142857
            self.wsheet.row_dimensions[self.measured_title_row_idx].height = (
                0.36 * (6 * col_scale))
            self.wsheet.merge_cells(
                start_row=self.measured_title_row_idx, start_column=1,
                end_row=self.measured_title_row_idx,
                end_column=1 + len(self.headings))
            for row_cells in self.wsheet.iter_rows(
                    min_row=self.measured_title_row_idx,
                    max_row=self.measured_title_row_idx):
                row_cells[0].fill = title_fill
                row_cells[0].font = title_font
                row_cells[0].border = border
                row_cells[0].alignment = alignment

            for row_cells in self.wsheet.iter_rows(
                    min_row=self.measured_title_row_idx + 1,
                    max_row=self.measured_title_row_idx + 1):
                row_cells[0].fill = subtitle_fill
                row_cells[0].font = subtitle_font
                row_cells[0].alignment = alignment
                for cell in row_cells[1:]:
                    cell.fill = subtitle_fill
                    cell.font = subtitle_font
                    cell.border = border
                    cell.alignment = alignment
            self.wsheet.merge_cells(
                start_row=self.measured_title_row_idx + 1,
                start_column=2,
                end_row=self.measured_title_row_idx + 1,
                end_column=2 + len(self.headings) // 2)
            self.wsheet.merge_cells(
                start_row=self.measured_title_row_idx + 1,
                start_column=3 + len(self.headings) // 2,
                end_row=self.measured_title_row_idx + 1,
                end_column=3 + (len(self.headings) - len(self.headings) // 2))

        content = io.BytesIO()
        self.wbook.save(content)
        content.seek(0)
        return content

    def get_filename(self):
        return datetime_or_now().strftime(self.basename + '-%Y%m%d.xlsx')
