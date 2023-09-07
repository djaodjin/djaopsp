# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import datetime, json, logging

from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from django.core.files.storage import get_storage_class
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.base import (ContextMixin, RedirectView,
    TemplateResponseMixin, TemplateView)
from django.template.defaultfilters import slugify
from survey.helpers import get_extra
from survey.models import EditableFilter
from survey.queries import datetime_or_now
from survey.settings import DB_PATH_SEP, URL_PATH_SEP
from survey.utils import get_question_model

from .downloads import PracticesSpreadsheetView
from ..scores import get_score_calculator
from ..api.samples import AssessmentContentMixin
from ..compat import reverse, six
from ..mixins import AccountMixin, ReportMixin, SectionReportMixin


LOGGER = logging.getLogger(__name__)


class AssessPracticesView(SectionReportMixin, TemplateView):
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
            'api_profiles': site_url("/api/accounts/users"),
            'api_content': reverse('api_sample_content',
                args=(self.account, self.sample,
                      self.full_path.lstrip(URL_PATH_SEP))),
            'api_assessment_sample': reverse('survey_api_sample',
                args=(self.account, self.sample)),
            'api_asset_upload_complete': self.request.build_absolute_uri(
                reverse('pages_api_upload_asset', args=(self.account,))),
            'api_aggregate_metric_base': reverse(
                'survey_api_aggregate_metric_base', args=(self.account,)),
        })
        if self.path:
            url_path = self.path.lstrip(URL_PATH_SEP)
            update_context_urls(context, {
                'download': reverse('assess_download_segment', args=(
                    self.account, self.sample, url_path)),
                # XXX should download PDF with actions guidance.
                'print': reverse('assess_download', args=(
                    self.account, self.sample)),
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
            'api_asset_upload_start': self.request.build_absolute_uri(
                reverse('pages_api_upload_asset', args=(self.account,))),
            })
        return context


class ImprovePracticesView(AssessPracticesView):
    """
    Improvement planning page
    """
    template_name = 'app/improve/index.html'
    breadcrumb_url = 'improve_practices'

    def get_template_names(self):
        campaign_slug = self.sample.campaign.slug
        candidates = ['app/improve/%s.html' %  campaign_slug]
        candidates += super(ImprovePracticesView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(ImprovePracticesView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_improvement_sample': reverse('survey_api_sample', args=(
                self.account, self.improvement_sample)),
            'api_account_benchmark': reverse(
                'survey_api_sample_benchmarks',
                args=(self.account, self.sample,
                      self.full_path.lstrip(URL_PATH_SEP))),
            'print': reverse('improve_print', args=(
                self.account, self.improvement_sample))
        })
        return context


class AssessRedirectView(ReportMixin, TemplateResponseMixin, ContextMixin,
                         RedirectView):
    """
    Redirects to an assess page for a segment
    """
    breadcrumb_url = 'assess_practices'
    template_name = 'app/assess/redirects.html'

    def get_redirect_url(self, *args, **kwargs):
        return reverse(self.breadcrumb_url, kwargs=kwargs)

    def get(self, request, *args, **kwargs):
        campaign_slug = self.sample.campaign.slug
        campaign_prefix = "%s%s%s" % (
            DB_PATH_SEP, campaign_slug, DB_PATH_SEP)
        has_mandatory_segment = get_question_model().objects.filter(
            path__startswith=campaign_prefix).exists()
        if has_mandatory_segment:
            kwargs.update({'path': campaign_prefix.strip(URL_PATH_SEP)})
            url = self.get_redirect_url(*args, **kwargs)
            return HttpResponseRedirect(self.get_redirect_url(*args, **kwargs))

        candidates = self.segments_available
        if not candidates:
            return HttpResponseRedirect(
                reverse('scorecard', args=(self.account, self.sample)))

        redirects = []
        for seg in candidates:
            # We insured that all candidates are the prefixed
            # content node at this point.
            path = seg.get('path')
            if path:
                kwargs.update({'path': path.strip(URL_PATH_SEP)})
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


class ImproveRedirectView(ReportMixin, TemplateResponseMixin, ContextMixin,
                         RedirectView):
    """
    Redirects to an improvement planning page for a segment
    """
    breadcrumb_url = 'improve_practices'
    template_name = 'app/improve/redirects.html'

    def get_redirect_url(self, *args, **kwargs):
        return reverse(self.breadcrumb_url, kwargs=kwargs)

    def get(self, request, *args, **kwargs):
        campaign_slug = self.sample.campaign.slug
        campaign_prefix = "%s%s%s" % (
            DB_PATH_SEP, campaign_slug, DB_PATH_SEP)

        redirects = []
        for seg in self.segments_available:
            # We insured that all segments available are the prefixed
            # content node at this point.
            extra = seg.get('extra')
            if extra and extra.get('visibility'):
                # Prevents sections that do not lend themselves
                # to improvement planning.
                path = seg.get('path')
                if path:
                    kwargs.update({'path': path.strip(URL_PATH_SEP)})
                    url = self.get_redirect_url(*args, **kwargs)
                    print_name = seg.get('title')
                    redirects += [(url, print_name)]

        if len(redirects) == 1:
            return super(ImproveRedirectView, self).get(
                request, *args, **kwargs)

        if not self.segments_candidates:
            kwargs.update({'path': self.sample.campaign.slug})
            return super(ImproveRedirectView, self).get(
                request, *args, **kwargs)

        context = self.get_context_data(**kwargs)
        context.update({
            'redirects': redirects,
        })
        return self.render_to_response(context)


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
            slug_part = path.split(DB_PATH_SEP)[-1]
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
        #pylint:disable=line-too-long
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

    base_headers = ['', 'Assessed', 'Planned', 'Comments', 'Opportunity']

    @property
    def intrinsic_value_headers(self):
        if not hasattr(self, '_intrinsic_value_headers'):
            self._intrinsic_value_headers = []
            for seg in self.segments_available:
                prefix = seg.get('path')
                if prefix:
                    score_calculator = get_score_calculator(prefix)
                    if (score_calculator and
                        score_calculator.intrinsic_value_headers):
                        self._intrinsic_value_headers = \
                            score_calculator.intrinsic_value_headers
                        break
        return self._intrinsic_value_headers

    def get_headings(self):
        if not hasattr(self, 'units'):
            self.units = {}
        self.peer_value_headers = []
        for unit in six.itervalues(self.units):
            if (unit.system == unit.SYSTEM_ENUMERATED and
                unit.slug == 'assessment'):
                self.peer_value_headers += [
                    (unit.slug, [choice.text for choice in unit.choices])]
        headers = [] + self.base_headers
        for header in self.peer_value_headers:
            headers += header[1]
        if self.peer_value_headers:
            headers += [
                "Nb respondents",
            ]
        headers += self.intrinsic_value_headers
        return headers

    def get_title_row(self):
        return [self.account.printable_name,
            self.sample.created_at.strftime("%Y-%m-%d")]


    def format_row(self, entry, key=None):
        #pylint:disable=too-many-locals
        default_unit = entry.get('default_unit', {})
        default_unit_choices = []
        if default_unit:
            try:
                default_unit = default_unit.slug
            except AttributeError:
                default_unit_choices = default_unit.get('choices', [])
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
        # base_headers
        title = entry['title']
        if default_unit and default_unit_choices:
            subtitle = ""
            for choice in default_unit_choices:
                text = choice.get('text', "").strip()
                descr = choice.get('descr', "").strip()
                if text != descr:
                    subtitle += "\n%s - %s" % (text, descr)
            if subtitle:
                title += "\n" + subtitle
        row = [
            title,
            primary_assessed,
            primary_planned,
            comments,
            entry.get('opportunity')]

        # peer_value_headers
        for header in self.peer_value_headers:
            if default_unit and default_unit == header[0]:
                for text in header[1]:
                    row += [entry.get('rate', {}).get(text, 0)]
            else:
                for text in header[1]:
                    row += [""]
        if self.peer_value_headers:
            row += [
                entry.get('nb_respondents'),
            ]

        # intrinsic_value_headers
        avg_value = 0
        extra = entry.get('extra')
        if extra:
            intrinsic_values = extra.get('intrinsic_values')
            if intrinsic_values:
                environmental_value = intrinsic_values.get('environmental', 0)
                business_value = intrinsic_values.get('business', 0)
                profitability = intrinsic_values.get('profitability', 0)
                implementation_ease = intrinsic_values.get(
                    'implementation_ease', 0)
                avg_value = (environmental_value + business_value +
                    profitability + implementation_ease) // 4
        if avg_value:
            row += [
                environmental_value,
                business_value,
                profitability,
                implementation_ease,
                avg_value
            ]
        else:
            row += ['', '', '', '', '']
        return row

    def get_filename(self):
        return datetime_or_now().strftime("%s-%s-%%Y%%m%%d.xlsx" % (
            self.account.slug, self.campaign.slug))
