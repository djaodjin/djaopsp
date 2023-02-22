# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.apps.django.redirects import AccountRedirectView
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from django import forms
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect, Http404
from django.views.generic.base import (RedirectView, TemplateResponseMixin,
    TemplateView)
from django.views.generic.edit import FormMixin
from survey.models import Answer, Campaign, Sample
from survey.utils import get_account_model


from ..compat import is_authenticated, reverse
from ..mixins import AccountMixin
from ..notifications import signals
from ..utils import (get_latest_active_assessments,
    get_latest_completed_assessment)

LOGGER = logging.getLogger(__name__)


class AppView(AccountMixin, TemplateView):
    """
    Homepage for an organization.
    """
    template_name = 'app/index.html'

    @property
    def unlock_editors(self):
        is_broker = bool(self.accessible_profiles & settings.UNLOCK_BROKERS)
        accessible_plans = {plan['slug']
            for plan in self.get_accessible_plans(self.request,
                    profile=str(self.account) # if we don't convert to `str`,
                                              # the equality will be `False`.
            )}
        unlock_editors = getattr(settings, 'UNLOCK_EDITORS', [])
        return (is_broker or not unlock_editors or
            accessible_plans & unlock_editors)

    @property
    def unlock_portfolios(self):
        is_broker = bool(self.accessible_profiles & settings.UNLOCK_BROKERS)
        accessible_plans = {plan['slug']
            for plan in self.get_accessible_plans(self.request,
                    profile=str(self.account) # if we don't convert to `str`,
                                              # the equality will be `False`.
            )}
        unlock_portfolios = getattr(settings, 'UNLOCK_PORTFOLIOS', [])
        return (is_broker or not unlock_portfolios or
            accessible_plans & unlock_portfolios)

    def get_template_names(self):
        candidates = ['app/%s.html' % self.account.slug]
        candidates += super(AppView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(AppView, self).get_context_data(**kwargs)
        context.update({
            'latest_completed_assessment': get_latest_completed_assessment(
                self.account),
            'active_assessment_in_progress': Answer.objects.filter(
                sample__in=get_latest_active_assessments(self.account)).exists()
        })
        update_context_urls(context, {
            'pages_index': reverse('pages_index'),
            'track_metrics': reverse('track_metrics_index',
                args=(self.account,)),
            'scorecard_history': reverse('scorecard_history',
                args=(self.account,)),
            'profile_getstarted': reverse('profile_getstarted',
                args=(self.account,)),
        })
        if self.unlock_portfolios:
            update_context_urls(context, {
                'portfolio_analyze': reverse('portfolio_analyze', args=(
                    self.account,)),
                'portfolio_engage': reverse('portfolio_engage', args=(
                    self.account,)),
            })
        if self.unlock_editors:
            update_context_urls(context, {
                'pages_editables_index': reverse(
                    'pages_editables_index', args=(self.account,)),
                'survey_campaign_list': reverse(
                    'survey_campaign_list', args=(self.account,)),
            })
        return context


class ScorecardRedirectForm(forms.Form):

    campaign = forms.CharField()


class GetStartedProfileView(AccountMixin, FormMixin, TemplateResponseMixin,
                            RedirectView):
    """
    Redirects to the latest scorecard page
    """
    # XXX This code was copy/pasted from ScorecardRedirectView and mixed
    # with SourcingAssessRedirectView.
    template_name = 'app/scorecard/redirects.html'
    form_class = ScorecardRedirectForm

    @property
    def campaign_candidates(self):
        """
        Returns a list of campaigns that can an account
        can answer against.
        """
        if not hasattr(self, '_campaign_candidates'):
            self._campaign_candidates = super(
                GetStartedProfileView, self).campaign_candidates
            campaign = self.kwargs.get('campaign')
            if campaign:
                self._campaign_candidates = self._campaign_candidates.filter(
                slug=campaign)
        return self._campaign_candidates

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
        reverse_kwargs = {
            self.account_url_kwarg: kwargs.get(self.account_url_kwarg),
            'sample': kwargs.get('sample')
        }
        path = kwargs.get('path')
        if path:
            reverse_kwargs.update({'path': path})
            return reverse('assess_practices', kwargs=reverse_kwargs)
        return reverse('assess_redirect', kwargs=reverse_kwargs)

    def get(self, request, *args, **kwargs):
        campaign = kwargs.get('campaign')
        candidates = get_latest_active_assessments(
            self.account, campaign=campaign)

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
        return super(GetStartedProfileView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)


class GetStartedView(AccountRedirectView):
    """
    Redirects to assess a specific campaign section.

    The profile is unknown. The user might be anonymous.
    """
    account_url_kwarg = 'profile'

    def get_redirect_url(self, *args, **kwargs):
        """
        Return the URL redirect to. Keyword arguments from the URL pattern
        match generating the redirect request are provided as kwargs to this
        method.
        """
        campaign = kwargs.get('campaign')
        path = kwargs.get('path')
        if campaign:
            if path:
                url = reverse('profile_getstarted_campaign_path',
                    args=args, kwargs=kwargs)
            else:
                url = reverse('profile_getstarted_campaign',
                    args=args, kwargs=kwargs)
        else:
            url = reverse('profile_getstarted',
                args=args, kwargs=kwargs)
        args = self.request.META.get('QUERY_STRING', '')
        if args and self.query_string:
            url = "%s?%s" % (url, args)
        return url

    def get(self, request, *args, **kwargs):
        if not is_authenticated(self.request):
            return HttpResponseRedirect(
                site_url('/activate/?next=') + self.request.path)
        return super(GetStartedView, self).get(request, *args, **kwargs)
