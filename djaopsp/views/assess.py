# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import datetime, json, logging

from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import datetime_or_now, update_context_urls
from django.core.files.storage import get_storage_class
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.base import (ContextMixin, RedirectView,
    TemplateResponseMixin, TemplateView)
from django.template.defaultfilters import slugify
from survey.models import EditableFilter
from survey.utils import get_question_model
from survey.helpers import get_extra

from .downloads import PracticesSpreadsheetView
from ..api.samples import AssessmentContentMixin
from ..compat import reverse
from ..mixins import AccountMixin, ReportMixin, SegmentReportMixin


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
            # XXX should download PDF with actions guidance.
            'print': reverse('assess_download', args=(
                self.account, self.sample)),
            'api_content': reverse('api_sample_content',
                args=(self.account, self.sample,
                      self.full_path.lstrip(self.URL_PATH_SEP))),
            'api_assessment_sample': reverse(
                'survey_api_sample', args=(self.account, self.sample))
        })
        # Upload supporting documents
        storage_class = get_storage_class()
        if 's3boto' in storage_class.__name__.lower():
            update_context_urls(context, {
                'api_asset_upload_start': site_url(
                    "api/auth/tokens/realms/%s" % self.account),
            })
        else:
            update_context_urls(context, {
            'api_asset_upload_start': reverse('pages_api_upload_asset',
                args=(self.account,)),
            })
        update_context_urls(context, {
            'api_asset_upload_complete': self.request.build_absolute_uri(
                reverse('pages_api_upload_asset', args=(self.account,))),
            'api_aggregate_metric_base': reverse(
                'survey_api_aggregate_metric_base', args=(self.account,)),
        })
        return context


class ImprovePracticesView(AssessPracticesView):
    """
    Profile improvement targets page
    """
    template_name = 'app/improve/index.html'
    breadcrumb_url = 'improve_practices'

    def get_template_names(self):
        campaign_slug = ('sustainability'
            if self.sample.campaign.slug == 'assessment'
            else self.sample.campaign.slug)
        candidates = ['app/improve/%s.html' %  campaign_slug]
        candidates += super(ImprovePracticesView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(ImprovePracticesView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_improvement_sample': reverse('survey_api_sample', args=(
                self.account, self.improvement_sample))
        })
        return context


class AssessRedirectView(ReportMixin, TemplateResponseMixin, ContextMixin,
                         RedirectView):
    """
    Redirects to an assess page for a segment
    """
    template_name = 'app/assess/redirects.html'
    breadcrumb_url = 'assess_practices'

    def get_redirect_url(self, *args, **kwargs):
        return reverse(self.breadcrumb_url, kwargs=kwargs)

    def get(self, request, *args, **kwargs):
        candidates = self.segments_available
        if not candidates:
            return HttpResponseRedirect(
                reverse('scorecard', args=(self.account, self.sample)))

        redirects = []
        for seg in candidates:
            # We insured that all candidates are the prefixed
            # content node at this point.
            path =  seg.get('path')
            if path:
                kwargs.update({'path': path.strip('/')})
                url = self.get_redirect_url(*args, **kwargs)
                print_name = seg.get('title')
                redirects += [(url, print_name)]

        if len(redirects) > 1:
            context = self.get_context_data(**kwargs)
            context.update({
                'redirects': redirects,
            })
            return self.render_to_response(context)

        return super(AssessRedirectView, self).get(request, *args, **kwargs)


class ImproveRedirectView(AssessRedirectView):
    """
    Redirects to a targets/improve page for a segment
    """
    breadcrumb_url = 'improve_practices'


class TrackMetricsView(AccountMixin, TemplateView):
    """
    Profile metrics page
    """
    DB_PATH_SEP = '/'
    template_name = 'app/track/index.html'

    def get_template_names(self):
        candidates = []
        metric = self.kwargs.get('metric')
        if metric:
            candidates += ['app/track/%s.html' % str(metric)]
        candidates += super(TrackMetricsView, self).get_template_names()
        return candidates

    def get_editable_filter_context(self, context, path, title=None):
        question = get_object_or_404(get_question_model(), path=path)
        filter_args = Q(extra__contains=path)
        tag = None
        if not title:
            title = question.title
        else:
            tag = slugify(title)
            filter_args &= Q(extra__contains=tag)
        try:
            editable_filter = None
            for row in EditableFilter.objects.filter(
                filter_args, account=self.account):
                # Sometimes titles are prefixes/suffixes of each other.
                # ex: 'Hazardous Waste' and 'Non-Hazardous Waste'
                extra_path = get_extra(row, 'path', "")
                if path == extra_path:
                    if not tag:
                        editable_filter = row
                        break
                    extra_tags = get_extra(row, 'tags', [])
                    if tag in extra_tags:
                        editable_filter = row
                        break
            if not editable_filter:
                raise EditableFilter.DoesNotExist()
        except EditableFilter.DoesNotExist:
            extra = {'path': path}
            if tag:
                extra.update({'tags': [tag]})
            editable_filter = EditableFilter.objects.create(
                account=self.account,
                title=title,
                extra=json.dumps(extra))
        if tag:
            slug_part = tag
        else:
            slug_part = path.split(self.DB_PATH_SEP)[-1]
        api_endpoint = "api_track_%s" % slug_part.replace('-', '_')
        update_context_urls(context, {
            api_endpoint: reverse(
                'survey_api_accounts_filter',
                args=(self.account, editable_filter.slug,))
        })
        return context

    def get_context_data(self, **kwargs):
        context = super(TrackMetricsView, self).get_context_data(**kwargs)
        ends_at = datetime.date(datetime_or_now().year - 1, 12, 31)
        context.update({
            'starts_at': datetime.date(ends_at.year, 1, 1).isoformat(),
            'ends_at': ends_at.isoformat()
        })
        metric = self.kwargs.get('metric')
        if metric == 'energy-ghg-emissions':
            self.get_editable_filter_context(context, '/sustainability/data-measured/ghg-emissions-measured/ghg-emissions-totals/ghg-emissions-scope1',
                    title='Scope1 Stationary Combustion')
            self.get_editable_filter_context(context, '/sustainability/data-measured/ghg-emissions-measured/ghg-emissions-totals/ghg-emissions-scope1',
                    title='Scope1 Mobile Combustion')
            self.get_editable_filter_context(context, '/sustainability/data-measured/ghg-emissions-measured/ghg-emissions-totals/ghg-emissions-scope1',
                    title='Scope1 Refrigerants')
            self.get_editable_filter_context(context, '/sustainability/data-measured/ghg-emissions-measured/ghg-emissions-totals/ghg-emissions-scope2')
            self.get_editable_filter_context(context, '/sustainability/data-measured/ghg-emissions-measured/ghg-emissions-totals/ghg-emissions-scope3')
        elif metric == 'waste':
            self.get_editable_filter_context(context, '/sustainability/data-measured/waste-measured/hazardous-waste')
            self.get_editable_filter_context(context, '/sustainability/data-measured/waste-measured/non-hazardous-waste')
            self.get_editable_filter_context(context, '/sustainability/data-measured/waste-measured/waste-recycled')
        elif metric == 'water':
            self.get_editable_filter_context(context, '/sustainability/data-measured/water-measured/water-withdrawn')
            self.get_editable_filter_context(context, '/sustainability/data-measured/water-measured/water-discharged')
            self.get_editable_filter_context(context, '/sustainability/data-measured/water-measured/water-recycled')
        return context


class AssessPracticesXLSXView(AssessmentContentMixin, PracticesSpreadsheetView):

    def get_headings(self):
        return ['', 'Assessed', 'Planned', 'Comments',
                'Environmental', 'Ops/maintenance', 'Financial',
                'Implementation ease', 'AVERAGE VALUE']

    def format_row(self, entry):
        default_unit = entry.get('default_unit', {})
        if default_unit:
            try:
                default_unit = default_unit.slug
            except AttributeError:
                default_unit = default_unit.get('slug', "")
        answers = entry.get('answers')
        primary_assessed = None
        primary_planned = None
        comments = ""
        if answers:
            for answer in answers:
                unit = answer.get('unit')
                if unit and default_unit and unit.slug == default_unit:
                    primary_assessed = answer.get('measured')
                    continue
                if unit and unit.slug == 'freetext': #XXX
                    comments = answer.get('measured')
        planned = entry.get('planned')
        if planned:
            for answer in planned:
                unit = answer.get('unit')
                if unit and default_unit and unit.slug == default_unit:
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
