# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import include, path

from ...views.matrix import CompareView, CompareXLSXView
from ...views.portfolios import (ActiveReportingEntitiesView,
    CompletedAssessmentsRawXLSXView, CompletionRatePPTXView,
    DashboardRedirectView, EngagementStatsPPTXView,
    PortfolioAccessiblesView, PortfolioEngagementView,
    PortfolioResponsesView, PortfolioResponsesXLSXView,
    PortfoliosDetailView, ReportingDashboardView)
from ...downloads.reporting import (PortfolioAccessiblesXLSXView,
    PortfolioEngagementXLSXView)

urlpatterns = [
    # Redirects
    path('reporting/analyze/',
        DashboardRedirectView.as_view(
            breadcrumb_url='reporting_profile_accessibles'),
        name='portfolio_analyze'),

    # PPTX charts downloads
    path('reporting/<slug:campaign>/download/completion-rate/',
        CompletionRatePPTXView.as_view(),
        name='reporting_download_completion_rate'),
    path('reporting/<slug:campaign>/download/engagement/stats/',
        EngagementStatsPPTXView.as_view(),
        name='reporting_download_engagement_stats'),
    # Views specifics to sustainability assessment
    path('reporting/<slug:campaign>/',
         include('djaopsp.sustainability.urls.views')),

    # Download of dashboards as spreadsheets
    path('completed/download/',
        CompletedAssessmentsRawXLSXView.as_view(),
         name="completed_assessments_download"),
    path('reporting/<slug:campaign>/compare/<path:path>/download/',
        CompareXLSXView.as_view(),
        name='download_matrix_compare_path'),
    path('reporting/<slug:campaign>/compare/download/',
        CompareXLSXView.as_view(),
        name='download_matrix_compare'),
    path('reporting/<slug:campaign>/download/',
        PortfolioResponsesXLSXView.as_view(),
        name='portfolio_responses_download'),

    # Dashboards as HTML pages
    path('reporting/<slug:campaign>/active/',
        ActiveReportingEntitiesView.as_view(),
        name='active_reporting_entities'),
    path('reporting/<slug:campaign>/engage/download/',
        PortfolioEngagementXLSXView.as_view(),
        name='reporting_profile_engage_download'),
    path('reporting/<slug:campaign>/engage/',
        PortfolioEngagementView.as_view(),
        name='reporting_profile_engage'),
    path('reporting/<slug:campaign>/accessibles/download/',
        PortfolioAccessiblesXLSXView.as_view(),
        name='reporting_profile_accessibles_download'),
    path('reporting/<slug:campaign>/accessibles/',
        PortfolioAccessiblesView.as_view(),
        name='reporting_profile_accessibles'),
    path('reporting/<slug:campaign>/dashboard/',
        ReportingDashboardView.as_view(),
        name='reporting_organization_dashboard'),
    path('reporting/<slug:campaign>/compare/<path:path>/',
        CompareView.as_view(), name='matrix_compare_path'),
    path('reporting/<slug:campaign>/compare/',
        CompareView.as_view(), name='matrix_compare'),
    path('reporting/<slug:campaign>/matrix/<path:path>/',
        PortfoliosDetailView.as_view(), name='matrix_chart'),

    path('reporting/<slug:campaign>/',
        PortfolioResponsesView.as_view(),
        name='portfolio_responses'),
    path('reporting/',
        DashboardRedirectView.as_view(breadcrumb_url='portfolio_responses'),
        name='portfolio_engage'),
    path('', include('survey.urls.views.portfolios')),
]
