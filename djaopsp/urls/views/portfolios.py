# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import include, path

from ...views.portfolios import (ByCampaignAccessiblesView,
    CompletedAssessmentsRawXLSXView,
    DashboardRedirectView,
    PortfolioAccessiblesView, PortfolioEngagementView,
    PortfolioResponsesView,
    PortfoliosDetailView, ReportingDashboardView)
from ...downloads.reporting import (
    AccessiblesAnswersXLSXView, AccessiblesAnswersPivotableCSVView,
    EngagedAnswersXLSXView, EngagedAnswersPivotableCSVView,
    BenchmarkPPTXView, CompletionRatePPTXView,
    EngagementStatsPPTXView, FullReportPPTXView,
    PortfolioAccessiblesXLSXView, PortfolioAccessiblesLongCSVView,
    PortfolioEngagementXLSXView)
from ...views.insights import (AnalyzeInsightsView, CompareInsightsView,
    InsightsView, CampaignAnalyzeInsightsView, CampaignCompareInsightsView,
    CampaignInsightsView)

urlpatterns = [
    # Redirects
    path('reporting/track/',
        DashboardRedirectView.as_view(
            breadcrumb_url='reporting_profile_accessibles'),
        name='portfolio_analyze'),
    path('reporting/dashboard/',
        DashboardRedirectView.as_view(
            breadcrumb_url='reporting_organization_dashboard'),
        name='portfolio_insights'),

    # side-by-side comparaison, and aggregates analytics
    path('reporting/insights/compare/',
        CompareInsightsView.as_view(),
        name='reporting_insights_compare'),
    path('reporting/insights/analyze/',
        AnalyzeInsightsView.as_view(),
        name='reporting_insights_analyze'),
    path('reporting/insights/',
        InsightsView.as_view(),
        name='reporting_insights'),

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
    path('reporting/<slug:campaign>/download/<path:path>',
        BenchmarkPPTXView.as_view(),
        name='reporting_download_benchmarks'),
    path('reporting/<slug:campaign>/download/',
        FullReportPPTXView.as_view(),
        name='reporting_download_full_report'),

    # Download of dashboards as spreadsheets
    path('completed/download/',
        CompletedAssessmentsRawXLSXView.as_view(),
         name="completed_assessments_download"),

    path('reporting/<slug:campaign>/compare/<path:path>/download/',
        EngagedAnswersXLSXView.as_view(),
        name='download_matrix_compare_path'),

    path('reporting/<slug:campaign>/engage/download/raw/long/',
        EngagedAnswersPivotableCSVView.as_view(),
        name='download_engage_raw_long'),
    path('reporting/<slug:campaign>/engage/download/raw/',
        EngagedAnswersXLSXView.as_view(),
        name='download_matrix_compare'),
    path('reporting/<slug:campaign>/engage/download/',
        PortfolioEngagementXLSXView.as_view(),
        name='reporting_profile_engage_download'),

    path('reporting/<slug:campaign>/accessibles/download/raw/long/',
        AccessiblesAnswersPivotableCSVView.as_view(),
        name='download_accessibles_raw_long'),
    path('reporting/<slug:campaign>/accessibles/download/raw/',
        AccessiblesAnswersXLSXView.as_view(),
        name='download_accessibles_raw'),
    path('reporting/<slug:campaign>/accessibles/download/long/',
        PortfolioAccessiblesLongCSVView.as_view(),
        name='reporting_profile_accessibles_download_long'),
    path('reporting/<slug:campaign>/accessibles/download/',
        PortfolioAccessiblesXLSXView.as_view(),
        name='reporting_profile_accessibles_download'),

    # Dashboards as HTML pages
    path('reporting/<slug:campaign>/accessibles/',
        PortfolioAccessiblesView.as_view(),
        name='reporting_profile_accessibles'),
    path('reporting/<slug:campaign>/dashboard/',
        ReportingDashboardView.as_view(),
        name='reporting_organization_dashboard'),

    # side-by-side comparaison, and aggregates analytics
    path('reporting/<slug:campaign>/insights/compare/',
        CampaignCompareInsightsView.as_view(),
        name='reporting_insights_compare_campaign'),
    path('reporting/<slug:campaign>/insights/analyze/',
        CampaignAnalyzeInsightsView.as_view(),
        name='reporting_insights_analyze_campaign'),
    path('reporting/<slug:campaign>/insights/',
        CampaignInsightsView.as_view(),
        name='reporting_insights_campaign'),

    path('reporting/<slug:campaign>/compare/<path:path>/',
        CampaignCompareInsightsView.as_view(), name='matrix_compare_path'),
    path('reporting/<slug:campaign>/compare/',
        CampaignCompareInsightsView.as_view(), name='matrix_compare'),
    path('reporting/<slug:campaign>/matrix/<path:path>/',
        PortfoliosDetailView.as_view(), name='matrix_chart'),

    path('reporting/<slug:campaign>/retiring/',
        PortfolioResponsesView.as_view(),
        name='portfolio_responses'),
    path('reporting/<slug:campaign>/',
        PortfolioEngagementView.as_view(),
        name='reporting_profile_engage'),

    path('reporting/',
        ByCampaignAccessiblesView.as_view(
            breadcrumb_url='reporting_profile_engage'),
        name='portfolio_engage'),

    path('', include('survey.urls.views.portfolios')),
]
