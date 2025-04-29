# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.

"""
API URLs
"""
from django.urls import path, include

from ...api.content import PageElementAPIView, PageElementIndexAPIView
from ...api.campaigns import CampaignContentAPIView
from ...api.newsfeed import NewsfeedAPIView
from ...api.samples import RespondentsAPIView, PortfolioRequestsSend

urlpatterns = [
    path('respondents', RespondentsAPIView.as_view(),
         name='api_respondents'),
    path('editables/<slug:profile>/', include('djaopsp.urls.api.editors')),
    path('attendance/<slug:profile>/', include('pages.urls.api.sequences')),
    path('progress/', include('pages.urls.api.progress')),

    path('content/<slug:profile>/newsfeed', # profile can be a user
         NewsfeedAPIView.as_view(), name='api_news_feed'),
    path('content/', include('pages.urls.api.readers')),
    path('content/', include('pages.urls.api.noauth')),
    path('content/campaigns/<slug:campaign>', CampaignContentAPIView.as_view(),
         name='api_campaign_questions'),
    path('content/campaigns', CampaignContentAPIView.as_view(),
         name='api_campaign_base'),
    path('content/<path:path>',
        PageElementAPIView.as_view(), name="api_content"),
    path('content',
         PageElementIndexAPIView.as_view(), name="api_content_index"),

    path('', include('survey.urls.api.noauth')),

    path('<slug:profile>/', include('djaopsp.urls.api.assess')),
    path('<slug:profile>/', include('djaopsp.urls.api.audit')),
    path('<slug:profile>/', include('djaopsp.urls.api.reporting')),
    path('<slug:profile>/portfolios/requests/send',
         PortfolioRequestsSend.as_view(), name='api_requests_resend'),
    path('<slug:profile>/', include('survey.urls.api.portfolios')),
    path('<slug:profile>/', include('survey.urls.api.benchmarks')),
]
