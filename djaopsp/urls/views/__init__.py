# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path, include
from django.views.generic import TemplateView
from deployutils.apps.django.redirects import AccountRedirectView
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)

from ...views.app import AppView
from ...views.assess import TrackMetricsView, AssessPracticesView
from ...views.content import ContentDetailView, ContentIndexView
from ...views.scorecard import (ScorecardIndexView, ScorecardHistoryView,
    ScorecardRedirectView)
from pages.views.elements import CertificateDownloadView


urlpatterns = [
    path('<slug:sequence>/certificate/',
         CertificateDownloadView.as_view(),
         name='certificate_download'),
    path('app/reporting/',
        AccountRedirectView.as_view(
            pattern_name='portfolio_engage'),
        name='reporting_redirect'),
    path('app/info/', include('djaopsp.urls.views.content')),
    path('app/<slug:profile>/', include('djaopsp.urls.views.reports')),
    path('app/<slug:profile>/', include('djaopsp.urls.views.portfolios')),
    path('app/<slug:profile>/', include('djaopsp.urls.views.editors')),
    path('app/<slug:profile>/', include('djaopsp.urls.views.app')),
    path('', include('djaopsp.urls.views.redirects')),
]
