# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
API URLs for portfolios engagement & analytics dashboards
"""
from django.urls import path

from ..api.portfolios import (CompletionRateAPIView, GoalsAPIView,
    BySegmentsAPIView, GHGEmissionsRateAPIView, GHGEmissionsAmountAPIView)

urlpatterns = [
    path('completion-rate',
        CompletionRateAPIView.as_view(), name="api_reporting_completion_rate"),
    path('goals',
        GoalsAPIView.as_view(), name="api_reporting_goals"),
    path('by-segments',
        BySegmentsAPIView.as_view(), name="api_reporting_by_segments"),
    path('ghg-emissions-rate',
        GHGEmissionsRateAPIView.as_view(),
        name="api_reporting_ghg_emissions_rate"),
    path('ghg-emissions-amount',
        GHGEmissionsAmountAPIView.as_view(),
        name="api_reporting_ghg_emissions_amount"),
]
