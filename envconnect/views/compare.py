# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging

from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from deployutils.apps.django.mixins import AccessiblesMixin
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_prefixed)

from ..mixins import AccountMixin

LOGGER = logging.getLogger(__name__)


class ReportingEntitiesView(AccountMixin, AccessiblesMixin, TemplateView):

    template_name = 'envconnect/reporting/index.html'

    def get_context_data(self, **kwargs):
        context = super(ReportingEntitiesView, self).get_context_data(**kwargs)
        accounts = self.managed_accounts
        if len(accounts) == 1:
            totals_chart_url = reverse('matrix_chart',
                args=(accounts[0], '/totals'))
        else:
            totals_chart_url = reverse('envconnect_portfolio',
                args=('/totals',))
        urls = {
            'api_suppliers': reverse('api_suppliers', args=(self.account,)),
            'api_accessibles': site_prefixed(
                "/api/users/%s/accessibles/" % str(self.request.user)),
            'api_organizations': site_prefixed("/api/profile/"),
            'totals_chart': totals_chart_url,
        }
        context.update({'score_toggle': True})
        self.update_context_urls(context, urls)
        return context
