# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from __future__ import unicode_literals

import logging

from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from survey.views.portfolios import PortfoliosView

from ..compat import reverse
from ..mixins import ReportMixin
from ..utils import (get_latest_active_assessments,
    get_latest_completed_assessment)


LOGGER = logging.getLogger(__name__)


class ShareView(ReportMixin, PortfoliosView):

    template_name = 'app/share/index.html'

    def get_reverse_kwargs(self):
        """
        List of kwargs taken from the url that needs to be passed through
        to ``get_success_url``.
        """
        if self.account_url_kwarg:
            return [self.account_url_kwarg]
        return []

    def get_context_data(self, **kwargs):
        context = super(ShareView, self).get_context_data(**kwargs)
        latest_completed_assessment = get_latest_completed_assessment(
            self.sample.account, campaign=self.sample.campaign)
        context.update({
            'sample': self.sample,
            'campaign': self.sample.campaign,
            'latest_completed_assessment': latest_completed_assessment,
        })
        update_context_urls(context, {
            'api_account_candidates': site_url("/api/accounts/profiles"),
        })
        if latest_completed_assessment:
            active_assessment = get_latest_active_assessments(
                self.sample.account, campaign=self.sample.campaign).get()
            update_context_urls(context, {
                'update_assessment': reverse('scorecard',
                    args=(active_assessment.account, active_assessment))
            })
        return context
