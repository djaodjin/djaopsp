# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
API URLs for portfolios engagement & analytics dashboards
"""
from django.urls import include, path

from ...api.samples import (
    AssessmentContentAPIView, AssessmentContentIndexAPIView,
    AssessmentCompleteAPIView, AssessmentCompleteIndexAPIView,
    BenchmarkAPIView, BenchmarkIndexAPIView, HistoricalAssessmentsAPIView)


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
        BenchmarkAPIView.as_view(),
        name='api_benchmark'),
    path('sample/<slug:sample>/benchmarks',
        BenchmarkIndexAPIView.as_view(),
        name='api_benchmark_index'),
    path('samples',
        HistoricalAssessmentsAPIView.as_view(),
        name='api_historical_assessments'),
    path('', include('survey.urls.api.sample')),
    path('', include('survey.urls.api.metrics')),
    path('', include('survey.urls.api.filters')),
    path('', include('pages.urls.api.assets')),
]
