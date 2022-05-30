# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
API URLs for portfolios engagement & analytics dashboards
"""
from django.urls import include, path

from ...api.samples import (AssessmentContentAPIView,
    AssessmentCompleteAPIView, BenchmarkAPIView, HistoricalAssessmentsAPIView)


urlpatterns = [
    path('', include('survey.urls.api.noauth')),
    path('<slug:profile>/sample/<slug:sample>/content/<path:path>',
        AssessmentContentAPIView.as_view(), name='api_sample_content'),
    path('<slug:profile>/sample/<slug:sample>/content',
        AssessmentContentAPIView.as_view(), name='api_sample_content_index'),
    path('<slug:profile>/sample/<slug:sample>/freeze/<path:path>',
        AssessmentCompleteAPIView.as_view(), name='survey_api_sample_freeze'),
    path('<slug:profile>/sample/<slug:sample>/freeze',
        AssessmentCompleteAPIView.as_view(),
        name='survey_api_sample_freeze_index'),
    path('<slug:profile>/<slug:sample>/benchmarks/<path:path>',
        BenchmarkAPIView.as_view(),
        name='api_benchmark'),
    path('<slug:profile>/<slug:sample>/benchmarks',
        BenchmarkAPIView.as_view(),
        name='api_benchmark_index'),
    path('<slug:profile>/samples/',
        HistoricalAssessmentsAPIView.as_view(),
        name='api_historical_assessments'),
    path('<slug:profile>/', include('survey.urls.api.sample')),
    path('<slug:profile>/', include('survey.urls.api.filters')),
]
