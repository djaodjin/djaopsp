# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import logging

from deployutils.helpers import datetime_or_now, update_context_urls
from django.views.generic import TemplateView

from .downloads import PracticesSpreadsheetView
from ..api.samples import AssessmentContentMixin
from ..compat import reverse
from ..mixins import AccountMixin, ReportMixin


LOGGER = logging.getLogger(__name__)


class AssessPracticesView(ReportMixin, TemplateView):
    """
    Profile assessment page
    """
    template_name = 'app/assess/index.html'
    breadcrumb_url = 'assess_practices'

    def get_reverse_kwargs(self):
        """
        List of kwargs taken from the url that needs to be passed through
        to ``reverse``.
        """
        return [self.account_url_kwarg, self.sample_url_kwarg,
            self.path_url_kwarg]

    def get_template_names(self):
        candidates = ['app/assess/%s.html' % self.sample.campaign]
        candidates += super(AssessPracticesView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(AssessPracticesView, self).get_context_data(**kwargs)
        context.update({'prefix': self.full_path})
        update_context_urls(context, {
            'pages_index': reverse('pages_index'),
            'download': reverse('assess_download', args=(
                self.account, self.sample)),
            'api_content': reverse('api_sample_content',
                args=(self.account, self.sample,
                      self.full_path.lstrip(self.URL_PATH_SEP))),
            'api_assessment_sample': reverse(
                'survey_api_sample', args=(self.account, self.sample))
        })
        return context


class ImprovePracticesView(AssessPracticesView):
    """
    Profile improvement targets page
    """
    template_name = 'app/improve/index.html'
    breadcrumb_url = 'improve_practices'

    def get_template_names(self):
        candidates = ['app/improve/%s.html' % self.sample.campaign]
        candidates += super(ImprovePracticesView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(ImprovePracticesView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_improvement_sample': reverse('survey_api_sample', args=(
                self.account, self.improvement_sample))
        })
        return context


class TrackMetricsView(AccountMixin, TemplateView):
    """
    Profile metrics page
    """
    template_name = 'app/track/index.html'

    def get_template_names(self):
        candidates = []
        metric = self.kwargs.get('metric')
        if metric:
            candidates += ['app/track/%s.html' % str(metric)]
        candidates += super(TrackMetricsView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(TrackMetricsView, self).get_context_data(**kwargs)
        return context


class AssessPracticesXLSXView(AssessmentContentMixin, PracticesSpreadsheetView):

    def get_headings(self):
        return ['', 'Assessed', 'Planned', 'Comments',
                'Environmental', 'Ops/maintenance', 'Financial',
                'Implementation ease', 'AVERAGE VALUE']

    def format_row(self, entry):
        primary_assessed = None
        primary_planned = None
        comments = ""
        answers = entry.get('answers')
        if answers:
            for answer in answers:
                unit = answer.get('unit')
                if unit and unit.slug == entry.get(
                        'default_unit', {}).get('slug'):
                    primary_assessed =  answer.get('measured')
                    continue
                if unit and unit.slug == 'freetext': #XXX
                    comments = answer.get('measured')
        planned = entry.get('planned')
        if planned:
            for answer in planned:
                unit = answer.get('unit')
                if unit and unit.slug == entry.get(
                        'default_unit', {}).get('slug'):
                    primary_planned =  answer.get('measured')
        row = [
            entry['title'],
            primary_assessed,
            primary_planned,
            comments,
            entry.get('environmental_value'),
            entry.get('business_value'),
            entry.get('profitability'),
            entry.get('implementation_ease'),
            entry.get('avg_value')
        ]
        return row

    def get_filename(self):
        return datetime_or_now().strftime("%s-%s-%%Y%%m%%d.xlsx" % (
            self.account.slug, self.campaign.slug))
