# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging

from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
from deployutils.apps.django.redirects import (
    AccountRedirectView as AccountRedirectBaseView)
from survey.models import Matrix

from ..mixins import ReportMixin
from ..models import Consumption


LOGGER = logging.getLogger(__name__)


class AccountRedirectView(ReportMixin, AccountRedirectBaseView):

    redirect_roles = ['manager', 'contributor']

    def get_redirect_roles(self, request):
        if self.pattern_name in ['scorecard_organization_redirect']:
            return self.redirect_roles + ['viewer']
        return super(AccountRedirectView, self).get_redirect_roles(request)

    def get(self, request, *args, **kwargs):
        if self.manages(settings.APP_NAME):
            kwargs.update({self.slug_url_kwarg: settings.APP_NAME})
            return http.HttpResponseRedirect(
                self.get_redirect_url(*args, **kwargs))
        return super(AccountRedirectView, self).get(request, *args, **kwargs)


class MyTSPRedirectView(AccountRedirectView):

    def get(self, request, *args, **kwargs):
        candidates = Matrix.objects.filter(
            account__slug__in=self.accessibles(roles=self.redirect_roles))
        if not candidates:
            return self.response_class(
                request=self.request,
                template='envconnect/reporting/locked.html',
                context={'request': self.request},
                using=self.template_engine,
                content_type=self.content_type)
        return super(MyTSPRedirectView, self).get(request, *args, **kwargs)
