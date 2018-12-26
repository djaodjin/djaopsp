# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

from django.conf.urls import url, include
from pages.settings import PATH_RE, SLUG_RE

from ...api.assessments import (AssessmentAPIView, AssessmentAnswerAPIView,
    AssessmentMeasuresAPIView, DestroyMeasureAPIView)
from ...api.benchmark import BenchmarkAPIView, HistoricalScoreAPIView
from ...api.improvements import (ImprovementListAPIView,
    ImprovementToggleAPIView)
from ...api.dashboards import (SupplierListAPIView,
    TotalScoreBySubsectorAPIView, ShareScorecardAPIView)

urlpatterns = [
    url(r'(?P<organization>%s)/suppliers/?' % SLUG_RE,
      SupplierListAPIView.as_view(), name="api_suppliers"),
    url(r'(?P<organization>%s)/matrix/(?P<path>%s)/?$' % (
        SLUG_RE, SLUG_RE + PATH_RE),
        TotalScoreBySubsectorAPIView.as_view()),
    url(r'(?P<organization>%s)/campaign/' % SLUG_RE,
        include('survey.urls.api.campaigns')),
    url(r'(?P<organization>%s)/matrix/' % SLUG_RE,
        include('survey.urls.api.matrix')),

    url(r'(?P<organization>%s)/benchmark/share(?P<path>%s)/?' % (
        SLUG_RE, PATH_RE),
        ShareScorecardAPIView.as_view(),
        name="api_benchmark_share"),
    url(r'(?P<organization>%s)/benchmark/current(?P<path>%s)/?' % (
        SLUG_RE, PATH_RE),
        BenchmarkAPIView.as_view(),
        name="api_benchmark"),
    url(r'(?P<organization>%s)/benchmark/historical(?P<path>%s)/?' % (
        SLUG_RE, PATH_RE),
        HistoricalScoreAPIView.as_view(),
        name="api_historical_scores"),
    url(r'(?P<organization>%s)/improvement(?P<path>%s)/?' % (
        SLUG_RE, PATH_RE),
        ImprovementToggleAPIView.as_view(),
        name='api_improvement'),
    url(r'(?P<organization>%s)/improvement/?' % SLUG_RE,
        ImprovementListAPIView.as_view(),
        name='api_improvement_base'),
    url(r'^(?P<interviewee>%s)/sample/(?P<sample>%s)/(?P<rank>\d+)/'\
    'measures/(?P<metric>%s)/' % (SLUG_RE, SLUG_RE, SLUG_RE),
        DestroyMeasureAPIView.as_view(), name='api_measures_delete'),
    url(r'^(?P<interviewee>%s)/sample/(?P<sample>%s)/(?P<rank>\d+)/measures/'
        % (SLUG_RE, SLUG_RE),
        AssessmentMeasuresAPIView.as_view(), name='api_assessment_measures'),
    url(r'^(?P<interviewee>%s)/sample/(?P<sample>%s)/(?P<rank>\d+)/' % (
        SLUG_RE, SLUG_RE),
        AssessmentAnswerAPIView.as_view(), name='survey_api_answer'),
    url(r'(?P<interviewee>%s)/sample/(?P<sample>%s)(?P<path>%s)/?' % (
        SLUG_RE, SLUG_RE, PATH_RE),
        AssessmentAPIView.as_view(), name='survey_api_sample'),
    url(r'(?P<interviewee>%s)/sample/' % (SLUG_RE,),
        include('survey.urls.api.sample')),
]
