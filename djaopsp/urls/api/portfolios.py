# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
API URLs for portfolios engagement & analytics dashboards
"""
from django.urls import include, path

from ...api.portfolios import (PortfolioResponsesAPIView,
    TotalScoreBySubsectorAPIView)


urlpatterns = [
    path('reporting/<slug:campaign>/',
         include('djaopsp.sustainability.urls.api')),
    path('reporting/<slug:campaign>',
        PortfolioResponsesAPIView.as_view(), name="api_portfolio_responses"),
    path('reporting/<slug:campaign>/matrix/<path:path>',
        TotalScoreBySubsectorAPIView.as_view()),
    path('reporting/<slug:campaign>/', include('survey.urls.api.filters')),
    path('reporting/<slug:campaign>/', include('survey.urls.api.matrix')),
]
