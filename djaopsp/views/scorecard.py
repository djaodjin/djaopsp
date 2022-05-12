# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.helpers import update_context_urls
from django import forms
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.views.generic.base import (RedirectView, TemplateResponseMixin,
    TemplateView)
from django.views.generic.edit import FormMixin
from survey.models import Campaign, Sample
from survey.utils import get_account_model

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
                account=account, campaign=campaign, is_frozen=False)
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

    def get_template_names(self):
        candidates = ['app/scorecard/%s.html' % self.sample.campaign]
        candidates += super(ScorecardIndexView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(ScorecardIndexView, self).get_context_data(**kwargs)
        context.update({
            'segments_candidates': self.segments_candidates,
            'highlights': get_highlights(self.sample),
            'summary_performance': get_summary_performance(self.sample)
        })
        if not self.segments_available:
            update_context_urls(context, {
                'complete': "#"  # When there are no answers yet, we want
                                 # to show the assess step on the scorecard.
            })
        update_context_urls(context, {
            'pages_index': reverse('pages_index'),
            'assess_base': reverse('assess_practices',
                args=(self.account, self.sample, '-'))[:-2],
            'survey_api_sample_answers': reverse('api_sample_content',
                args=(self.account, self.sample, '-'))[:-2],
            'api_account_benchmark': reverse('api_sample_content',
                args=(self.account, self.sample, '-'))[:-2],
#XXX            'api_account_benchmark': reverse('api_benchmark',
#                args=(self.account, self.sample, '')),
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
