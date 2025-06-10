# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.apps.django.redirects import AccountRedirectView
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from django import forms
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.views.generic.base import TemplateView
from survey.models import Answer

from ..compat import is_authenticated, reverse
from ..mixins import AccountMixin, VisibilityMixin
from ..utils import (get_latest_active_assessments,
    get_latest_completed_assessment)
from .assess import AssessRedirectView


LOGGER = logging.getLogger(__name__)


class AppView(VisibilityMixin, TemplateView):
    """
    Homepage for a user when no profile is specified in the URL path
    """
    template_name = 'app/index.html'

    def get_context_data(self, **kwargs):
        context = super(AppView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_accounts': site_url("/api/profile"),
            'api_users': site_url("/api/users"),
            'pages_index': reverse('pages_index'),
            'api_newsfeed': reverse('api_news_feed', args=(
                self.request.user.username,)),

            'getstarted': reverse('getstarted'),
        })
        if 'practices_index' not in context.get('urls', {}):
            update_context_urls(context, {
                'practices_index': reverse('pages_index'),
            })
        return context

    def get(self, request, *args, **kwargs):
        candidates = self.get_accessible_profiles(
            request, self.get_redirect_roles(request))
        count = len(candidates)
        if count == 1:
            return HttpResponseRedirect(
                reverse('app_profile', args=(candidates[0]['slug'],)))
        return super(AppView, self).get(request, *args, **kwargs)



class ProfileAppView(AccountMixin, TemplateView):
    """
    Homepage for a profile.
    """
    template_name = ('app/index.html' if settings.FEATURES_DEBUG
        else 'app/profile.html')


    def get_template_names(self):
        candidates = ['app/%s.html' % self.account.slug]
        candidates += super(ProfileAppView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(ProfileAppView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_accounts': site_url("/api/profile"),
            'api_users': site_url("/api/users"),
            'pages_index': reverse('pages_index'),
            'getstarted': reverse('profile_getstarted', args=(self.account,)),
        })
        if 'practices_index' not in context.get('urls', {}):
            update_context_urls(context, {
                'practices_index': reverse('pages_index'),
            })
        context.update({
            'latest_completed_assessment': get_latest_completed_assessment(
                self.account),
            'active_assessment_in_progress': Answer.objects.filter(
                sample__in=get_latest_active_assessments(self.account)).exists()
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
