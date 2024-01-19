# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

"""
API URLs
"""
from django.urls import path, include
from pages.api.elements import (PageElementSearchAPIView,
    PageElementDetailAPIView)

from ...api.content import (PageElementAPIView, PageElementIndexAPIView,
    PageElementEditableListAPIView)
from ...api.samples import RespondentsAPIView


urlpatterns = [
    path('respondents', RespondentsAPIView.as_view(),
         name='api_respondents'),
    path('editables/<slug:profile>/content',
        PageElementEditableListAPIView.as_view(),
        name="pages_api_editables_index"),
    path('editables/<slug:profile>/',
         include('djaopsp.urls.api.editors')),
    path('attendance/', include('pages.urls.api.sequences')),

    path('progress/', include('pages.urls.api.progress')),
    path('content/', include('pages.urls.api.readers')),

    path('content/search',
        PageElementSearchAPIView.as_view(), name='api_page_element_search'),
    path('content/detail/<path:path>',
        PageElementDetailAPIView.as_view(), name='pages_api_pageelement'),
    path('content/<path:path>',
        PageElementAPIView.as_view(), name="api_content"),
    path('content',
         PageElementIndexAPIView.as_view(), name="api_content_index"),
    path('', include('survey.urls.api.noauth')),

    path('<slug:profile>/', include('djaopsp.urls.api.assess')),
    path('<slug:profile>/', include('djaopsp.urls.api.audit')),
    path('<slug:profile>/', include('djaopsp.urls.api.portfolios')),
    path('<slug:profile>/', include('survey.urls.api.campaigns')),
    path('<slug:profile>/', include('survey.urls.api.portfolios')),
]
