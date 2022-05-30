# Copyright (c) 2022, DjaoDjin inc.

from deployutils.apps.django.mockup.views import SigninView
from deployutils.apps.django.urlbuilders import url_prefixed
from django.conf import settings
from django.views.generic import RedirectView
from django.views.static import serve as django_static_serve
from django.urls import path, re_path, include

from .. import __version__
from ..urlbuilders import login_required


if settings.DEBUG: #pylint: disable=no-member
    from django.contrib import admin
    from django.views.defaults import page_not_found, server_error
    from ..views.assets import AssetView

    urlpatterns = [
# XXX We cannot import name 'get_safe_settings' from 'django.views.debug'
#        path(r'__debug__/', include('debug_toolbar.urls')),
# XXX django.contrib.admin does not support Jinja2 templates
#        path('admin/', admin.site.urls),

        # You need to run `python manage.py --nostatic` to enable hotreload.
        url_prefixed(r'static/(?P<path>.*)', AssetView.as_view()),
        path(r'%s%s<path:path>' % (
            settings.APP_NAME, settings.MEDIA_URL), django_static_serve, {
            'document_root': settings.MEDIA_ROOT}),
        path(r'404/', page_not_found),
        path(r'500/', server_error),
    ]
else:
    urlpatterns = [
        re_path(r'%s/(?P<path>static/.*)' % settings.APP_NAME,
            django_static_serve,
            {'document_root': settings.HTDOCS}),
        re_path(r'(?P<path>static/.*)', django_static_serve,
            {'document_root': settings.HTDOCS}),
        path(r'%s<path:path>' % settings.MEDIA_URL, django_static_serve,
            {'document_root': settings.MEDIA_ROOT}),
    ]

if settings.API_DEBUG:
    from rest_framework.schemas import get_schema_view
    from ..views.api_docs import APIDocView
    urlpatterns += [
        path(r'docs/api/schema/', get_schema_view(
            title="DjaoPsp API",
            version=__version__,
            description="API for the Practices Sharing Platform",
        ), name='openapi-schema'),
        path(r'docs/api/', APIDocView.as_view()),
    ]

urlpatterns += [
    # User authenticated
    url_prefixed(r'api/', include('djaopsp.urls.api')),
    url_prefixed(r'', include('djaopsp.urls.views')),

    # Theses views will be intercepted by the proxy.
    url_prefixed(r'', include('deployutils.apps.django.mockup.urls')),
    url_prefixed(r'$', SigninView.as_view(), name='homepage'),
]
