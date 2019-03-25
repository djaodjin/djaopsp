# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

from django.conf import settings
from django.views.generic import RedirectView, TemplateView
from django.views.static import serve as static_serve
from pages.settings import PATH_RE, SLUG_RE
from urldecorators import include, url

from ..urlbuilders import (APP_PREFIX, url_prefixed, url_authenticated,
    url_direct, url_content_manager)
from ..views import AccountRedirectView, MyTSPRedirectView
from ..views.assessments import AssessmentView, AssessmentXLSXView
from ..views.benchmark import (BenchmarkView,
    ScoreCardView, ScoreCardDownloadView, ScoreCardRedirectView)
from ..views.compare import (SuppliersView, SuppliersXLSXView,
    PortfoliosDetailView)
from ..views.detail import DetailView, DetailXLSXView
from ..views.index import IndexView
from ..views.improvements import (ImprovementView, ImprovementPDFView,
    ImprovementXLSXView)

if settings.DEBUG: #pylint: disable=no-member
    from django.contrib import admin
    from django.views.defaults import page_not_found, server_error
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    import debug_toolbar

    admin.autodiscover()
    urlpatterns = staticfiles_urlpatterns()
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
        url(r'^envconnect%s(?P<path>.*)$' % settings.MEDIA_URL, static_serve, {
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

IDENTIFIER_RE = r'[_a-zA-Z][_a-zA-Z0-9]*'
NON_EMPTY_PATH_RE = r'(/[a-zA-Z0-9\-]+)+'

urlpatterns += [
    # User authenticated
    url_authenticated(r'api/suppliers/', include('answers.urls.api')),
    url_content_manager(r'api/content/',
        include('envconnect.urls.api.content')),

    # API to manage reporting, assessment and improvement planning.
    url_direct(r'api/', include('envconnect.urls.api.suppliers')),

    # authenticated user
    url_authenticated(r'app/info/portfolios(?P<path>%s)/' % PATH_RE,
        MyTSPRedirectView.as_view(
            pattern_name='matrix_chart',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='envconnect_portfolio'),
    url_authenticated(r'app/info/requests/',
        MyTSPRedirectView.as_view(
            pattern_name='organization_reporting_entities',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='envconnect_share_requests'),
    url_authenticated(r'app/info/assess(?P<path>%s)/' % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='envconnect_assess_organization',
            new_account_url='/%sapp/new/' % APP_PREFIX),
                name='envconnect_assess'),
    url_authenticated(r'app/info/improve(?P<path>%s)/' % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='envconnect_improve_organization',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='envconnect_improve'),
    url_authenticated(r'app/info/benchmark(?P<path>%s)/'
        % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='benchmark_organization',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='benchmark'),
    url_authenticated(r'app/info/scorecard(?P<path>%s)/'
        % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='scorecard_organization',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='scorecard'),
    url_authenticated(r'app/info(?P<path>%s)/download/' % PATH_RE,
      DetailXLSXView.as_view(), name='summary_download'),
    url_authenticated(r'app/info(?P<path>%s)/' % PATH_RE,
      DetailView.as_view(), name='summary'),

    url_authenticated(r'app/comments/', include('django_comments.urls')),

    # direct manager of :organization
    url_direct(r'app/(?P<organization>%s)/reporting/download/' % SLUG_RE,
        SuppliersXLSXView.as_view(),
        name='organization_reporting_entities_download'),

    url_direct(r'app/(?P<organization>%s)/reporting/' % SLUG_RE,
        SuppliersView.as_view(),
        name='organization_reporting_entities'),
    url_direct(r'app/(?P<organization>%s)/portfolios(?P<path>%s)/'
               % (SLUG_RE, NON_EMPTY_PATH_RE),
        PortfoliosDetailView.as_view(), name='matrix_chart'),

    url_direct(r'app/(?P<organization>%s)/portfolios/' % SLUG_RE,
        include('survey.urls.matrix')),
    url_direct(r'app/(?P<organization>%s)/sample/(?P<sample>%s)(?P<path>%s)'\
        '/download/' % (SLUG_RE, SLUG_RE, PATH_RE),
        AssessmentXLSXView.as_view(),
        name='envconnect_sample_organization_download'),
    url_direct(r'app/(?P<organization>%s)/sample/(?P<sample>%s)(?P<path>%s)/'
        % (SLUG_RE, SLUG_RE, PATH_RE),
        AssessmentView.as_view(),
        name='envconnect_sample_organization'),
    url_direct(r'app/(?P<organization>%s)/assess(?P<path>%s)/download/' % (
        SLUG_RE, PATH_RE), AssessmentXLSXView.as_view(),
        name='envconnect_assess_organization_download'),
    url_direct(r'app/(?P<organization>%s)/assess(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), AssessmentView.as_view(),
        name='envconnect_assess_organization'),
    url_direct(r'app/(?P<organization>%s)/improve(?P<path>%s)/print/' % (
        SLUG_RE, PATH_RE), ImprovementPDFView.as_view(),
        name='envconnect_improve_organization_print'),
    url_direct(r'app/(?P<organization>%s)/improve(?P<path>%s)/download/' % (
        SLUG_RE, PATH_RE), ImprovementXLSXView.as_view(),
        name='envconnect_improve_organization_download'),
    url_direct(r'app/(?P<organization>%s)/improve(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), ImprovementView.as_view(),
        name='envconnect_improve_organization'),
    url_direct(r'app/(?P<organization>%s)/benchmark/$' % (
        SLUG_RE), ScoreCardRedirectView.as_view(
            pattern_name='benchmark_organization'),
        name='benchmark_organization_redirect'),
    url_direct(r'app/(?P<organization>%s)/benchmark(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), BenchmarkView.as_view(),
        name='benchmark_organization'),
    url_direct(r'app/(?P<organization>%s)/scorecard(?P<path>%s)/download/' % (
        SLUG_RE, PATH_RE), ScoreCardDownloadView.as_view(),
        name='scorecard_download_organization'),
    url_direct(r'app/(?P<organization>%s)/scorecard/?$' % (
        SLUG_RE), ScoreCardRedirectView.as_view(
            pattern_name='scorecard_organization'),
        name='scorecard_organization_redirect'),
    url_direct(r'app/(?P<organization>%s)/scorecard(?P<path>%s)/' % (
        SLUG_RE, PATH_RE), ScoreCardView.as_view(),
        name='scorecard_organization'),
    url_direct(r'app/(?P<organization>%s)/info(?P<path>%s)/download/' % (
        SLUG_RE, PATH_RE),
        DetailXLSXView.as_view(), name='summary_organization_download'),
    url_direct(r'app/(?P<organization>%s)/info(?P<path>%s)/' % (
        SLUG_RE, PATH_RE),
        DetailView.as_view(), name='summary_organization'),

    url_direct(r'app/(?P<organization>%s)/$' % SLUG_RE,
        IndexView.as_view(), name='homepage_organization'),
    url_authenticated(r'app/',
        AccountRedirectView.as_view(
            pattern_name='scorecard_organization_redirect',
            new_account_url='/%sapp/new/' % APP_PREFIX)),

    # URL to download theme to install on proxy.
    url(r'^(?P<path>themes/.*)$', static_serve,
        {'document_root': settings.HTDOCS}),

    # These URLs will be served by the djaodjin webapp.
    # XXX fix: remove envconnect prefix when themes are ready.
    url_prefixed(r'', include('deployutils.apps.django.mockup.urls')),
    # XXX The following URL should be envconnect/app/contact/ but for some
    # reasons it would appear there is some javascript code on the
    # IndustryListView that prevents it.
    url_prefixed(r'sponsors/',
        TemplateView.as_view(template_name='sponsors.html'),
        name='sponsors'),
    url_prefixed(r'docs/faq/',
        TemplateView.as_view(template_name='docs/faq.html'),
        name='faq'),
    url_prefixed(r'docs/legend-1/',
        TemplateView.as_view(template_name='docs/legend-1.html'),
        name='legend-1'),
    url_prefixed(r'docs/legend-2/',
        TemplateView.as_view(template_name='docs/legend-2.html'),
        name='legend-2'),
    url_prefixed(r'docs/legend-3/',
        TemplateView.as_view(template_name='docs/legend-3.html'),
        name='legend-3'),
    url_prefixed(r'contact/',
        TemplateView.as_view(template_name='contact.html'),
        name='contact'),
    # XXX These URLs are temporarly here until we are able to serve them
    # from the djaodjin webapp.
    url_prefixed(r'$', IndexView.as_view(), name='homepage'),
    url(r'^$',
        RedirectView.as_view(pattern_name='homepage'),
        name='homepage_index'),
]
