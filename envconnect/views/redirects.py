# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.apps.django.redirects import (
    AccountRedirectView as AccountRedirectBaseView)
from survey.models import Matrix

from ..mixins import ReportMixin


LOGGER = logging.getLogger(__name__)


class AccountRedirectView(ReportMixin, AccountRedirectBaseView):

    redirect_roles = ['manager', 'contributor']

    def get_redirect_roles(self, request):
        if self.pattern_name in ['scorecard_organization_redirect']:
            return self.redirect_roles + ['viewer']
        return super(AccountRedirectView, self).get_redirect_roles(request)


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
