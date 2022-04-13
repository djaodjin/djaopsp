# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
API URLs
"""
from django.urls import path, include
from ...api.samples import AssessmentContentAPIView
from ...api.content import PageElementAPIView, PageElementEditableListAPIView


urlpatterns = [
    path('content/editables/<slug:profile>/',
        PageElementEditableListAPIView.as_view(),
        name="pages_api_editables_index"),
    path('content/editables/<slug:profile>/',
         include('djaopsp.urls.api.editors')),
    path('content/', include('pages.urls.api.readers')),
    path('content/', PageElementAPIView.as_view(),
        name="api_content_index"),
    path('content/', include('pages.urls.api.noauth')),

    path('', include('survey.urls.api.noauth')),
    path('<slug:profile>/sample/<slug:sample>/content/<path:path>',
       AssessmentContentAPIView.as_view(), name='api_sample_content'),
    path('<slug:profile>/sample/<slug:sample>/content',
       AssessmentContentAPIView.as_view(), name='api_sample_content_index'),
    path('<slug:profile>/', include('survey.urls.api.campaigns')),
    path('<slug:profile>/', include('survey.urls.api.sample')),
    path('<slug:profile>/', include('survey.urls.api.portfolios')),
]
