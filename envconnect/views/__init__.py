# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging

from django import http
from django.core.urlresolvers import reverse
from deployutils.redirects import AccountRedirectView as AccountRedirectBaseView
from survey.models import Response

from ..mixins import ReportMixin
from ..models import Consumption


LOGGER = logging.getLogger(__name__)


class AccountRedirectView(ReportMixin, AccountRedirectBaseView):

    def get(self, request, *args, **kwargs):
        if not self.kwargs.get('path', None):
            response = None
            managed = self.get_managed(request)
            count = len(managed)
            if count == 1 and not self.create_more:
                organization = managed[0]
                queryset = Response.objects.filter(
                    account__slug=organization['slug'],
                    survey__title=self.report_title)
                response = queryset.first()
            if not response:
                return http.HttpResponseRedirect(reverse('homepage'))
            queryset = Consumption.objects.filter(
                answer__response=response).order_by('-path')
            candidate = queryset.first()
            if candidate and candidate.path:
                kwargs.update({'path': '/%s/%s' % (
                    'sustainability', candidate.path.split('/')[1])})
            else:
                kwargs.update({'path': ''})
        return super(AccountRedirectView, self).get(request, *args, **kwargs)
