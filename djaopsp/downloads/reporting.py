# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

import io, logging

from deployutils.helpers import datetime_or_now
from deployutils.apps.django.mixins.timers import TimersMixin
from django.http import HttpResponse
from django.views.generic import ListView
from openpyxl import Workbook
from survey.helpers import get_extra

from ..api.portfolios import (PortfolioAccessibleSamplesMixin,
    PortfolioEngagementMixin)
from ..helpers import as_valid_sheet_title
from ..mixins import AccountMixin

LOGGER = logging.getLogger(__name__)


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
