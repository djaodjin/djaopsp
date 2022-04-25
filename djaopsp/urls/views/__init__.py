# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path, include
from django.views.generic import TemplateView
from deployutils.apps.django.redirects import AccountRedirectView
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_prefixed)

from ...views.app import AppView
from ...views.assess import TrackMetricsView, AssessPracticesView
from ...views.content import ContentDetailView, ContentIndexView
from ...views.reporting import ReportsRequestedView
from ...views.scorecard import (ScorecardIndexView, ScorecardHistoryView,
    ScorecardRedirectView)


urlpatterns = [
    path('app/info/<path:path>/',
         ContentDetailView.as_view(), name='pages_element'),
    path('app/info/',
         ContentIndexView.as_view(), name='pages_index'),
    path('app/<slug:profile>/', include('djaopsp.urls.views.reports')),
    path('app/<slug:profile>/', include('djaopsp.urls.views.editors')),
    path(r'app/<slug:profile>/reporting/',
        ReportsRequestedView.as_view(), name='reporting'),

    path(r'app/<slug:profile>/',
         AppView.as_view(), name='app'),
    path(r'app/',
        AccountRedirectView.as_view(
            pattern_name='app',
            slug_url_kwarg='profile',
            new_account_url=site_prefixed('/users/roles/accept/')),
        name='app_redirect'),
]
