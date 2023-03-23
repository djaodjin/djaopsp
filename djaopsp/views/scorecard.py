# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

import logging

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
from ..mixins import AccountMixin, ReportMixin
from ..utils import (get_highlights, get_summary_performance,
    get_latest_active_assessments)


LOGGER = logging.getLogger(__name__)


class ScorecardRedirectForm(forms.Form):

    campaign = forms.CharField()


class ScorecardRedirectView(AccountMixin, FormMixin, TemplateResponseMixin,
                            RedirectView):
    """
    Redirects to the latest scorecard page
    """
    template_name = 'app/scorecard/redirects.html'
    form_class = ScorecardRedirectForm
    breadcrumb_url = 'scorecard'

    def create_sample(self, campaign):
        account_model = get_account_model()
        with transaction.atomic():
            #pylint:disable=unused-variable
            if isinstance(self.account, account_model):
                account = self.account
            else:
                account, unused = account_model.objects.get_or_create(
                    slug=str(self.account))
            # XXX Whenever Sample.campaign_id is null, the survey APIs
            # will not behave properly.
            sample, created = Sample.objects.get_or_create(
                account=account, campaign=campaign, is_frozen=False,
                extra__isnull=True)
        return sample

    def form_valid(self, form):
        try:
            campaign = self.campaign_candidates.get(
                slug=form.cleaned_data['campaign'])
        except Campaign.DoesNotExist:
            raise Http404('No candidate campaign matches %(campaign)s.' % {
                'campaign': form.cleaned_data['campaign']})
        sample = self.create_sample(campaign)
        kwargs = {
            self.account_url_kwarg: self.account,
            'sample': sample
        }
        return HttpResponseRedirect(self.get_redirect_url(**kwargs))

    def get_redirect_url(self, *args, **kwargs):
        return reverse(self.breadcrumb_url, kwargs=kwargs)

    def get(self, request, *args, **kwargs):
        candidates = get_latest_active_assessments(self.account)

        redirects = []
        for sample in candidates:
            # We insured that all candidates are the prefixed
            # content node at this point.
            kwargs.update({'sample': sample})
            url = self.get_redirect_url(*args, **kwargs)
            print_name = sample.campaign.title
            redirects += [(url, print_name)]

        if len(redirects) > 1 or len(self.campaign_candidates) > 1:
            context = self.get_context_data(**kwargs)
            context.update({
                'redirects': redirects,
                'campaigns': self.campaign_candidates
            })
            return self.render_to_response(context)

        if not redirects:
            if not self.campaign_candidates:
                raise Http404(
                  "No campaigns available for %(account)s" % str(self.account))
            sample = self.create_sample(self.campaign_candidates[0])
            kwargs.update({'sample': sample})
            url = self.get_redirect_url(*args, **kwargs)
            print_name = sample.campaign.title
            redirects += [(url, print_name)]
        return super(ScorecardRedirectView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)


class ScorecardIndexView(ReportMixin, TemplateView):
    """
    Profile scorecard page
    """
    template_name = 'app/scorecard/index.html'
    URL_PATH_SEP = '/'

    @property
    def campaign_mandatory_segments(self):
        #pylint:disable=attribute-defined-outside-init
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
        #pylint:disable=attribute-defined-outside-init
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
        candidates += super(ScorecardIndexView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(ScorecardIndexView, self).get_context_data(**kwargs)
        context.update({
            'highlights': get_highlights(self.sample),
            'is_mandatory_segment_present': self.is_mandatory_segment_present,
            'segments_candidates': self.segments_candidates,
            'summary_performance': get_summary_performance(self.sample)
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
            'api_account_benchmark': reverse('api_benchmark_index',
                args=(self.account, self.sample)),
            # These URLs can't be accessed by profiles the sample was shared
            # with. They must use ``sample.account``.
            'scorecard_share': reverse('share',
                args=(self.sample.account, self.sample)),
            'assess_base': reverse('assess_practices',
                args=(self.sample.account, self.sample, '-'))[:-2],
            'api_assessment_freeze': reverse('survey_api_sample_freeze_index',
                args=(self.sample.account, self.sample)),
            'api_assessment_reset': reverse('survey_api_sample_reset_index',
                args=(self.sample.account, self.sample)),
            # The Vue component will use the fully resolved URL to show
            # if it is an external link or an uploaded document.
            'api_asset_upload_complete': self.request.build_absolute_uri(
                reverse('pages_api_upload_asset', args=(self.sample.account,))),
        })
        return context


class ScorecardHistoryView(AccountMixin, TemplateView):
    """
    Profile scorecard history page
    """
    template_name = 'app/scorecard/history.html'

    def get_context_data(self, **kwargs):
        context = super(ScorecardHistoryView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_historical_assessments': reverse('api_historical_assessments',
                    args=(self.account,)),
            'scorecard_base': reverse('scorecard_redirect',
                    args=(self.account,)),
        })
        return context


class DataValuesView(AccountMixin, TemplateView):
    """
    Data points tracked so far
    """
    template_name = 'app/track/values.html'

    def get_context_data(self, **kwargs):
        context = super(DataValuesView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_data_values': reverse('survey_api_accounts_values',
                    args=(self.account,)),
        })
        return context
