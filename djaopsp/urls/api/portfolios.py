# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

"""
API URLs for portfolios engagement & analytics dashboards
"""
from django.urls import include, path

from ...api.portfolios import (CompareAPIView, CompareIndexAPIView,
    CompletedAssessmentsAPIView,
    PortfolioAccessibleSamplesAPIView, PortfolioEngagementAPIView,
    PortfolioResponsesAPIView, TotalScoreBySubsectorAPIView)


urlpatterns = [
    path('completed',
        CompletedAssessmentsAPIView.as_view(),
         name="api_completed_assessments"),
    path('reporting/<slug:campaign>/compare/<path:path>',
        CompareAPIView.as_view(), name='djaopsp_api_compare_samples_path'),
    path('reporting/<slug:campaign>/compare',
        CompareIndexAPIView.as_view(), name='djaopsp_api_compare_samples'),
    path('reporting/<slug:campaign>/engagement',
         PortfolioEngagementAPIView.as_view(),
         name='api_portfolio_engagement'),
    path('reporting/<slug:campaign>/accessibles',
         PortfolioAccessibleSamplesAPIView.as_view(),
         name='api_portfolio_accessible_samples'),
    path('reporting/<slug:campaign>/',
         include('djaopsp.sustainability.urls.api')),
    path('reporting/<slug:campaign>',
        PortfolioResponsesAPIView.as_view(), name="api_portfolio_responses"),
    path('reporting/<slug:campaign>/matrix/<path:path>',
        TotalScoreBySubsectorAPIView.as_view()),
    path('reporting/<slug:campaign>/', include('survey.urls.api.matrix')),
]
