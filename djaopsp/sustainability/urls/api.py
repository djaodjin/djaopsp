# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

"""
API URLs for portfolios analytics dashboards
related to sustainability questionnaires
"""
from django.urls import path

from ..api.portfolios import (GoalsAPIView,
    BySegmentsAPIView, GHGEmissionsRateAPIView, GHGEmissionsAmountAPIView)

urlpatterns = [
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
