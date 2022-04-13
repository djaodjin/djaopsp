# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path, include

from ...views.assess import TrackMetricsView, AssessPracticesView
from ...views.scorecard import (ScorecardIndexView, ScorecardHistoryView,
    ScorecardRedirectView)


urlpatterns = [
    path('track/<slug:metric>/',
         TrackMetricsView.as_view(), name='track_metrics'),
    path('track/',
         TrackMetricsView.as_view(), name='track_metrics_index'),
    path('assess/<slug:sample>/<path:path>/',
         AssessPracticesView.as_view(), name='assess_practices'),
    path('scorecard/history/',
         ScorecardHistoryView.as_view(), name='scorecard_history'),
    path('scorecard/<slug:sample>/',
         ScorecardIndexView.as_view(), name='scorecard'),
    path('scorecard/',
         ScorecardRedirectView.as_view(), name='scorecard_redirect'),
]
