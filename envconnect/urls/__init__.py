# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_prefixed)
from django.conf import settings
from django.views.generic import RedirectView, TemplateView
from django.views.static import serve as static_serve
from pages.settings import PATH_RE, SLUG_RE
from urldecorators import include, url

from ..urlbuilders import (url_prefixed, url_authenticated,
    url_direct, url_content_manager)
from ..views.redirects import AccountRedirectView, MyTSPRedirectView
from ..views.index import IndexView


if settings.DEBUG: #pylint: disable=no-member
    from django.views.defaults import page_not_found, server_error
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    import debug_toolbar

    urlpatterns = staticfiles_urlpatterns()
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
        url(r'^envconnect%s(?P<path>.*)$' % settings.MEDIA_URL, static_serve, {
            'document_root': settings.MEDIA_ROOT}),
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

urlpatterns += [
    # User authenticated
    url_authenticated(r'api/suppliers/', include('answers.urls.api')),
    url_content_manager(r'api/content/',
        include('envconnect.urls.api.content')),

    # API to manage reporting, assessment and improvement planning.
    url_prefixed(r'api/', include('envconnect.urls.api.suppliers')),

    url_authenticated(r'', include('envconnect.urls.views.browse')),
    url_direct(r'', include('envconnect.urls.views.organizations')),
    url_authenticated(r'app/',
        AccountRedirectView.as_view(
            pattern_name='organization_app',
            new_account_url=site_prefixed('/users/roles/accept/')),
        name='app_redirect'),

    # These URLs will be served by the djaodjin webapp.
    # XXX fix: remove envconnect prefix when themes are ready.
    url_prefixed(r'', include('deployutils.apps.django.mockup.urls')),
    # XXX The following URL should be envconnect/app/contact/ but for some
    # reasons it would appear there is some javascript code on the
    # IndustryListView that prevents it.
    url_prefixed(r'about/',
        TemplateView.as_view(template_name='about.html'),
        name='about'),
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
    # from the djaoapp proxy.
    url_prefixed(r'$', IndexView.as_view(), name='homepage'),
    url(r'^$',
        RedirectView.as_view(pattern_name='homepage'),
        name='homepage_index'),
]
