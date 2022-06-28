# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path

from ...views.assess import (AssessPracticesXLSXView, AssessPracticesView,
    AssessRedirectView, ImprovePracticesView, ImproveRedirectView,
    TrackMetricsView)
from ...views.scorecard import (ScorecardIndexView, ScorecardHistoryView,
    ScorecardRedirectView, DataValuesView)
from ...views.share import ShareView


urlpatterns = [
    path('track/values/',
         DataValuesView.as_view(), name='data_values'),
    path('track/<slug:metric>/',
         TrackMetricsView.as_view(), name='track_metrics'),
    path('track/',
         TrackMetricsView.as_view(), name='track_metrics_index'),
    # Assessment
    path('assess/<slug:sample>/download/',
         AssessPracticesXLSXView.as_view(), name='assess_download'),
    path('assess/<slug:sample>/<path:path>/',
         AssessPracticesView.as_view(), name='assess_practices'),
    path('assess/<slug:sample>/',
         AssessRedirectView.as_view(), name='assess_redirect'),
    # Target and improvement plan
    path('improve/<slug:sample>/<path:path>/',
         ImprovePracticesView.as_view(), name='improve_practices'),
    path('improve/<slug:sample>/',
         ImproveRedirectView.as_view(), name='improve_redirect'),
    # Scorecard review
    path('scorecard/history/',
         ScorecardHistoryView.as_view(), name='scorecard_history'),
    path('scorecard/<slug:sample>/',
         ScorecardIndexView.as_view(), name='scorecard'),
    path('scorecard/',
         ScorecardRedirectView.as_view(), name='scorecard_redirect'),
    # Share
    path('share/<slug:sample>/',
        ShareView.as_view(), name='share'),
]
