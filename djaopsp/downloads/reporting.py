# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

import csv, datetime, io, logging, os

from deployutils.apps.django.mixins.timers import TimersMixin
from django.conf import settings
from django.db.models import Q, F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, TemplateView
from openpyxl import Workbook
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.shapes.autoshape import Shape
from pptx.shapes.graphfrm import GraphicFrame
from rest_framework.request import Request
from survey.compat import force_str, six
from survey.filters import DateRangeFilter
from survey.helpers import get_extra
from survey.models import Answer, Choice, Unit
from survey.queries import datetime_or_now
from survey.utils import get_question_model

from ..api.serializers import EngagementSerializer
from ..api.portfolios import (BenchmarkMixin, PortfolioAccessibleSamplesMixin,
    PortfolioEngagementMixin)
from ..helpers import as_valid_sheet_title
from ..mixins import (AccountMixin, CampaignMixin,
    AccountsNominativeQuerysetMixin)
from ..queries import get_completed_assessments_at_by
from ..utils import get_alliances

LOGGER = logging.getLogger(__name__)


class CSVDownloadView(AccountMixin, ListView):

    content_type = 'text/csv'
    basename = 'download'
    headings = []
    filter_backends = []

    @staticmethod
    def encode(text):
        if six.PY2:
            return force_str(text).encode('utf-8')
        return force_str(text)

    @staticmethod
    def decorate_queryset(queryset):
        return queryset

    def filter_queryset(self, queryset):
        """
        Recreating a GenericAPIView.filter_queryset functionality here
        """
        # creating a DRF-compatible request object
        request = Request(self.request)
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(request, queryset, self)
        return queryset

    def get(self, *args, **kwargs): #pylint: disable=unused-argument
        if six.PY2:
            content = io.BytesIO()
        else:
            content = io.StringIO()
        csv_writer = csv.writer(content)
        csv_writer.writerow([self.encode(head)
            for head in self.get_headings()])
        qs = self.decorate_queryset(self.filter_queryset(self.get_queryset()))
        for record in qs:
            csv_writer.writerow(self.queryrow_to_columns(record))
        content.seek(0)
        resp = HttpResponse(content, content_type=self.content_type)
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())
        return resp

    def get_headings(self):
        return self.headings

    def get_queryset(self):
        # Note: this should take the same arguments as for
        # Searchable and SortableListMixin in "extra_views"
        raise NotImplementedError

    def get_filename(self):
        return datetime_or_now().strftime(self.basename + '-%Y%m%d.csv')

    def queryrow_to_columns(self, record):
        raise NotImplementedError


class FullReportPPTXView(CampaignMixin, AccountMixin, TemplateView):
    """
    Download full report as a .pptx presentation
    """
    content_type = \
     'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    basename = 'report'
    is_percentage = True
    title = 'Full Report'

    def get_data(self, title=None):
        #pylint:disable=unused-argument
        return []

    def get_filename(self):
        return datetime_or_now().strftime(
            self.account.slug + '-' + self.basename + '-%Y%m%d.pptx')

    def get_template_names(self):
        candidates = [
            os.path.join('app', 'reporting', '%s.pptx' % self.campaign),
            os.path.join('app', 'reporting', '%s.pptx' % self.basename)]
        return candidates + super(FullReportPPTXView, self).get_template_names()

    def get(self, request, *args, **kwargs):
        #pylint: disable=unused-argument,too-many-locals,too-many-nested-blocks

        # Prepares the result file
        content = io.BytesIO()
        candidate = None
        for candidate_template in self.get_template_names():
            for template_dir in settings.TEMPLATES_DIRS:
                full_path = os.path.join(template_dir, candidate_template)
                if os.path.exists(full_path):
                    candidate = full_path
                    break
            if candidate:
                break
        if candidate:
            data = {}
            with open(candidate, 'rb') as reporting_file:
                prs = Presentation(reporting_file)
            for slide in prs.slides:
                LOGGER.debug("slide=%s", slide)
                for shape in slide.shapes:
                    LOGGER.debug("\tshape=%s", shape)
                    if isinstance(shape, Shape):
                        LOGGER.debug("\t- text=%s", shape.text)
                        if '{{title}}' in shape.text:
                            shape.text = shape.text.replace(
                                '{{title}}', self.title)
                        if '{{accounts}}' in shape.text:
                            shape.text = shape.text.replace(
                                '{{accounts}}', ', '.join([
                                self.account.printable_name] + [
                                alliance.printable_name for alliance
                                    in get_alliances(self.account)]))
                        if (self.is_percentage and
                            shape.text == "(nb suppliers)"):
                            shape.text = "(% of suppliers)"
                    elif isinstance(shape, GraphicFrame):
                        # We found the chart's container
                        try:
                            chart = shape.chart
                            if chart.has_title:
                                data = self.get_data(chart.chart_title)
                            else:
                                data = self.get_data()
                            chart_data = CategoryChartData()
                            labels = False
                            for serie in data:
                                if not labels:
                                    for point in serie.get('values'):
                                        label = point[0]
                                        if isinstance(label, datetime.datetime):
                                            label = label.date()
                                        chart_data.add_category(label)
                                    labels = True
                                chart_data.add_series(
                                serie.get('slug'),
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


class BenchmarkPPTXView(BenchmarkMixin, FullReportPPTXView):
    """
    Download benchmarks a .pptx presentation
    """
    basename = 'benchmarks'

    @property
    def question(self):
        if not hasattr(self, '_question'):
            self._question = get_object_or_404(
                get_question_model(), path=self.db_path)
        return self._question

    def get_template_names(self):
        if self.question.default_unit.system == Unit.SYSTEM_DATETIME:
            return [os.path.join('app', 'reporting', 'column.pptx')]
        return [os.path.join('app', 'reporting', 'doughnut.pptx')]

    @property
    def title(self):
        #pylint:disable=attribute-defined-outside-init
        if not hasattr(self, '_title'):
            question = get_question_model().objects.filter(
                path=self.db_path).first()
            if question:
                self._title = question.title
        return self._title

    def get_data(self, title=None):
        questions = self.get_questions(self.db_path)
        results = questions[0].get('benchmarks', [])
        if self.question.default_unit.system != Unit.SYSTEM_DATETIME:
            return reversed(results)
        return results


class TemplateXLSXView(AccountMixin, TimersMixin, ListView):

    content_type = \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    basename = 'download'
    filter_backends = []
    title = ""

    def __init__(self, **kwargs):
        super(TemplateXLSXView, self).__init__(**kwargs)
        self.wsheet = None

    def decorate_queryset(self, queryset):
        return queryset

    def filter_queryset(self, queryset):
        """
        Given a queryset, filter it with whichever filter backend is in use.
        """
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_filename(self):
        return datetime_or_now().strftime(
            self.account.slug + '-' + self.basename + '-%Y%m%d.xlsx')

    def get_headings(self):
        return []

    @staticmethod
    def get_indent_question(depth=0):
        return "  " * depth

    @staticmethod
    def get_indent_heading(depth=0):
        return "  " * depth

    def writerow(self, rec):
        pass

    def get(self, request, *args, **kwargs):
        #pylint: disable=unused-argument
        self._start_time()
        wbook = Workbook()

        # Populate the Total sheet
        self.wsheet = wbook.active
        self.wsheet.title = as_valid_sheet_title(self.title)

        queryset = self.filter_queryset(self.get_queryset())
        self.decorate_queryset(queryset)

        self.wsheet.append(self.get_headings())
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


class PortfolioAccessiblesXLSXView(PortfolioAccessibleSamplesMixin,
                                   TemplateXLSXView):
    """
    Download scores of all reporting entities as an Excel spreadsheet.
    """
    basename = 'accessibles'
    title = "Accessibles responses"

    def get_headings(self):
        return ['Supplier name', 'Tags'] + list(reversed(self.labels))

    def writerow(self, rec):
        row = [rec.printable_name, ", ".join(get_extra(rec, 'tags', []))]
        for val in reversed(rec.values):
            if val[1] in (self.REPORTING_COMPLETED, self.REPORTING_RESPONDED):
                # WORKAROUND:
                # "Excel does not support timezones in datetimes. The tzinfo
                #  in the datetime/time object must be set to None."
                row += [val[0].date()]
            elif val[1] in (self.REPORTING_DECLINED,):
                row += ['no-response']
            else:
                row += [val[1]]
        self.wsheet.append(row)


class PortfolioEngagementXLSXView(PortfolioEngagementMixin, TemplateXLSXView):
    """
    Download scores of all reporting entities as an Excel spreadsheet.
    """
    basename = 'engagement'
    title = "Engagement"

    def get_headings(self):
        return [
            'Supplier name',
            'Tags',
            'Status',
            'Last update',
            'Last reminder',
            'Added']

    def writerow(self, rec):
        reporting_statuses = dict(EngagementSerializer.REPORTING_STATUSES)
        row = [rec.printable_name,
               ", ".join(get_extra(rec, 'tags', [])),
               reporting_statuses[rec.reporting_status],
               rec.last_activity_at.date() if rec.last_activity_at else "",
               "",
               rec.requested_at.date() if rec.requested_at else ""]
        self.wsheet.append(row)


class LongFormatCSVView(CampaignMixin, AccountsNominativeQuerysetMixin,
                        CSVDownloadView):
    """
    Download raw data in format suitable for OLAP Software
    """
    headings = ['profile', 'created_at', 'unit', 'measured', 'path', 'title']
    filter_backends = [DateRangeFilter]

    def __init__(self, **kwargs):
        super(LongFormatCSVView, self).__init__(**kwargs)
        self._choices = {}

    def get_queryset(self):
        requested_accounts = self.requested_accounts.filter(
            grant_key__isnull=True)
        queryset = Answer.objects.filter(
            Q(unit_id=F('question__default_unit_id')) |
        Q(unit_id=F('question__default_unit__source_equivalences__target_id')),
            sample__in=get_completed_assessments_at_by(
                self.campaign, start_at=self.start_at, ends_at=self.ends_at,
                accounts=requested_accounts)).distinct().select_related(
                'sample__account', 'question', 'question__content', 'unit')
        return queryset

    def queryrow_to_columns(self, record):
        measured = record.measured
        if record.unit.system == Unit.SYSTEM_ENUMERATED:
            if not hasattr(self, '_choices'):
                self._choices = {}
            choices = self._choices.get(record.unit.slug)
            if not choices:
                choices = {choice.pk: choice.text
                    for choice in Choice.objects.filter(
                        unit=record.unit)}
                self._choices.update({record.unit.slug: choices})
            measured = choices.get(record.measured)
        elif record.unit.system not in Unit.NUMERICAL_SYSTEMS:
            measured = self.encode(
                Choice.objects.get(pk=measured).text)
        row = [
            record.sample.account.slug,
            record.created_at.date(),
            record.unit.slug,
            measured,
            record.question.path,
            self.encode(record.question.title)
        ]
        return row
