# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from __future__ import unicode_literals

import logging, json

from django.views.generic.base import TemplateView
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_prefixed)
from deployutils.helpers import update_context_urls

from ..compat import reverse
from ..mixins import ReportMixin
from ..suppliers import get_supplier_managers


LOGGER = logging.getLogger(__name__)


class ShareView(ReportMixin, TemplateView):

    template_name = 'envconnect/share/index.html'

    def get_context_data(self, **kwargs):
        context = super(ShareView, self).get_context_data(**kwargs)
        from_root, trail = self.breadcrumbs
        # Find supplier managers subscribed to this profile
        # to share scorecard with.
        is_account_manager = self.manages(self.account)
        if is_account_manager:
            context.update({
                'is_account_manager': is_account_manager})
        context.update({
            'supplier_managers': json.dumps(
                get_supplier_managers(self.account))})
        update_context_urls(context, {
            'api_benchmark_share': reverse('api_benchmark_share',
                args=(context['organization'], from_root)),
            'api_organizations': site_prefixed("/api/profile/"),
            'api_viewers': site_prefixed(
                "/api/profile/%s/roles/viewers/" % self.account),
        })
        return context
