# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.

"""
API URLs for portfolios engagement & analytics dashboards
"""
from django.urls import include, path

from ...api.campaigns import DashboardsAvailableAPIView
from ...api.exports import BenchmarksExportAPIView
from ...api.portfolios import (BenchmarkAPIView, BenchmarkIndexAPIView,
    CompareAPIView, CompareIndexAPIView,
    CompletedAssessmentsAPIView, CompletionRateAPIView, EngagementStatsAPIView,
    LastByCampaignAccessiblesAPIView,
    PortfolioAccessibleSamplesAPIView, PortfolioAccessiblesDeleteAPIView,
    PortfolioEngagementAPIView, TotalScoreBySubsectorAPIView)

urlpatterns = [
    path('exports',
        BenchmarksExportAPIView.as_view(),
         name='api_benchmarks_export'),
    path('completed',
        CompletedAssessmentsAPIView.as_view(),
         name="api_completed_assessments"),
    path('reporting/campaigns',
         DashboardsAvailableAPIView.as_view(),
         name="api_reporting_campaigns"),
    path('reporting/<slug:campaign>/benchmarks/<path:path>',
        BenchmarkAPIView.as_view(), name='api_reporting_benchmarks'),
    path('reporting/<slug:campaign>/benchmarks',
        BenchmarkIndexAPIView.as_view(), name='api_reporting_benchmarks_index'),
    path('reporting/<slug:campaign>/compare/<path:path>',
        CompareAPIView.as_view(), name='survey_api_compare_samples'),
    path('reporting/<slug:campaign>/compare',
        CompareIndexAPIView.as_view(), name='survey_api_compare_samples_index'),
    path('reporting/<slug:campaign>/engaged/stats',
        EngagementStatsAPIView.as_view(),
        name="api_portfolio_engagement_stats"),
    path('reporting/<slug:campaign>/engaged',
        PortfolioEngagementAPIView.as_view(),
        name='api_portfolio_engagement'),
    path('reporting/<slug:campaign>/accessibles/<slug:account>',
        PortfolioAccessiblesDeleteAPIView.as_view(),
        name='api_portfolio_accessibles_delete'),
    path('reporting/<slug:campaign>/accessibles',
        PortfolioAccessibleSamplesAPIView.as_view(),
        name='api_portfolio_accessible_samples'),
    path('reporting/<slug:campaign>/completion-rate',
        CompletionRateAPIView.as_view(), name="api_reporting_completion_rate"),
    path('reporting/<slug:campaign>/',
        include('djaopsp.sustainability.urls.api')),
    path('reporting/<slug:campaign>/matrix/<path:path>',
        TotalScoreBySubsectorAPIView.as_view()),
    path('reporting/<slug:campaign>/', include('survey.urls.api.matrix')),
    path('reporting',
        LastByCampaignAccessiblesAPIView.as_view(),
        name='api_last_by_campaign_accessibles'),
]
