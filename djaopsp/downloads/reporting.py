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
from survey.helpers import datetime_or_now, get_extra, extra_as_internal
from survey.models import Answer, Choice, Portfolio, Sample, Unit
from survey.utils import get_question_model

from .. import humanize
from ..api.serializers import EngagementSerializer
from ..api.portfolios import (BenchmarkMixin, CompletionRateMixin,
    DashboardAggregateMixin, EngagementStatsMixin,
    PortfolioAccessibleSamplesMixin, PortfolioEngagementMixin)
from ..compat import gettext_lazy as _
from ..helpers import as_valid_sheet_title
from ..mixins import (AccountMixin, CampaignMixin,
    AccountsNominativeQuerysetMixin)
from ..scores.base import get_top_normalized_score
from ..utils import get_alliances

LOGGER = logging.getLogger(__name__)

STAGE_BY_BUCKET = {
    '1-40': _("Adopting/ Initiating"),
    '41-60': _("Growing/ Progressing"),
    '61-80': _("Leading"),
    '81-100': _("Pioneering"),
}

def get_bucket(normalized_score):
    bucket = "1-40"
    if normalized_score:
        if normalized_score > 40.5:
            bucket = "41-60"
        if normalized_score > 60.5:
            bucket = "61-80"
        if normalized_score > 80.5:
            bucket = "81-100"
    return bucket


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
        self.csv_writer = csv.writer(content)
        self.csv_writer.writerow([self.encode(head)
            for head in self.get_headings()])
        qs = self.decorate_queryset(self.filter_queryset(self.get_queryset()))
        for record in qs:
            self.writerecord(record)
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

    def writerecord(self, record):
        table = self.queryrow_to_columns(record)
        if table:
            if isinstance(table[0], list):
                for row in table:
                    self.csv_writer.writerow(row)
            else:
                self.csv_writer.writerow(table)


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

    def get_questions_by_key(self, prefix=None, initial=None):
        #pylint:disable=unused-argument
        return initial if isinstance(initial, dict) else {}

    def get_template_names(self):
        candidates = [
            os.path.join('app', 'reporting', '%s.pptx' % self.campaign),
            os.path.join('app', 'reporting', '%s.pptx' % self.basename)]
        return candidates + super(FullReportPPTXView, self).get_template_names()

    def get(self, request, *args, **kwargs):
        #pylint: disable=unused-argument,too-many-locals,too-many-nested-blocks
        context = {
            'title': self.title,
            'accounts': ', '.join([self.account.printable_name] + [
                alliance.printable_name for alliance
                in get_alliances(self.account)]),
            'unit': "%" if self.is_percentage else "nb"
        }

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
        LOGGER.debug("use template '%s'", candidate)
        if candidate:
            with open(candidate, 'rb') as reporting_file:
                prs = Presentation(reporting_file)
            for slide in prs.slides:
                LOGGER.debug("slide=%s", slide)
                for shape in slide.shapes:
                    LOGGER.debug("\tshape=%s", shape)
                    if isinstance(shape, Shape):
                        LOGGER.debug("\t- text=%s", shape.text)
                        for key, val in context.items():
                            key_text = '{{%s}}' % key
                            if key_text in shape.text:
                                for para in shape.text_frame.paragraphs:
                                    LOGGER.debug("\t- replace %s in %s",
                                        key_text, para)
                                    para.text = para.text.replace(key_text, val)
                    elif isinstance(shape, GraphicFrame):
                        # We found the chart's container
                        try:
                            chart = shape.chart
                            if chart.has_title:
                                data = list(self.get_data(chart.chart_title))
                            else:
                                data = list(self.get_data())
                            LOGGER.debug("use data %s", data)
                            chart_data = CategoryChartData()
                            # Series might not have exactly the same labels.
                            # Thus we need to gather all defined labels first.
                            labels = set([])
                            for serie in data:
                                for point in serie.get('values'):
                                    label = point[0]
                                    if isinstance(label, datetime.datetime):
                                        label = label.date()
                                    labels |= {label}
                            labels = sorted(labels)
                            LOGGER.debug("\tlabels=%s", labels)
                            for label in labels:
                                chart_data.add_category(label)
                            # Make sure we have a value for each label before
                            # adding serie.
                            LOGGER.debug("\tseries=%s", list(data))
                            for serie in data:
                                dataset = {point[0]:point[1]
                                    for point in serie.get('values')}
                                values = []
                                for label in labels:
                                    val = dataset.get(label)
                                    values += [val if val else 0]
                                LOGGER.debug("\tadd serie '%s' with values %s",
                                    serie.get('title'), values)
                                chart_data.add_series(
                                    serie.get('title'), values)

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
            #pylint:disable=attribute-defined-outside-init
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

    def get_title(self):
        # To label benchmark data set (engaged suppliers)
        return self.account.printable_name

    def get_query_param(self, key, default_value=None):
        # XXX Workaround until overridden method in djaodjin-survey supports
        # Django HTTPRequest.
        try:
            return self.request.query_params.get(key, default_value)
        except AttributeError:
            pass
        return self.request.GET.get(key, default_value)

    def get_decorated_questions(self, prefix=None):
        return list(six.itervalues(self.get_questions_by_key(
            prefix=prefix if prefix else settings.DB_PATH_SEP)))

    def get_data(self, title=None):
        questions = self.get_decorated_questions(self.db_path)
        results = questions[0].get('benchmarks', [])
        if self.question.default_unit.system != Unit.SYSTEM_DATETIME:
            return reversed(results)
        return results


class ReportingDashboardPPTXView(DashboardAggregateMixin, FullReportPPTXView):
    """
    Download reporting dashboard as an .pptx spreadsheet.
    """
    basename = 'doughnut'

    def get_template_names(self):
        return [os.path.join('app', 'reporting', '%s.pptx' % self.basename)]

    def get_filename(self):
        return datetime_or_now().strftime(
            self.account.slug + '-' + self.basename + '-%Y%m%d.pptx')

    def get_data(self, title=None):
        data = self.get_response_data(self.request, **self.kwargs)
        return data['results']

    @property
    def title(self):
        #pylint:disable=attribute-defined-outside-init
        if not hasattr(self, '_title'):
            data = self.get_response_data(self.request, **self.kwargs)
            self._title = data['title']
        return self._title


class CompletionRatePPTXView(CompletionRateMixin, ReportingDashboardPPTXView):
    """
    Download completion rate as a .pptx presentation
    """
    basename = 'completion-rate'


class EngagementStatsPPTXView(EngagementStatsMixin, ReportingDashboardPPTXView):
    """
    Download engagement statistics as a .pptx presentation
    """

    def get_response_data(self, request, *args, **kwargs):
        resp = super(EngagementStatsPPTXView, self).get_response_data(
            request, *args, **kwargs)
        # We have to reverse the results to keep charts consistent with
        # HTML version.
        resp.update({'results': reversed(resp.get('results'))})
        return resp


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

    def get_descr(self):
        return ""

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

    def get(self, request, *args, **kwargs):
        #pylint: disable=unused-argument
        self._start_time()
        wbook = Workbook()

        # Populate the Total sheet
        self.wsheet = wbook.active
        self.wsheet.title = as_valid_sheet_title(self.title)

        queryset = self.filter_queryset(self.get_queryset())
        self.decorate_queryset(queryset)

        descr = self.get_descr()
        if descr:
            self.wsheet.append([descr])
        self.wsheet.append(self.get_headings())
        self.write_queryset(queryset)

        # Prepares the result file
        content = io.BytesIO()
        wbook.save(content)
        content.seek(0)

        resp = HttpResponse(content, content_type=self.content_type)
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())
        self._report_queries("http response created")
        return resp

    def write_queryset(self, queryset):
        for record in queryset:
            self.writerecord(record)

    def writerecord(self, record):
        table = self.queryrow_to_columns(record)
        if table:
            if isinstance(table[0], list):
                for row in table:
                    self.wsheet.append(row)
            else:
                self.wsheet.append(table)

    def queryrow_to_columns(self, record):
        raise NotImplementedError


class PortfolioAccessiblesXLSXView(PortfolioAccessibleSamplesMixin,
                                   TemplateXLSXView):
    """
    Download scores of all reporting entities as an Excel spreadsheet.
    """
    basename = 'accessibles'
    title = "Accessibles responses"

    def get_headings(self):
        labels = [str(_("Supplier No.")), str(_("Supplier name")), str(_("Tags"))]
        for label in list(reversed(self.labels)):
            labels += ["%s Score" % label]
        for label in list(reversed(self.labels)):
            labels += ["%s Status" % label]
        for label in list(reversed(self.labels)):
            labels += ["%s Completed at" % label]
        for label in list(reversed(self.labels)):
            labels += ["%s Score Range" % label]
        return labels

    def queryrow_to_columns(self, record):
        reporting_statuses = dict(humanize.REPORTING_STATUSES)
        supplier_key = get_extra(record, 'supplier_key')
        row = [str(supplier_key), record.printable_name,
            ", ".join(get_extra(record, 'tags', []))]

        # Write period-over-period normalized scores
        for val in reversed(record.values):
            state = val.state
            if state in (humanize.REPORTING_COMPLETED,
                         humanize.REPORTING_VERIFIED):
                normalized_score = get_top_normalized_score(
                    val, segments_candidates=self.segments_candidates)
                row += [
                    normalized_score if normalized_score is not None else ""]
            else:
                row += [""]

        # Write period-over-period status
        for val in reversed(record.values):
            state = val.state
            row += [reporting_statuses[state]]

        # Write period-over-period completed at
        for val in reversed(record.values):
            completed_at = val.created_at if val.pk else None
            row += [completed_at.strftime('%Y-%m-%d') if completed_at else ""]

        # Write period-over-period score buckets
        for val in reversed(record.values):
            state = val.state
            if state in (humanize.REPORTING_COMPLETED,
                         humanize.REPORTING_VERIFIED):
                normalized_score = get_top_normalized_score(
                    val, segments_candidates=self.segments_candidates)
                bucket = get_bucket(normalized_score)
                row += [bucket]
            else:
                row += [""]

        return row


class PortfolioAccessiblesLongCSVView(PortfolioAccessibleSamplesMixin,
                                      TemplateXLSXView):
    """
    Downloads year-over-year scores in long format
    """
    base_headings = ['Supplier no.', 'Supplier name',
        'TSP Score', 'Score Range', 'Score Stage']
    title = "Responses"

    def get_headings(self):
        headings = self.base_headings
        if self.period == 'monthly':
            headings += ['Month']
        else:
            headings += ['Year']
        return headings

    def get_filename(self):
        basename = "%s-suppliers" % self.account
        return datetime_or_now().strftime(basename + '-%Y%m%d.xlsx')

    def queryrow_to_columns(self, record):
        collapsed_reporting_statuses = {
            humanize.REPORTING_NO_RESPONSE: _("Invited"),
            humanize.REPORTING_NO_DATA: _("No Data"),
            humanize.REPORTING_NO_PROFILE: _("N/A"),
            humanize.REPORTING_RESPONDED: _("Not Shared"),
        }
        reporting_statuses = dict(humanize.REPORTING_STATUSES)
        table = []
        for val in reversed(record.values):
            bucket = None
            stage = None
            # Write 'Supplier No.' and 'Supplier Name'
            supplier_key = get_extra(record, 'supplier_key')
            row = [str(supplier_key), record.printable_name]
            state = val.state
            # Write 'TSP Score'
            if state in (humanize.REPORTING_COMPLETED,
                         humanize.REPORTING_VERIFIED):
                normalized_score = get_top_normalized_score(
                    val, segments_candidates=self.segments_candidates)
                bucket = get_bucket(normalized_score)
                stage = STAGE_BY_BUCKET.get(bucket)
                row += [
                    normalized_score if normalized_score is not None else ""]
            else:
                status = collapsed_reporting_statuses.get(
                    state, reporting_statuses[state])
                bucket = status
                stage = status
                row += [str(status)]

            # Write 'Score Range'
            row += [str(bucket)]
            # Write 'Score Stage'
            row += [str(stage)]
            # Write Period ('Year' or 'Month')
            if self.period == 'monthly':
                row += [val.created_at.strftime("%b %Y")]
            else:
                row += [val.created_at.year]

            table += [row]

        return table


class PortfolioEngagementXLSXView(PortfolioEngagementMixin, TemplateXLSXView):
    """
    Download scores of all reporting entities as an Excel spreadsheet.
    """
    basename = 'engagement'
    title = "Engagement"

    def get_headings(self):
        return [
            'SupplierID',
            'Profile name',
            'Tags',
            'Status',
            'Last update',
            'Last reminder',
            'Added']

    def queryrow_to_columns(self, record):
        reporting_statuses = dict(EngagementSerializer.REPORTING_STATUSES)
        supplier_key = get_extra(record, 'supplier_key')
        row = [
            supplier_key,
            record.printable_name,
            ", ".join(get_extra(record, 'tags', [])),
            reporting_statuses[record.reporting_status],
            record.last_activity_at.date() if record.last_activity_at else "",
            "",
            record.requested_at.date() if record.requested_at else ""]
        return row


class LongFormatCSVView(AccountsNominativeQuerysetMixin, CSVDownloadView):
    """
    Download raw data in format suitable for OLAP Software
    """
    headings = ['Created at', 'SupplierID', 'Profile name',
        'Measured', 'Unit', 'Question title', 'Question path']
    filter_backends = [DateRangeFilter]

    def __init__(self, **kwargs):
        super(LongFormatCSVView, self).__init__(**kwargs)
        self._choices = {}

    def get_supplier_key(self, account):
        if not hasattr(self, '_portfolio_extras'):
            extras_queryset = Portfolio.objects.filter(
                grantee=self.account,
                account_id__in=[val.pk for val in self.requested_accounts])
            self._portfolio_extras = {
                (val.grantee_id, val.account_id): extra_as_internal(val)
                for val in extras_queryset}
        return self._portfolio_extras.get(
            (self.account.pk, account.pk), {}).get('supplier_key', "")


    def get_queryset(self):
        requested_accounts = self.requested_accounts.filter(
            grant_key__isnull=True)
        queryset = Answer.objects.filter(
            Q(unit_id=F('question__default_unit_id')) |
        Q(unit_id=F('question__default_unit__source_equivalences__target_id')),
            sample__in=Sample.objects.get_completed_assessments_at_by(
                self.campaign, accounts=requested_accounts,
                start_at=self.start_at, ends_at=self.ends_at
            )).distinct().select_related('sample__account', 'question', 'unit')
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
        supplier_key = self.get_supplier_key(record.sample.account)
        row = [
            record.created_at.date(),
            supplier_key,
            record.sample.account.printable_name,
            measured,
            record.unit.slug,
            self.encode(record.question.title),
            record.question.path
        ]
        return row
