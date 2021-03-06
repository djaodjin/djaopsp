# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
API URLs
"""
from django.urls import path, include
from ...api.content import (PageElementAPIView, PageElementIndexAPIView,
    PageElementEditableListAPIView)


urlpatterns = [
    path('content/editables/<slug:profile>/',
        PageElementEditableListAPIView.as_view(),
        name="pages_api_editables_index"),
    path('content/editables/<slug:profile>/',
        include('djaopsp.urls.api.editors')),
    path('content/', include('pages.urls.api.readers')),
    path('content/<path:path>',
        PageElementAPIView.as_view(), name="api_content"),
    path('content/',
         PageElementIndexAPIView.as_view(), name="api_content_index"),
    path('content/', include('pages.urls.api.noauth')),
    path('', include('survey.urls.api.noauth')),

    path('<slug:profile>/', include('djaopsp.urls.api.assess')),
    path('<slug:profile>/', include('djaopsp.urls.api.portfolios')),
    path('<slug:profile>/', include('survey.urls.api.campaigns')),
    path('<slug:profile>/', include('survey.urls.api.portfolios')),
]
