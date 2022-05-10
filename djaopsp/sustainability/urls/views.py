# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path

from ..views.portfolios import (CompletionRatePPTXView,
    GoalsPPTXView, BySegmentsPPTXView, GHGEmissionsRatePPTXView,
    GHGEmissionsAmountPPTXView)


urlpatterns = [
    # PPTX charts downloads
    path('download/completion-rate/',
        CompletionRatePPTXView.as_view(),
        name='reporting_download_completion_rate'),
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
