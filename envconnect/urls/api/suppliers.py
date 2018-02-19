# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

from django.conf import settings
from django.conf.urls import url, include

from ...api.assessments import AssessmentAPIView, AssessmentAnswerAPIView
from ...api.benchmark import BenchmarkAPIView, HistoricalScoreAPIView
from ...api.improvements import (ImprovementListAPIView,
    ImprovementToggleAPIView)
from ...api.dashboards import SupplierListAPIView, TotalScoreBySubsectorAPIView

urlpatterns = [
    url(r'(?P<organization>%s)/suppliers/?' % settings.SLUG_RE,
      SupplierListAPIView.as_view(), name="api_suppliers"),
    url(r'(?P<organization>%s)/matrix/(?P<path>%s)/?$' % (
        settings.SLUG_RE, settings.SLUG_RE + settings.PATH_RE),
        TotalScoreBySubsectorAPIView.as_view()),
    url(r'(?P<organization>%s)/campaign/' % settings.SLUG_RE,
        include('survey.urls.api.campaigns')),
    url(r'(?P<organization>%s)/matrix/' % settings.SLUG_RE,
        include('survey.urls.api.matrix')),

    url(r'(?P<organization>%s)/benchmark/current(?P<path>%s)/?' % (
        settings.SLUG_RE, settings.PATH_RE),
        BenchmarkAPIView.as_view(),
        name="api_benchmark"),
    url(r'(?P<organization>%s)/benchmark/historical(?P<path>%s)/?' % (
        settings.SLUG_RE, settings.PATH_RE),
        HistoricalScoreAPIView.as_view(),
        name="api_historical_scores"),
    url(r'(?P<organization>%s)/improvement(?P<path>%s)/?' % (
        settings.SLUG_RE, settings.PATH_RE),
        ImprovementToggleAPIView.as_view(),
        name='api_improvement'),
    url(r'(?P<organization>%s)/improvement/?' % settings.SLUG_RE,
        ImprovementListAPIView.as_view(),
        name='api_improvement_base'),
    url(r'^(?P<interviewee>%s)/sample/(?P<sample>%s)/(?P<rank>\d+)/' % (
        settings.SLUG_RE, settings.SLUG_RE),
        AssessmentAnswerAPIView.as_view(), name='survey_api_answer'),
    url(r'(?P<interviewee>%s)/sample/(?P<sample>%s)/$' % (
        settings.SLUG_RE, settings.SLUG_RE),
        AssessmentAPIView.as_view(), name='survey_api_sample'),
    url(r'(?P<interviewee>%s)/sample/' % (settings.SLUG_RE,),
        include('survey.urls.api.sample')),
]
