# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

"""
API URLs for portfolios engagement & analytics dashboards
"""
from django.urls import include, path

from ...api.assets import AssetAPIView
from ...api.samples import (
    AssessmentContentAPIView, AssessmentContentIndexAPIView,
    AssessmentCompleteAPIView, AssessmentCompleteIndexAPIView,
    SampleBenchmarksAPIView, SampleBenchmarksIndexAPIView)


urlpatterns = [
    path('sample/<slug:sample>/content/<path:path>',
        AssessmentContentAPIView.as_view(), name='api_sample_content'),
    path('sample/<slug:sample>/content',
        AssessmentContentIndexAPIView.as_view(),
        name='api_sample_content_index'),
    path('sample/<slug:sample>/freeze/<path:path>',
        AssessmentCompleteAPIView.as_view(), name='survey_api_sample_freeze'),
    path('sample/<slug:sample>/freeze',
        AssessmentCompleteIndexAPIView.as_view(),
        name='survey_api_sample_freeze_index'),
    path('sample/<slug:sample>/benchmarks/<path:path>',
        SampleBenchmarksAPIView.as_view(),
        name='survey_api_sample_benchmarks'),
    path('sample/<slug:sample>/benchmarks',
        SampleBenchmarksIndexAPIView.as_view(),
        name='survey_api_sample_benchmarks_index'),
    path('', include('survey.urls.api.sample')),
    path('', include('survey.urls.api.metrics')),
    path('', include('survey.urls.api.filters')),
    path('assets/<path:path>',
        AssetAPIView.as_view(), name='pages_api_asset'),
    path('', include('pages.urls.api.assets')),
]
