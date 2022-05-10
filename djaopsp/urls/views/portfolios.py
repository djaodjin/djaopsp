# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import include, path

from ...views.portfolios import (ActiveReportingEntitiesView,
    DashboardRedirectView, ReportingDashboardView, ReportingHistoricalView,
    PortfolioResponsesView, PortfolioResponsesXLSXView,
    PortfolioResponsesRawXLSXView, PortfoliosDetailView)


urlpatterns = [
    # Views specifics to sustainability assessment
    path('reporting/<slug:campaign>/',
         include('djaopsp.sustainability.urls.views')),

    # Dashboards
    path('reporting/<slug:campaign>/active/',
        ActiveReportingEntitiesView.as_view(),
        name='active_reporting_entities'),
    path('reporting/historical/',
        ReportingHistoricalView.as_view(),
        name='reporting_organization_historical'),

    path('reporting/<slug:campaign>/dashboard/',
        ReportingDashboardView.as_view(),
        name='reporting_organization_dashboard'),
    path('reporting/<slug:campaign>/compare/<path:path>/',
        PortfoliosDetailView.as_view(), name='matrix_chart'),

    # Download of dashboards as spreadsheets
    path('reporting/<slug:campaign>/download/raw/',
        PortfolioResponsesRawXLSXView.as_view(),
        name='portfolio_responses_download_raw'),
    path('reporting/<slug:campaign>/download/',
        PortfolioResponsesXLSXView.as_view(),
        name='portfolio_responses_download'),

    path('reporting/<slug:campaign>/',
        PortfolioResponsesView.as_view(),
        name='portfolio_responses'),
    path('reporting/',
        DashboardRedirectView.as_view(breadcrumb_url='portfolio_responses'),
        name='reporting'),
]
