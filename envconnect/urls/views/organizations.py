# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from pages.settings import PATH_RE, SLUG_RE
from urldecorators import include, url

from ...views.assessments import AssessmentView, AssessmentXLSXView
from ...views.benchmark import BenchmarkView, BenchmarkDownloadView
from ...views.compare import (PortfoliosDetailView, SuppliersView,
    SuppliersXLSXView, SuppliersImprovementsXLSXView)
from ...views.detail import DetailView, DetailXLSXView
from ...views.index import AppView
from ...views.improvements import (ImprovementView, ImprovementPDFView,
    ImprovementXLSXView)
from ...views.redirects import LastCompletedRedirectView
from ...views.share import ShareView

NON_EMPTY_PATH_RE = r'(/[a-zA-Z0-9\-]+)+'

urlpatterns = [
    # direct manager of :organization
    url(r'app/(?P<organization>%s)/reporting(?P<path>%s)/improvements/download/'
        % (SLUG_RE, PATH_RE),
        SuppliersImprovementsXLSXView.as_view(),
        name='reporting_organization_improvements_download'),
    url(r'app/(?P<organization>%s)/reporting(?P<path>%s)/download/'
        % (SLUG_RE, PATH_RE),
        SuppliersXLSXView.as_view(),
        name='reporting_organization_download'),
    url(r'app/(?P<organization>%s)/reporting(?P<path>%s)/'
        % (SLUG_RE, PATH_RE),
        SuppliersView.as_view(),
        name='reporting_organization'),

    url(r'app/(?P<organization>%s)/portfolios(?P<path>%s)/'
        % (SLUG_RE, NON_EMPTY_PATH_RE),
        PortfoliosDetailView.as_view(), name='matrix_chart'),
    url(r'app/(?P<organization>%s)/portfolios/' % SLUG_RE,
        include('survey.urls.matrix')),

    # Assessments
    url(r'app/(?P<organization>%s)/assess/(?P<sample>%s)/'\
        'sample(?P<path>%s)/download/' % (SLUG_RE,
        SLUG_RE, PATH_RE), AssessmentXLSXView.as_view(),
        name='assess_organization_sample_download'),
    url(r'app/(?P<organization>%s)/assess/(?P<sample>%s)/'\
        'sample(?P<path>%s)/' % (SLUG_RE,
        SLUG_RE, PATH_RE), AssessmentView.as_view(),
        name='assess_organization_sample'),
    url(r'app/(?P<organization>%s)/assess(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), AssessmentView.as_view(),
        name='assess_organization'),

    # Benchmarks
    url(r'app/(?P<organization>%s)/benchmark/(?P<sample>%s)/'\
        'sample(?P<path>%s)/download/' % (SLUG_RE, SLUG_RE, PATH_RE),
        BenchmarkDownloadView.as_view(),
        name='benchmark_organization_download'),
    url(r'app/(?P<organization>%s)/benchmark/(?P<sample>%s)/'\
        'sample(?P<path>%s)/'
        % (SLUG_RE, SLUG_RE, PATH_RE),
        BenchmarkView.as_view(),
        name='benchmark_organization'),

    # XXX Redirects to last completed assessment
    url(r'app/(?P<organization>%s)/benchmark(?P<path>%s)/$' % (
        SLUG_RE, PATH_RE), LastCompletedRedirectView.as_view(
            pattern_name='benchmark_organization'),
        name='benchmark_organization_redirect'),

    url(r'app/(?P<organization>%s)/improve/(?P<sample>%s)/'\
        'sample(?P<path>%s)/print/' % (SLUG_RE,
        SLUG_RE, PATH_RE), ImprovementPDFView.as_view(),
        name='improve_organization_sample_print'),
    url(r'app/(?P<organization>%s)/improve/(?P<sample>%s)/'\
        'sample(?P<path>%s)/download/' % (SLUG_RE,
        SLUG_RE, PATH_RE), ImprovementXLSXView.as_view(),
        name='improve_organization_sample_download'),
    url(r'app/(?P<organization>%s)/improve/(?P<sample>%s)/'\
        'sample(?P<path>%s)/' % (SLUG_RE,
        SLUG_RE, PATH_RE), ImprovementView.as_view(),
        name='improve_organization_sample'),
    url(r'app/(?P<organization>%s)/improve(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), ImprovementView.as_view(),
        name='improve_organization'),

    url(r'app/(?P<organization>%s)/scorecard/(?P<sample>%s)/'\
        'sample(?P<path>%s)/download/' % (SLUG_RE, SLUG_RE, PATH_RE),
        BenchmarkDownloadView.as_view(),
        name='scorecard_organization_download'),
    # XXX Redirects to last completed assessment
    url(r'app/(?P<organization>%s)/scorecard(?P<path>%s)/$' % (
        SLUG_RE, PATH_RE), LastCompletedRedirectView.as_view(
            pattern_name='scorecard_organization'),
        name='scorecard_organization_redirect'),

    url(r'app/(?P<organization>%s)/share(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), ShareView.as_view(),
        name='share_organization'),
    url(r'app/(?P<organization>%s)/info(?P<path>%s)/download/' % (
        SLUG_RE, PATH_RE),
        DetailXLSXView.as_view(), name='summary_organization_download'),
    url(r'app/(?P<organization>%s)/info(?P<path>%s)/' % (
        SLUG_RE, PATH_RE),
        DetailView.as_view(), name='summary_organization_redirect'),

    url(r'app/(?P<organization>%s)/$' % SLUG_RE,
        AppView.as_view(), name='organization_app'),
]
