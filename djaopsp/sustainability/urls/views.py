# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path

from ..views.portfolios import (
    GoalsPPTXView, BySegmentsPPTXView, GHGEmissionsRatePPTXView,
    GHGEmissionsAmountPPTXView)


urlpatterns = [
    # PPTX charts downloads
    path('download/goals/',
        GoalsPPTXView.as_view(),
        name='reporting_download_goals'),
    path('download/by-segments/',
        BySegmentsPPTXView.as_view(),
        name='reporting_download_by_segments'),
    path('download/ghg-emissions-rate/',
        GHGEmissionsRatePPTXView.as_view(),
        name='reporting_download_ghg_emissions_rate'),
    path('download/ghg-emissions-amount/',
        GHGEmissionsAmountPPTXView.as_view(),
        name='reporting_download_ghg_emissions_amount'),
]
