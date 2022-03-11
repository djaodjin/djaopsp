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
from ...views.assess import AssessMetricsView, AssessPracticesView
from ...views.content import ContentDetailView, ContentIndexView
from ...views.reporting import ReportsRequestedView
from ...views.scorecard import (ScorecardView, ScorecardHistoryView,
    ScorecardRedirectView)


urlpatterns = [
    path('app/<slug:profile>/', include('djaopsp.urls.views.editors')),
    path('app/info/<path:path>/',
         ContentDetailView.as_view(), name='pages_edit_element'),
    path('app/info/',
         ContentIndexView.as_view(), name='summary_index'),
    path(r'app/<slug:profile>/assess/metrics/',
         AssessMetricsView.as_view(), name='assess_metrics'),
    path(r'app/<slug:profile>/assess/<slug:sample>/<path:path>/',
         AssessPracticesView.as_view(), name='assess_practices'),
    path(r'app/<slug:profile>/scorecard/history/',
         ScorecardHistoryView.as_view(), name='scorecard_history'),
    path(r'app/<slug:profile>/scorecard/<slug:sample>/',
         ScorecardView.as_view(), name='scorecard'),
    path(r'app/<slug:profile>/scorecard/',
         ScorecardRedirectView.as_view(), name='scorecard_redirect'),
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
    path(r'', TemplateView.as_view(template_name='index.html'),
        name='homepage'),
]
