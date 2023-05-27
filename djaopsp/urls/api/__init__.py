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


urlpatterns = [
    path('content/editables/<slug:profile>',
        PageElementEditableListAPIView.as_view(),
        name="pages_api_editables_index"),
    path('content/editables/<slug:profile>/',
         include('djaopsp.urls.api.editors')),
    path('content/', include('pages.urls.api.readers')),
    path('content/search',
        PageElementSearchAPIView.as_view(), name='api_page_element_search'),
    path('content/detail/<path:path>',
        PageElementDetailAPIView.as_view(), name='pages_api_pageelement'),
    path('content/<path:path>',
        PageElementAPIView.as_view(), name="api_content"),
    path('content/',
         PageElementIndexAPIView.as_view(), name="api_content_index"),
    path('', include('survey.urls.api.noauth')),

    path('<slug:profile>/', include('djaopsp.urls.api.assess')),
    path('<slug:profile>/', include('djaopsp.urls.api.audit')),
    path('<slug:profile>/', include('djaopsp.urls.api.portfolios')),
    path('<slug:profile>/', include('survey.urls.api.campaigns')),
    path('<slug:profile>/', include('survey.urls.api.portfolios')),
]
