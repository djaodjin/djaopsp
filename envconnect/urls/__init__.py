# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from django.conf import settings
from django.views.generic import RedirectView, TemplateView
from django.views.static import serve as static_serve
from urldecorators import include, url
from deployutils.apps.django.redirects import (
    AccountRedirectView as AccountRedirectBaseView)

from ..api.dashboards import TotalScoreBySubsectorAPIView
from ..api.suppliers import SupplierListAPIView
from ..urlbuilders import (APP_PREFIX, url_prefixed, url_authenticated,
    url_direct)
from ..views import AccountRedirectView
from ..views.best_practices import (BestPracticeDetailView,
    FollowBestPracticeView, UnfollowBestPracticeView, BestPracticeVoteView)
from ..views.benchmark import (BenchmarkView, PortfoliosDetailView,
    ScoreCardView, ScoreCardDownloadView, ScoreCardRedirectView)
from ..views.compare import ReportingEntitiesView
from ..views.index import IndexView
from ..views.improvements import ReportPDFView
from ..views.self_assessment import SelfAssessmentView, SelfAssessmentCSVView
from ..views.detail import DetailView
from ..views.improvements import ImproveView, ImprovementCSVView

if settings.DEBUG: #pylint: disable=no-member
    from django.contrib import admin
    from django.views.defaults import page_not_found, server_error
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    import debug_toolbar

    admin.autodiscover()
    urlpatterns = staticfiles_urlpatterns()
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
        url(r'^media/(?P<path>.*)$', static_serve, {
            'document_root': settings.MEDIA_ROOT}),
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
        url(r'^admin/', include(admin.site.urls)),
        url(r'^404/$', page_not_found),
        url(r'^500/$', server_error),
    ]
else:
    urlpatterns = [
        url(r'^envconnect/(?P<path>static/.*)$', static_serve,
            {'document_root': settings.HTDOCS}),
        url(r'^(?P<path>static/.*)$', static_serve,
            {'document_root': settings.HTDOCS}),
        url(r'^media/envconnect/(?P<path>.*)$', static_serve,
            {'document_root': settings.MEDIA_ROOT}),
    ]

SLUG_RE = r'[a-zA-Z0-9-]+'
IDENTIFIER_RE = r'[_a-zA-Z][_a-zA-Z0-9]*'
NON_EMPTY_PATH_RE = r'(/[a-zA-Z0-9\-]+)+'

urlpatterns += [
    # Locking
    #url_direct(r'api/best-practice/(?P<pk>[0-9]+)/lock/',
    #   LockToggleAPIView.as_view(), name='best_practice_lock_toggle'),

    # User authenticated
    url_authenticated(r'api/suppliers/?',
      SupplierListAPIView.as_view(), name="api_suppliers"),

    # envconnect manager
    url_direct(r'api/content/', include('envconnect.urls.api.content')),
    # XXX only used in testing?
    url_direct(r'api/', include('pages.urls.api.elements')),

    # direct manager of :organization
    url_direct(r'api/(?P<organization>%s)/' % SLUG_RE,
        include('envconnect.urls.api.suppliers')),
    url_direct(r'api/(?P<organization>%s)/matrix/(?P<matrix>%s)/?$' % (
        SLUG_RE, SLUG_RE + settings.PATH_RE),
        TotalScoreBySubsectorAPIView.as_view()),
    url_direct(r'api/(?P<organization>%s)/' % SLUG_RE,
        include('survey.urls.api')),

    # authenticated user
    url_authenticated(r'app/info/portfolios(?P<path>%s)/' % settings.PATH_RE,
        AccountRedirectBaseView.as_view(
            pattern_name='matrix_chart',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='envconnect_portfolio'),
    url_authenticated(r'app/info/requests/',
        AccountRedirectBaseView.as_view(
            pattern_name='organization_reporting_entities',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='envconnect_share_requests'),
    url_authenticated(r'app/info/report(?P<path>%s)/' % settings.PATH_RE,
        AccountRedirectView.as_view(pattern_name='report_organization',
            new_account_url='/%sapp/new/' % APP_PREFIX), name='report'),
    url_authenticated(r'app/info/improve(?P<path>%s)/' % settings.PATH_RE,
        AccountRedirectView.as_view(pattern_name='improve_organization',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='envconnect_improve'),
    url_authenticated(r'app/info/benchmark(?P<path>%s)/'
        % settings.PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='benchmark_organization',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='benchmark'),
    url_authenticated(r'app/info/detail(?P<path>%s)/' % settings.PATH_RE,
        BestPracticeDetailView.as_view(), name='best_practice_detail'),
    url_authenticated(r'app/info(?P<path>%s)/' % settings.PATH_RE,
      DetailView.as_view(), name='summary'),

    url_authenticated('app/comments/unfollow(?P<path>%s)/' % settings.PATH_RE,
        UnfollowBestPracticeView.as_view(), name='unfollow_best_practice'),
    url_authenticated('app/comments/follow(?P<path>%s)/' % settings.PATH_RE,
        FollowBestPracticeView.as_view(), name='follow_best_practice'),
    url_authenticated('app/comments/vote(?P<path>%s)/(?P<direction>up)/'
        % settings.PATH_RE,
        BestPracticeVoteView.as_view(), name='vote_best_practice'),
    url_authenticated(r'app/comments/', include('django_comments.urls')),

    # direct manager of :organization
    url_direct(r'app/(?P<organization>%s)/report/print/'\
'(?P<industry>%s)/' % (SLUG_RE, SLUG_RE),
        ReportPDFView.as_view(), name='envconnect_report_print'),
    url_direct(r'app/(?P<organization>%s)/reporting/' % SLUG_RE,
        ReportingEntitiesView.as_view(),
        name='organization_reporting_entities'),
    url_direct(r'app/(?P<organization>%s)/portfolios(?P<path>%s)/'
               % (SLUG_RE, NON_EMPTY_PATH_RE),
        PortfoliosDetailView.as_view(), name='matrix_chart'),

    url_direct(r'app/(?P<organization>%s)/portfolios/' % SLUG_RE,
        include('survey.urls.matrix')),
    url_direct(r'app/(?P<organization>%s)/report(?P<path>%s)/download/' % (
        SLUG_RE, settings.PATH_RE), SelfAssessmentCSVView.as_view(),
        name='report_organization_download'),
    url_direct(r'app/(?P<organization>%s)/report(?P<path>%s)/' % (
        SLUG_RE, settings.PATH_RE), SelfAssessmentView.as_view(),
        name='report_organization'),
    url_direct(r'app/(?P<organization>%s)/improve/download/' % (
        SLUG_RE), ImprovementCSVView.as_view(),
        name='improve_organization_download'),
    url_direct(r'app/(?P<organization>%s)/improve(?P<path>%s)/' % (
        SLUG_RE, settings.PATH_RE), ImproveView.as_view(),
        name='improve_organization'),
    url_direct(r'app/(?P<organization>%s)/benchmark/$' % (
        SLUG_RE), ScoreCardRedirectView.as_view(),
        name='benchmark_organization_redirect'),
    url_direct(r'app/(?P<organization>%s)/benchmark(?P<path>%s)/' % (
        SLUG_RE, settings.PATH_RE), BenchmarkView.as_view(),
        name='benchmark_organization'),
    url_direct(r'app/(?P<organization>%s)/scorecard(?P<path>%s)/download/' % (
        SLUG_RE, settings.PATH_RE), ScoreCardDownloadView.as_view(),
        name='scorecard_download_organization'),
    url_direct(r'app/(?P<organization>%s)/scorecard/?$' % (
        SLUG_RE), ScoreCardRedirectView.as_view(
            pattern_name='scorecard_organization'),
        name='scorecard_organization_redirect'),
    url_direct(r'app/(?P<organization>%s)/scorecard(?P<path>%s)/' % (
        SLUG_RE, settings.PATH_RE), ScoreCardView.as_view(),
        name='scorecard_organization'),
    url_direct(r'app/(?P<organization>%s)/detail(?P<path>%s)/'
        % (SLUG_RE, settings.PATH_RE), BestPracticeDetailView.as_view(),
        name='best_practice_detail_organization'),
    url_direct(r'app/(?P<organization>%s)/summary(?P<path>%s)/' % (
        SLUG_RE, settings.PATH_RE),
        DetailView.as_view(), name='summary_organization'),

    url_authenticated(r'app/',
        AccountRedirectView.as_view(
            pattern_name='benchmark_organization_redirect',
            new_account_url='/%sapp/new/' % APP_PREFIX)),

    # no authentication required

    # These URLs will be served by the djaodjin webapp.
    # XXX fix: remove envconnect prefix when themes are ready.
    url_prefixed(r'', include('deployutils.apps.django.mockup.urls')),
    # XXX The following URL should be envconnect/app/contact/ but for some
    # reasons it would appear there is some javascript code on the
    # IndustryListView that prevents it.
    url_prefixed(r'sponsors/',
        TemplateView.as_view(template_name='sponsors.html'),
        name='sponsors'),
    url_prefixed(r'contact/',
        TemplateView.as_view(template_name='contact.html'),
        name='contact'),
    # XXX These URLs are temporarly here until we are able to serve them
    # from the djaodjin webapp.
    url_prefixed(r'about/$',
        TemplateView.as_view(template_name='about.html'), name='about'),
    url_prefixed(r'$', IndexView.as_view(), name='homepage'),
    url(r'^$',
        RedirectView.as_view(pattern_name='homepage'),
        name='homepage_index'),
]
