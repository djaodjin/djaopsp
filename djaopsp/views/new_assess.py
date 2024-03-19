import logging

from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from django import forms
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.views.generic.base import (RedirectView, TemplateResponseMixin,
                                       TemplateView)
from django.views.generic.edit import FormMixin
from survey.models import Answer, Campaign, Sample
from survey.settings import DB_PATH_SEP
from survey.utils import get_account_model, get_question_model

from ..compat import reverse
from ..mixins import AccountMixin, SectionReportMixin, VisibilityMixin
from ..utils import (get_highlights, get_summary_performance,
                     get_latest_active_assessments)

LOGGER = logging.getLogger(__name__)

from survey.models import Choice


class NewAssessView(SectionReportMixin, TemplateView):
    """
    Profile scorecard page
    """
    template_name = 'app/new_assess/scorecard/index.html'
    URL_PATH_SEP = '/'
    breadcrumb_url = 'assess_practices'

    def get_reverse_kwargs(self):
        """
        List of kwargs taken from the url that needs to be passed through
        to ``reverse``.
        """
        return [self.account_url_kwarg, self.sample_url_kwarg,
                self.path_url_kwarg]

    @property
    def campaign_mandatory_segments(self):
        # pylint:disable=attribute-defined-outside-init
        if not hasattr(self, '_campaign_mandatory_segments'):
            self._campaign_mandatory_segments = []
            campaign_slug = self.sample.campaign.slug
            campaign_prefix = "%s%s%s" % (
                DB_PATH_SEP, campaign_slug, DB_PATH_SEP)
            if get_question_model().objects.filter(
                    path__startswith=campaign_prefix).exists():
                self._campaign_mandatory_segments = [campaign_prefix]
        return self._campaign_mandatory_segments

    @property
    def is_mandatory_segment_present(self):
        # pylint:disable=attribute-defined-outside-init
        if not hasattr(self, '_is_mandatory_segment_present'):
            filter_args = None
            for seg_path in self.campaign_mandatory_segments:
                if filter_args:
                    filter_args |= Q(question__path__startswith=seg_path)
                else:
                    filter_args = Q(question__path__startswith=seg_path)
            self._is_mandatory_segment_present = False
            if filter_args:
                queryset = Answer.objects.filter(
                    filter_args, sample=self.sample)
                self._is_mandatory_segment_present = queryset.exists()
        return self._is_mandatory_segment_present

    def get_template_names(self):
        candidates = ['app/scorecard/%s.html' % self.sample.campaign]
        candidates += super(NewAssessView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(NewAssessView, self).get_context_data(**kwargs)
        context.update({
            'prefix': self.full_path,
            'nb_answers': self.nb_answers,
            'nb_questions': self.nb_questions,
            'units': {},
            'verification_enabled': self.account in self.verifier_accounts,
            'highlights': get_highlights(self.sample),
            'is_mandatory_segment_present': self.is_mandatory_segment_present,
            'summary_performance': get_summary_performance(
                self.improvement_sample)
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
        if not self.segments_available:
            update_context_urls(context, {
                'complete': "#"  # When there are no answers yet, we want
                # to show the assess step on the scorecard.
            })
        if self.campaign_mandatory_segments:
            update_context_urls(context, {
                'assess_mandatory_segment': reverse('assess_practices',
                                                    args=(self.account, self.sample, self.sample.campaign)),
            })
        update_context_urls(context, {
            'pages_index': reverse('pages_index'),
            'scorecard_download': reverse('assess_download',
                                          args=(self.account, self.sample)),
            'survey_api_sample_answers': reverse('api_sample_content',
                                                 args=(self.account, self.sample, '-'))[:-2],
            'api_account_benchmark': reverse(
                'survey_api_sample_benchmarks_index',
                args=(self.account, self.sample)),
            # These URLs can't be accessed by profiles the sample was shared
            # with. They must use ``sample.account``.
            'assess_base': reverse('assess_practices',
                                   args=(self.sample.account, self.sample, '-'))[:-2],
            'api_assessment_freeze': reverse('survey_api_sample_freeze_index',
                                             args=(self.sample.account, self.sample)),
            'api_assessment_reset': reverse('survey_api_sample_reset_index',
                                            args=(self.sample.account, self.sample)),
            'api_assessment_notes': reverse('api_verifier_notes_index',
                                            args=(self.sample.account, self.sample)),
            # The Vue component will use the fully resolved URL to show
            # if it is an external link or an uploaded document.
            'api_asset_upload_complete': self.request.build_absolute_uri(
                reverse('pages_api_upload_asset', args=(self.sample.account,))),
            'track_metrics_index': reverse(
                'track_metrics_index', args=(self.account,)),
            'api_profiles': site_url("/api/accounts/users"),
            'api_content': reverse('api_sample_content',
                                   args=(self.account, self.sample,
                                         self.full_path.lstrip(self.URL_PATH_SEP))),
            'api_assessment_sample': reverse('survey_api_sample',
                                             args=(self.account, self.sample)),
            # 'api_asset_upload_complete': self.request.build_absolute_uri(
            #     reverse('pages_api_upload_asset', args=(self.account,))),
            'api_aggregate_metric_base': reverse(
                'survey_api_aggregate_metric_base', args=(self.account,)),
            'api_asset_upload_start': self.request.build_absolute_uri(
                reverse('pages_api_upload_asset', args=(self.account,))),

        })
        return context
