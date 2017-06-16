# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging

from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
from deployutils.redirects import AccountRedirectView as AccountRedirectBaseView
from survey.models import Response

from ..mixins import ReportMixin
from ..models import Consumption
from ..templatetags.navactive import category_entry


LOGGER = logging.getLogger(__name__)


class AccountRedirectView(ReportMixin, AccountRedirectBaseView):

    redirect_roles = ['manager', 'contributor']

    def get(self, request, *args, **kwargs):
        if self.manages(settings.APP_NAME):
            kwargs.update({self.slug_url_kwarg: settings.APP_NAME})
            return http.HttpResponseRedirect(
                self.get_redirect_url(*args, **kwargs))
        return super(AccountRedirectView, self).get(request, *args, **kwargs)
