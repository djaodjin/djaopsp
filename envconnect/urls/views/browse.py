# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_prefixed)
from rules.urldecorators import include, url

from ...views.redirects import AccountRedirectView, MyTSPRedirectView
from ...views.detail import ContentDetailXLSXView, DetailView, DetailXLSXView

PATH_RE = r'(/[a-zA-Z0-9\-]+)*'

urlpatterns = [

    # authenticated user
    url(r'app/portfolios(?P<path>%s)/' % PATH_RE,
        MyTSPRedirectView.as_view(
            pattern_name='matrix_chart',
            new_account_url=site_prefixed('/users/roles/accept/')),
        name='envconnect_portfolio'),
    url(r'app/reporting(?P<path>%s)/' % PATH_RE,
        MyTSPRedirectView.as_view(
            pattern_name='reporting_organization',
            new_account_url=site_prefixed('/users/roles/accept/')),
        name='reporting_redirect'),
    url(r'app/assess(?P<path>%s)/' % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='assess_organization_redirect',
            new_account_url=site_prefixed('/users/roles/accept/')),
                name='assess_redirect'),
    url(r'app/improve(?P<path>%s)/' % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='improve_organization_redirect',
            new_account_url=site_prefixed('/users/roles/accept/')),
        name='improve_redirect'),
    url(r'app/complete(?P<path>%s)/'
        % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='complete_organization_redirect',
            new_account_url=site_prefixed('/users/roles/accept/')),
        name='complete_redirect'),
    url(r'app/scorecard(?P<path>%s)/'
        % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='scorecard_organization_redirect',
            new_account_url=site_prefixed('/users/roles/accept/')),
        name='scorecard_redirect'),
    url(r'app/share(?P<path>%s)/'
        % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='share_organization',
            new_account_url=site_prefixed('/users/roles/accept/')),
        name='share_redirect'),
    url(r'app/info/download/content(?P<path>%s)/' % PATH_RE,
      ContentDetailXLSXView.as_view(), name='summary_download_content'),
    url(r'app/info/download(?P<path>%s)/' % PATH_RE,
      DetailXLSXView.as_view(), name='summary_download'),
    url(r'app/info(?P<path>%s)/' % PATH_RE,
      DetailView.as_view(), name='summary'),

    url(r'app/comments/', include('django_comments.urls')),
]
