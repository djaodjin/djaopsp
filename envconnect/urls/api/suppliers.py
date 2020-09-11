# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from django.conf.urls import url, include
from survey.settings import PATH_RE, SLUG_RE

from ...api.assessments import (AssessmentAPIView, AssessmentAnswersAPIView,
    AssessmentFreezeAPIView, AssessmentResetAPIView)
from ...api.benchmark import (BenchmarkAPIView, PracticeBenchmarkAPIView,
    HistoricalScoreAPIView)
from ...api.dashboards import (SupplierListAPIView,
    TotalScoreBySubsectorAPIView, ShareScorecardAPIView)
from ...api.improvements import (ImprovementListAPIView,
    ImprovementAnswerAPIView)

urlpatterns = [
    url(r'(?P<organization>%s)/suppliers/(?P<path>%s)'
        % (SLUG_RE, PATH_RE),
        SupplierListAPIView.as_view(), name="api_suppliers"),
    url(r'(?P<organization>%s)/matrix/(?P<path>%s)' % (
        SLUG_RE, PATH_RE),
        TotalScoreBySubsectorAPIView.as_view()),
    url(r'(?P<organization>%s)/campaign/' % SLUG_RE,
        include('survey.urls.api.campaigns')),
    url(r'(?P<organization>%s)/' % SLUG_RE,
        include('survey.urls.api.matrix')),

    url(r'(?P<organization>%s)/benchmark/share/(?P<path>%s)' % (
        SLUG_RE, PATH_RE),
        ShareScorecardAPIView.as_view(),
        name="api_scorecard_share"),
    url(r'(?P<organization>%s)/benchmark/historical/(?P<path>%s)' % (
        SLUG_RE, PATH_RE),
        HistoricalScoreAPIView.as_view(),
        name="api_historical_scores"),
    url(r'(?P<organization>%s)/benchmark/(?P<sample>%s)/'\
        'details/(?P<path>%s)' % (SLUG_RE, SLUG_RE, PATH_RE),
        PracticeBenchmarkAPIView.as_view(),
        name="api_benchmark_practices"),
    url(r'(?P<organization>%s)/benchmark/(?P<sample>%s)/'\
        'graphs/(?P<path>%s)' % (SLUG_RE, SLUG_RE, PATH_RE),
        BenchmarkAPIView.as_view(),
        name="api_benchmark"),
    url(r'(?P<organization>%s)/improvement$' % SLUG_RE,
        ImprovementListAPIView.as_view(),
        name='api_improvement_base'),
    url(r'(?P<organization>%s)/improvement/(?P<path>%s)' % (
        SLUG_RE, PATH_RE),
        ImprovementAnswerAPIView.as_view(),
        name='api_improvement'),
    url(r'(?P<organization>%s)/sample/(?P<sample>%s)/answers/(?P<path>%s)' % (
        SLUG_RE, SLUG_RE, PATH_RE),
        AssessmentAnswersAPIView.as_view(), name='survey_api_sample_answers'),
    url(r'(?P<organization>%s)/sample/(?P<sample>%s)/reset/(?P<path>%s)' % (
        SLUG_RE, SLUG_RE, PATH_RE),
        AssessmentResetAPIView.as_view(), name='survey_api_sample_reset'),
    url(r'(?P<organization>%s)/sample/(?P<sample>%s)/freeze/(?P<path>%s)' % (
        SLUG_RE, SLUG_RE, PATH_RE),
        AssessmentFreezeAPIView.as_view(), name='survey_api_sample_freeze'),
    url(r'(?P<organization>%s)/sample/(?P<sample>%s)' % (
        SLUG_RE, SLUG_RE),
        AssessmentAPIView.as_view(), name='survey_api_sample'),
    url(r'(?P<organization>%s)/sample/' % (SLUG_RE,),
        include('survey.urls.api.sample')),
]
