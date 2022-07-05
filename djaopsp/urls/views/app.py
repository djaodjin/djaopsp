# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path
from deployutils.apps.django.redirects import AccountRedirectView
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)

from ...views.app import AppView


urlpatterns = [
    path(r'<slug:profile>/',
         AppView.as_view(), name='app'),
    path(r'',
        AccountRedirectView.as_view(
            pattern_name='app',
            account_url_kwarg='profile',
            new_account_url=site_url('/users/roles/accept/')),
        name='app_redirect'),
]
