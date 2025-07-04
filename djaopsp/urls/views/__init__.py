# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.conf import settings
from django.urls import path, include
from django.views.generic import TemplateView
from deployutils.apps.django.redirects import AccountRedirectView
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)

from ...views.app import AppView


urlpatterns = [
    path('', include('djaopsp.urls.views.redirects')), # getstarted/
    path('app/reporting/',
        AccountRedirectView.as_view(
            pattern_name='portfolio_engage'),
        name='reporting_redirect'),
    path('app/info/', include('djaopsp.urls.views.content')),
    path('app/<slug:profile>/', include('djaopsp.urls.views.reports')),
    path('app/<slug:profile>/', include('djaopsp.urls.views.portfolios')),
    path('app/<slug:profile>/', include('djaopsp.urls.views.editors')),
    path('app/<slug:profile>/', include('djaopsp.urls.views.app')),
]

if settings.DEBUG and settings.FEATURES_DEBUG:
    urlpatterns += [
        path('app/', AppView.as_view(), name='product_default_start'),
    ]
else:
    urlpatterns += [
        path('app/', AccountRedirectView.as_view(
            pattern_name='app_profile', account_url_kwarg='profile'),
            name='product_default_start'),
    ]
