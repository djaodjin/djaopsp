# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.apps.django.redirects import AccountRedirectView
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from django import forms
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.db import transaction
from django.http import HttpResponseRedirect, Http404
from django.views.generic.base import (RedirectView, TemplateResponseMixin,
    TemplateView)
from django.views.generic.edit import FormMixin
from survey.models import Answer, Campaign, Sample
from survey.utils import get_account_model


from ..compat import is_authenticated, reverse
from ..mixins import AccountMixin
from ..utils import (get_latest_active_assessments,
    get_latest_completed_assessment)
from .assess import AssessRedirectView


LOGGER = logging.getLogger(__name__)


class AppView(AccountMixin, TemplateView):
    """
    Homepage for an organization.
    """
    template_name = 'app/index.html'

    @property
    def unlock_editors(self):
        return self.get_unlocked(getattr(settings, 'UNLOCK_EDITORS', []))

    @property
    def unlock_portfolios(self):
        return self.get_unlocked(getattr(settings, 'UNLOCK_PORTFOLIOS', []))


    def get_unlocked(self, candidates):
        is_broker = False
        site = self.request.session.get('site')
        if site:
            is_broker = bool(self.account.slug == site.get('slug'))
        accessible_plans = {plan['slug']
            for plan in self.get_accessible_plans(self.request,
                    profile=str(self.account) # if we don't convert to `str`,
                                              # the equality will be `False`.
            )}
        return (is_broker or not candidates or accessible_plans & candidates)


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
                'portfolio_track': reverse('portfolio_analyze', args=(
                    self.account,)),
                'portfolio_engage': reverse('portfolio_engage', args=(
                    self.account,)),
                'portfolio_insights': reverse('portfolio_insights', args=(
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


class GetStartedProfileView(AssessRedirectView):
    """
    Shows a list of assessment requested or in progress decorated
    with grantees whenever available.

    The list is filtered by `campaign` and section `path` whenever available
    on the URL path.
    """


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
            return HttpResponseRedirect(site_url(
                '/activate/?%s=' % REDIRECT_FIELD_NAME) + self.request.path)
        return super(GetStartedView, self).get(request, *args, **kwargs)
