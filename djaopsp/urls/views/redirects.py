# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path
from deployutils.apps.django.redirects import AccountRedirectView
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)

from ...views.app import GetStartedView


urlpatterns = [
    path('app/',
        AccountRedirectView.as_view(
            pattern_name='app',
            account_url_kwarg='profile'),
        name='app_redirect'),
    path('getstarted/<slug:campaign>/<path:path>/',
        GetStartedView.as_view(), name='getstarted_campaign_path'),
    path('getstarted/<slug:campaign>/',
        GetStartedView.as_view(), name='getstarted_campaign'),
    path('getstarted/',
        GetStartedView.as_view(), name='getstarted'),
]
