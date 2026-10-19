# Copyright (c) 2026, DjaoDjin inc.
# see LICENSE.

"""
API URLs
"""
from django.urls import path, include

from ...api.benchmarks import AffinityFilterAPIView
from ...api.content import PageElementAPIView, PageElementIndexAPIView
from ...api.campaigns import CampaignContentAPIView, CampaignContentIndexAPIView
from ...api.newsfeed import GetStartedAPIView, NewsfeedAPIView
from ...api.samples import RespondentsAPIView, PortfolioRequestsSend

urlpatterns = [
    path('filters/affinity',
        AffinityFilterAPIView.as_view(),
        name='survey_api_affinity_filter'),
    path('', include('survey.urls.api.accounts.filters')),
]
