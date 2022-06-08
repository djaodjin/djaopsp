# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import json, logging

from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import datetime_or_now, update_context_urls
from django.views.generic import TemplateView
from django.template.defaultfilters import slugify
from survey.models import EditableFilter

from .downloads import PracticesSpreadsheetView
from ..api.samples import AssessmentContentMixin
from ..compat import reverse
from ..mixins import AccountMixin, SegmentReportMixin


LOGGER = logging.getLogger(__name__)


class AssessPracticesView(SegmentReportMixin, TemplateView):
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
        context.update({
            'prefix': self.full_path,
            'nb_answers': self.nb_answers,
            'nb_questions': self.nb_questions,
        })
        if not self.sample.is_frozen:
            context.update({
                'nb_required_answers': self.nb_required_answers,
                'nb_required_questions': self.nb_required_questions,
            })
        update_context_urls(context, {
            'pages_index': reverse('pages_index'),
            'track_metrics_index': reverse(
                'track_metrics_index', args=(self.account,)),
            'download': reverse('assess_download', args=(
                self.account, self.sample)),
            'api_content': reverse('api_sample_content',
                args=(self.account, self.sample,
                      self.full_path.lstrip(self.URL_PATH_SEP))),
            'api_assessment_sample': reverse(
                'survey_api_sample', args=(self.account, self.sample))
        })
        # Upload supporting documents
        update_context_urls(context, {
# XXX       'asset_upload_start': site_url("api/auth/tokens/realms/%s" % self.account),
            'api_asset_upload_start': reverse('pages_api_upload_asset',
                args=(self.account,)),
            'api_asset_upload_complete': reverse('pages_api_upload_asset',
                args=(self.account,)),
# XXX       'api_aggregate_metric_base': reverse('survey_api_aggregate_metric_base', args=(self.account,)),
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
        title = 'GHG Emissions Scope 1'
        tag = slugify(title)
        try:
            editable_filter = EditableFilter.objects.get(
                account=self.account, extra__contains=tag)
        except EditableFilter.DoesNotExist:
            editable_filter = EditableFilter.objects.create(
                account=self.account,
                title=title,
                extra=json.dumps({'tags': [tag]}))
        update_context_urls(context, {
            'api_track_ghg_emissions_scope1': reverse(
                'survey_api_accounts_filter',
                args=(self.account, editable_filter.slug,))
        })
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
                    primary_assessed = answer.get('measured')
                    continue
                if unit and unit.slug == 'freetext': #XXX
                    comments = answer.get('measured')
        planned = entry.get('planned')
        if planned:
            for answer in planned:
                unit = answer.get('unit')
                if unit and unit.slug == entry.get(
                        'default_unit', {}).get('slug'):
                    primary_planned = answer.get('measured')
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
