# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

from pages.settings import PATH_RE, SLUG_RE
from urldecorators import include, url

from ...views.assessments import AssessmentView, AssessmentXLSXView
from ...views.benchmark import (BenchmarkView,
    ScoreCardView, ScoreCardDownloadView, ScoreCardRedirectView)
from ...views.compare import (SuppliersView, SuppliersXLSXView,
    PortfoliosDetailView)
from ...views.detail import DetailView, DetailXLSXView
from ...views.index import AppView
from ...views.improvements import (ImprovementView, ImprovementPDFView,
    ImprovementXLSXView)
from ...views.share import ShareView, ShareRedirectView

NON_EMPTY_PATH_RE = r'(/[a-zA-Z0-9\-]+)+'

urlpatterns = [
    # direct manager of :organization
    url(r'app/(?P<organization>%s)/reporting/download/' % SLUG_RE,
        SuppliersXLSXView.as_view(),
        name='organization_reporting_entities_download'),

    url(r'app/(?P<organization>%s)/reporting/' % SLUG_RE,
        SuppliersView.as_view(),
        name='organization_reporting_entities'),
    url(r'app/(?P<organization>%s)/portfolios(?P<path>%s)/'
               % (SLUG_RE, NON_EMPTY_PATH_RE),
        PortfoliosDetailView.as_view(), name='matrix_chart'),

    url(r'app/(?P<organization>%s)/portfolios/' % SLUG_RE,
        include('survey.urls.matrix')),
    url(r'app/(?P<organization>%s)/assess/(?P<sample>%s)/'\
        'sample(?P<path>%s)/download/' % (SLUG_RE, SLUG_RE, PATH_RE),
        AssessmentXLSXView.as_view(),
        name='envconnect_sample_organization_download'),
    url(r'app/(?P<organization>%s)/assess/(?P<sample>%s)/'\
        'sample(?P<path>%s)/'
        % (SLUG_RE, SLUG_RE, PATH_RE),
        AssessmentView.as_view(),
        name='envconnect_sample_organization'),
    url(r'app/(?P<organization>%s)/assess/?$' % (
        SLUG_RE), ScoreCardRedirectView.as_view(
            pattern_name='envconnect_assess_organization'),
        name='assess_organization_redirect'),

    url(r'app/(?P<organization>%s)/assess(?P<path>%s)/download/' % (
        SLUG_RE, PATH_RE), AssessmentXLSXView.as_view(),
        name='envconnect_assess_organization_download'),
    url(r'app/(?P<organization>%s)/assess(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), AssessmentView.as_view(),
        name='envconnect_assess_organization'),
    url(r'app/(?P<organization>%s)/improve(?P<path>%s)/print/' % (
        SLUG_RE, PATH_RE), ImprovementPDFView.as_view(),
        name='envconnect_improve_organization_print'),
    url(r'app/(?P<organization>%s)/improve(?P<path>%s)/download/' % (
        SLUG_RE, PATH_RE), ImprovementXLSXView.as_view(),
        name='envconnect_improve_organization_download'),
    url(r'app/(?P<organization>%s)/improve(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), ImprovementView.as_view(),
        name='envconnect_improve_organization'),
    url(r'app/(?P<organization>%s)/benchmark/$' % (
        SLUG_RE), ScoreCardRedirectView.as_view(
            pattern_name='benchmark_organization'),
        name='benchmark_organization_redirect'),
    url(r'app/(?P<organization>%s)/benchmark(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), BenchmarkView.as_view(),
        name='benchmark_organization'),
    url(r'app/(?P<organization>%s)/scorecard(?P<path>%s)/download/' % (
        SLUG_RE, PATH_RE), ScoreCardDownloadView.as_view(),
        name='scorecard_download_organization'),
    url(r'app/(?P<organization>%s)/scorecard/?$' % (
        SLUG_RE), ScoreCardRedirectView.as_view(
            pattern_name='scorecard_organization'),
        name='scorecard_organization_redirect'),
    url(r'app/(?P<organization>%s)/scorecard(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), ScoreCardView.as_view(),
        name='scorecard_organization'),
    url(r'app/(?P<organization>%s)/share/?$' % (
        SLUG_RE), ShareRedirectView.as_view(
            pattern_name='envconnect_share_organization'),
        name='envconnect_share_organization_redirect'),
    url(r'app/(?P<organization>%s)/share(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), ShareView.as_view(),
        name='envconnect_share_organization'),
    url(r'app/(?P<organization>%s)/info(?P<path>%s)/download/' % (
        SLUG_RE, PATH_RE),
        DetailXLSXView.as_view(), name='summary_organization_download'),
    url(r'app/(?P<organization>%s)/info(?P<path>%s)/' % (
        SLUG_RE, PATH_RE),
        DetailView.as_view(), name='summary_organization'),

    url(r'app/(?P<organization>%s)/$' % SLUG_RE,
        AppView.as_view(), name='organization_app'),
]
