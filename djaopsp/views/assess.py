# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import datetime, json, logging
from io import BytesIO

from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from django.core.files.storage import get_storage_class
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from django.views.generic.base import (ContextMixin, RedirectView,
    TemplateResponseMixin, TemplateView)
from django.template.defaultfilters import slugify
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from survey.helpers import get_extra
from survey.models import Choice, EditableFilter
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
            'units': {}
        })
        for unit_slug in ('verifiability', 'supporting-document',
                          'completeness'):
            context['units'].update({
                unit_slug.replace('-', '_'): Choice.objects.filter(
                    unit__slug=unit_slug).order_by('rank')})
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
            self.get_editable_filter_context(context, '/sustainability/environmental-reporting/ghg-emissions-reporting/ghg-emissions-scope1-measured/ghg-emissions-scope1',
                    title='Scope1 Stationary Combustion')
            self.get_editable_filter_context(context, '/sustainability/environmental-reporting/ghg-emissions-reporting/ghg-emissions-scope1-measured/ghg-emissions-scope1',
                    title='Scope1 Mobile Combustion')
            self.get_editable_filter_context(context, '/sustainability/environmental-reporting/ghg-emissions-reporting/ghg-emissions-scope1-measured/ghg-emissions-scope1',
                    title='Scope1 Refrigerants')
            self.get_editable_filter_context(context, '/sustainability/environmental-reporting/ghg-emissions-reporting/ghg-emissions-scope1-measured/ghg-emissions-scope2')
            self.get_editable_filter_context(context, '/sustainability/environmental-reporting/ghg-emissions-reporting/ghg-emissions-scope3-details/ghg-emissions-scope3-measured/ghg-emissions-scope3')
        elif metric == 'waste':
            self.get_editable_filter_context(context, '/sustainability/environmental-reporting/waste-reporting/waste-measured/hazardous-waste')
            self.get_editable_filter_context(context, '/sustainability/environmental-reporting/waste-reporting/waste-measured/non-hazardous-waste')
            self.get_editable_filter_context(context, '/sustainability/environmental-reporting/waste-reporting/waste-measured/waste-recycled')
        elif metric == 'water':
            self.get_editable_filter_context(context, '/sustainability/environmental-reporting/water-reporting/water-measured/water-withdrawn')
            self.get_editable_filter_context(context, '/sustainability/environmental-reporting/water-reporting/water-measured/water-discharged')
            self.get_editable_filter_context(context, '/sustainability/environmental-reporting/water-reporting/water-measured/water-recycled')
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
        return [self.sample.account.printable_name,
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
        points = None
        comments = ""
        if answers:
            for answer in answers:
                unit = answer.get('unit')
                if unit and default_unit and unit.slug == default_unit:
                    primary_assessed = answer.get('measured')
                    continue
                if unit and unit.slug == 'freetext': #XXX
                    comments = answer.get('measured')
                if unit and unit.slug == 'points': #XXX
                    points = float(answer.get('measured'))
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
            self.sample.account.slug, self.campaign.slug))


class AssessPracticesPPTXView(AssessmentContentMixin, ListView):
    """
    Allows downloading an assessment as a PPTX
    """

    def __init__(self):
        super().__init__()
        self.prs = Presentation()
        self.template_config = {
            "background_color": [255, 255, 255],
            "title_font": "Arial",
            "title_font_size": 18,
            "title_font_color": [42, 87, 141],
            "body_font": "Calibri",
            "body_font_size": 12,
            "left": 1,
            "top": 2,
            "width": 8,
            "height": 0.5,
        }
        self.update_template_settings()
        self.current_slide = None
        self.title_hierarchy = {0: None, 1: None, 2: None, 3: None, 4: None, 5: None}
        self.basename = 'practices'

    def update_template_settings(self):
        self.left = Inches(self.template_config["left"])
        self.top = Inches(self.template_config["top"])
        self.width = Inches(self.template_config["width"])
        self.height = Inches(self.template_config["height"])

    def apply_background(self, slide):
        bg_color = self.template_config.get("background_color")
        if bg_color:
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = RGBColor(*bg_color)

    def format_slide_title(self, title_shape):
        title_shape.text_frame.paragraphs[0].font.name = \
            self.template_config["title_font"]
        title_shape.text_frame.paragraphs[0].font.size = Pt(
            self.template_config["title_font_size"])
        title_shape.text_frame.paragraphs[0].font.bold = True
        title_shape.text_frame.paragraphs[0].font.color.rgb = RGBColor(
            *self.template_config["title_font_color"])

    def format_entry_content(self, entry):
        content = []
        try:
            default_unit_slug = entry['default_unit'].slug
        except AttributeError:
            default_unit_slug = entry.get('default_unit', {}).get('slug', "")

        answers = entry.get('answers', [])
        primary_assessed = None
        primary_planned = None
        points = None
        comments = ""

        for answer in answers:
            try:
                unit_slug = answer['unit'].slug
            except AttributeError:
                unit_slug = ""

            measured = answer.get('measured')
            if unit_slug == default_unit_slug:
                primary_assessed = measured
            elif unit_slug == 'freetext':
                comments = measured
            elif unit_slug == 'points':
                points = float(measured) if measured else None

        planned = entry.get('planned', [])
        for plan in planned:
            try:
                unit_slug = plan['unit'].slug
            except AttributeError:
                unit_slug = ""

            if unit_slug == default_unit_slug:
                primary_planned = plan.get('measured')

        title = entry['title']
        content.append(f"Title: {title}")
        opportunity = entry.get('opportunity')
        rates = entry.get('rate', {})
        nb_respondents = entry.get('nb_respondents', {})
        extra = entry.get('extra')
        avg_value = 0

        if primary_assessed is not None:
            content.append(f"Assessed: {primary_assessed}")
        if primary_planned is not None:
            content.append(f"Planned: {primary_planned}")
        if points is not None:
            content.append(f"Points: {points}")
        if comments:
            content.append(f"Comments: {comments}")
        if opportunity:
            content.append(f"Opportunity: {opportunity}")
        if nb_respondents:
            content.append(f"Number of respondents: {nb_respondents}")
        if rates:
            for choice, value in rates.items():
                content.append(f"{choice}: {value}")
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
                content.append(f"Environmental value: {environmental_value}")
                content.append(f"Business value: {business_value}")
                content.append(f"Profitability: {profitability}")
                content.append(f"Implementation Ease: {implementation_ease}")
                content.append(f"Average Value: {avg_value}")

        return "\n".join(content)


    def add_new_slide(self, presentation, title):
        self.top = Inches(self.template_config["top"])
        slide_layout = presentation.slide_layouts[5]
        slide = presentation.slides.add_slide(slide_layout)
        self.apply_background(slide)
        title_shape = slide.shapes.title
        title_shape.text = title
        self.format_slide_title(title_shape)
        return slide

    def add_content_to_slide(self, slide, entry):
        textbox = slide.shapes.add_textbox(self.left, self.top, self.width, self.height)
        text_frame = textbox.text_frame
        text_frame.word_wrap = True
        content = self.format_entry_content(entry)

        for line in content.split("\n"):
            p = text_frame.add_paragraph()

            if ": " in line:
                prefix, rest = line.split(": ", 1)
                self.add_text_run(p, prefix + ":", bold=True)
            else:
                rest = line

            self.add_text_run(p, rest)

    def add_text_run(self, paragraph, text, bold=False):
        run = paragraph.add_run()
        run.text = text
        run.font.bold = bold
        run.font.name = self.template_config["body_font"]
        run.font.size = Pt(self.template_config["body_font_size"])

    def add_extra_content_to_title_slide(self, slide, extra_values):
        for key, value in extra_values.items():
            textbox = slide.shapes.add_textbox(self.left, self.top, self.width, self.height)
            text_frame = textbox.text_frame
            text_frame.word_wrap = True

            if key and value:
                p = text_frame.add_paragraph()
                p.text = f"{key}: {value}"
                for run in p.runs:
                    run.font.name = self.template_config["body_font"]
                    run.font.size = Pt(self.template_config["body_font_size"])

            self.top += self.height

    def get(self, request, *args, **kwargs):
        self.current_slide = None
        queryset = self.get_queryset()

        for entry in queryset:
            indent_level = entry['indent']
            title = entry['title']

            if indent_level > 1:
                self.title_hierarchy[indent_level] = title
                for higher_level in range(indent_level + 1, 6):
                    self.title_hierarchy[higher_level] = None

                if 'answers' in entry:
                    title_parts = [self.title_hierarchy[level] for level in range(1, indent_level) if self.title_hierarchy[level] is not None]
                    composed_title = ' - '.join(title_parts)
                    self.current_slide = self.add_new_slide(self.prs, composed_title)
                    self.add_content_to_slide(self.current_slide, entry)

            elif indent_level == 0:
                self.current_slide = self.add_new_slide(self.prs, title)
                extra_values = {
                    'Campaign': self.sample.campaign.title,
                    'Created at': self.sample.created_at.date(),
                    'Campaign Creator': self.sample.account.full_name,
                    'Normalized score': entry.get('normalized_score'),
                }
                self.add_extra_content_to_title_slide(self.current_slide, extra_values)

            elif indent_level == 1:
                self.current_slide = self.add_new_slide(self.prs, title)
                self.title_hierarchy[1] = title
                for higher_level in range(2, 6):
                    self.title_hierarchy[higher_level] = None
        ppt_io = BytesIO()
        self.prs.save(ppt_io)
        ppt_io.seek(0)
        filename = self.get_filename()
        response = HttpResponse(
            ppt_io,
            content_type=self.content_type)
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    def get_filename(self):
        return datetime_or_now().strftime("%s-%s-%%Y%%m%%d.pptx" % (
            self.sample.account.slug, self.campaign.slug))
