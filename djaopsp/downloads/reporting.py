# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

import csv, io, logging

from deployutils.helpers import datetime_or_now
from deployutils.apps.django.mixins.timers import TimersMixin
from django.db.models import Q, F
from django.http import HttpResponse
from django.views.generic import ListView
from openpyxl import Workbook
from rest_framework.request import Request
from survey.compat import force_str, six
from survey.filters import DateRangeFilter
from survey.helpers import get_extra
from survey.mixins import DateRangeContextMixin
from survey.models import Answer, Choice, Unit

from ..api.portfolios import (PortfolioAccessibleSamplesMixin,
    PortfolioEngagementMixin)
from ..helpers import as_valid_sheet_title
from ..mixins import AccountMixin, CampaignMixin
from ..queries import get_completed_assessments_at_by
from ..utils import get_requested_accounts


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


class TemplateXLSXView(AccountMixin, TimersMixin, ListView):

    content_type = \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    basename = 'download'
    title = ""

    def decorate_queryset(self, queryset):
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

        queryset = self.get_queryset()
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
        return ['Supplier name', 'Tags'] + self.labels

    def writerow(self, rec):
        row = [rec.printable_name, ", ".join(get_extra(rec, 'tags', []))]
        for val in rec.values:
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
        row = [rec.printable_name,
               ", ".join(get_extra(rec, 'tags', [])),
               rec.reporting_status,
               rec.last_activity_at.date() if rec.last_activity_at else "",
               "",
               rec.requested_at.date() if rec.requested_at else ""]
        self.wsheet.append(row)


class LongFormatCSVView(DateRangeContextMixin, CampaignMixin, CSVDownloadView):
    """
    Download raw data in format suitable for OLAP Software
    """
    headings = ['profile', 'created_at', 'unit', 'measured', 'path', 'title']
    filter_backends = [DateRangeFilter]

    def get_queryset(self):
        requested_accounts = get_requested_accounts(
            self.account, campaign=self.campaign,
            start_at=self.start_at, ends_at=self.ends_at).filter(
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
