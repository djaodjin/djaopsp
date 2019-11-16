# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

from pages.settings import PATH_RE
from urldecorators import include, url

from ...urlbuilders import APP_PREFIX
from ...views.redirects import AccountRedirectView, MyTSPRedirectView
from ...views.detail import DetailView, DetailXLSXView

urlpatterns = [

    # authenticated user
    url(r'app/info/portfolios(?P<path>%s)/' % PATH_RE,
        MyTSPRedirectView.as_view(
            pattern_name='matrix_chart',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='envconnect_portfolio'),
    url(r'app/info/requests/',
        MyTSPRedirectView.as_view(
            pattern_name='organization_reporting_entities',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='envconnect_share_requests'),
    url(r'app/info/assess(?P<path>%s)/' % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='envconnect_assess_organization',
            new_account_url='/%sapp/new/' % APP_PREFIX),
                name='envconnect_assess'),
    url(r'app/info/improve(?P<path>%s)/' % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='envconnect_improve_organization',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='envconnect_improve'),
    url(r'app/info/benchmark(?P<path>%s)/'
        % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='benchmark_organization',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='benchmark'),
    url(r'app/info/scorecard(?P<path>%s)/'
        % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='scorecard_organization',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='scorecard'),
    url(r'app/info/share(?P<path>%s)/'
        % PATH_RE,
        AccountRedirectView.as_view(
            pattern_name='envconnect_share_organization',
            new_account_url='/%sapp/new/' % APP_PREFIX),
        name='envconnect_share'),
    url(r'app/info(?P<path>%s)/download/' % PATH_RE,
      DetailXLSXView.as_view(), name='summary_download'),
    url(r'app/info(?P<path>%s)/' % PATH_RE,
      DetailView.as_view(), name='summary'),

    url(r'app/comments/', include('django_comments.urls')),
]
