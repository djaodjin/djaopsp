# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from pages.settings import PATH_RE, SLUG_RE
from rules.urldecorators import include, url

from ...views.assessments import (AssessmentView, AssessmentXLSXView,
    CompleteView, TargetsView)
from ...views.benchmark import BenchmarkView, BenchmarkDownloadView
from ...views.compare import (PortfoliosDetailView, SuppliersView,
    SuppliersSummaryXLSXView, SuppliersAssessmentsXLSXView,
    SuppliersPlanningXLSXView, SuppliersImprovementsXLSXView)
from ...views.detail import DetailView, DetailXLSXView
from ...views.index import AppView
from ...views.improvements import (ImprovementView, ImprovementPDFView,
    ImprovementXLSXView)
from ...views.redirects import LastCompletedRedirectView
from ...views.share import ShareView

NON_EMPTY_PATH_RE = r'(/[a-zA-Z0-9\-]+)+'

urlpatterns = [
    # Dashboard
    url(r'app/(?P<organization>%s)/reporting(?P<path>%s)/improvements/download/'
        % (SLUG_RE, PATH_RE),
        SuppliersImprovementsXLSXView.as_view(),
        name='reporting_organization_improvements_download'),
    url(r'app/(?P<organization>%s)/reporting(?P<path>%s)/improve/download/'
        % (SLUG_RE, PATH_RE),
        SuppliersPlanningXLSXView.as_view(),
        name='reporting_organization_improve_download'),
    url(r'app/(?P<organization>%s)/reporting(?P<path>%s)/assess/download/'
        % (SLUG_RE, PATH_RE),
        SuppliersAssessmentsXLSXView.as_view(),
        name='reporting_organization_assess_download'),
    url(r'app/(?P<organization>%s)/reporting(?P<path>%s)/download/'
        % (SLUG_RE, PATH_RE),
        SuppliersSummaryXLSXView.as_view(),
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
        'intro(?P<path>%s)/' % (SLUG_RE,
        SLUG_RE, PATH_RE), AssessmentView.as_view(),
        name='assess_intro'),
    url(r'app/(?P<organization>%s)/assess/(?P<sample>%s)/'\
        'download(?P<path>%s)/' % (SLUG_RE,
        SLUG_RE, PATH_RE), AssessmentXLSXView.as_view(),
        name='assess_organization_sample_download'),
    url(r'app/(?P<organization>%s)/assess/(?P<sample>%s)/'\
        'content(?P<path>%s)/' % (SLUG_RE,
        SLUG_RE, PATH_RE), AssessmentView.as_view(),
        name='assess_organization'),
    url(r'app/(?P<organization>%s)/assess/new/' % SLUG_RE,
        AssessmentView.as_view(),
        name='assess_new'),
    url(r'app/(?P<organization>%s)/assess(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), AssessmentView.as_view(),
        name='assess_organization_redirect'), # XXX redirect to most current

    # Improvement plan
    url(r'app/(?P<organization>%s)/improve/(?P<sample>%s)/'\
        'intro(?P<path>%s)/' % (SLUG_RE,
        SLUG_RE, PATH_RE), ImprovementView.as_view(),
        name='improve_intro'),
    url(r'app/(?P<organization>%s)/improve/(?P<sample>%s)/'\
        'print(?P<path>%s)/' % (SLUG_RE,
        SLUG_RE, PATH_RE), ImprovementPDFView.as_view(),
        name='improve_organization_sample_print'),
    url(r'app/(?P<organization>%s)/improve/(?P<sample>%s)/'\
        'download(?P<path>%s)/' % (SLUG_RE,
        SLUG_RE, PATH_RE), ImprovementXLSXView.as_view(),
        name='improve_organization_sample_download'),
    url(r'app/(?P<organization>%s)/improve/(?P<sample>%s)/'\
        'content(?P<path>%s)/' % (SLUG_RE,
        SLUG_RE, PATH_RE), ImprovementView.as_view(),
        name='improve_organization'),
    url(r'app/(?P<organization>%s)/improve(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), ImprovementView.as_view(),
        name='improve_organization_redirect'),

    # Complete
    url(r'app/(?P<organization>%s)/complete/(?P<sample>%s)/'\
        'content(?P<path>%s)/' % (SLUG_RE, SLUG_RE, PATH_RE),
        CompleteView.as_view(),
        name='complete_organization'),
    url(r'app/(?P<organization>%s)/complete(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), LastCompletedRedirectView.as_view(
            pattern_name='complete_organization'),
        name='complete_organization_redirect'),  # XXX redirect to most current

    # Benchmarks and scorecards
    url(r'app/(?P<organization>%s)/scorecard/(?P<sample>%s)/'\
        'download(?P<path>%s)/' % (SLUG_RE, SLUG_RE, PATH_RE),
        BenchmarkDownloadView.as_view(),
        name='scorecard_organization_download'),
    url(r'app/(?P<organization>%s)/scorecard/(?P<sample>%s)/'\
        'content(?P<path>%s)/'
        % (SLUG_RE, SLUG_RE, PATH_RE),
        BenchmarkView.as_view(),
        name='scorecard_organization'),
    url(r'app/(?P<organization>%s)/scorecard(?P<path>%s)/$' % (
        SLUG_RE, PATH_RE), LastCompletedRedirectView.as_view(
            pattern_name='scorecard_organization'),
        name='scorecard_organization_redirect'), # XXX redirect to most current

    # Share
    url(r'app/(?P<organization>%s)/share/(?P<sample>%s)/'\
        'content(?P<path>%s)/' % (SLUG_RE, SLUG_RE, PATH_RE),
        ShareView.as_view(),
        name='share_organization'),
    url(r'app/(?P<organization>%s)/share(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), LastCompletedRedirectView.as_view(
            pattern_name='share_organization'),
        name='share_organization_redirect'),     # XXX redirect to most current

    # Best practices info pages
    url(r'app/(?P<organization>%s)/info(?P<path>%s)/download/' % (
        SLUG_RE, PATH_RE),
        DetailXLSXView.as_view(), name='summary_organization_download'),
    url(r'app/(?P<organization>%s)/info(?P<path>%s)/' % (
        SLUG_RE, PATH_RE),
        DetailView.as_view(), name='summary_organization_redirect'),

    # App page
    url(r'app/(?P<organization>%s)/$' % SLUG_RE,
        AppView.as_view(), name='organization_app'),
]
