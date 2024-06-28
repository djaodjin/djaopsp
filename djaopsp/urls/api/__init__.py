# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

"""
API URLs
"""
from django.urls import path, include, re_path

from ...api.content import (PageElementAPIView, PageElementIndexAPIView,
    PageElementEditableListAPIView)
from ...api.campaigns import CampaignContentAPIView
from ...api.samples import RespondentsAPIView

urlpatterns = [
    path('respondents', RespondentsAPIView.as_view(),
         name='api_respondents'),

    path('editables/<slug:profile>/content',
        PageElementEditableListAPIView.as_view(),
        name="pages_api_editables_index"),
    path('editables/<slug:profile>/', include('djaopsp.urls.api.editors')),

    path('attendance/<slug:profile>/', include('pages.urls.api.sequences')),

    path('progress/', include('pages.urls.api.progress')),

    path('content/', include('pages.urls.api.readers')),
    path('content/', include('pages.urls.api.noauth')),
    path('content/campaigns/<slug:campaign>', CampaignContentAPIView.as_view(),
         name='api_campaign_questions'),
    path('content/<path:path>',
        PageElementAPIView.as_view(), name="api_content"),
    path('content',
         PageElementIndexAPIView.as_view(), name="api_content_index"),

    path('', include('survey.urls.api.noauth')),

    path('<slug:profile>/', include('survey.urls.api.campaigns')),
    path('<slug:profile>/', include('djaopsp.urls.api.assess')),
    path('<slug:profile>/', include('djaopsp.urls.api.audit')),
    path('<slug:profile>/', include('djaopsp.urls.api.portfolios')),
    path('<slug:profile>/', include('survey.urls.api.portfolios')),
    path('<slug:profile>/', include('survey.urls.api.benchmarks')),
]
