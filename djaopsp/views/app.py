# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.helpers import update_context_urls
from django.conf import settings
from django.views.generic import TemplateView

from ..compat import reverse
from ..mixins import AccountMixin
from ..utils import get_latest_completed_assessment

LOGGER = logging.getLogger(__name__)


class AppView(AccountMixin, TemplateView):
    """
    Homepage for an organization.
    """
    template_name = 'app/index.html'

    def get_template_names(self):
        candidates = ['app/%s.html' % self.account.slug]
        candidates += super(AppView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(AppView, self).get_context_data(**kwargs)
        context.update({
            'latest_completed_assessment': get_latest_completed_assessment(
                self.account),
        })
        update_context_urls(context, {
            'pages_index': reverse('pages_index'),
            'track_metrics': reverse('track_metrics_index',
                args=(self.account,)),
            'scorecard_history': reverse('scorecard_history',
                args=(self.account,)),
            'scorecard_redirect': reverse('scorecard_redirect',
                args=(self.account,)),
        })
        unlock_portfolios = getattr(settings, 'UNLOCK_PORTFOLIOS', [])
        if (self.manages(settings.APP_NAME) or
            not unlock_portfolios or
            self.accessible_plans & unlock_portfolios):
            update_context_urls(context, {
                'reporting': reverse(
                    'reporting', args=(self.account,)),
            })
        unlock_editors = getattr(settings, 'UNLOCK_EDITORS', [])
        if (self.manages(settings.APP_NAME) or
            not unlock_editors or
            self.accessible_plans & unlock_editors):
            update_context_urls(context, {
                'pages_editables_index': reverse(
                    'pages_editables_index', args=(self.account,)),
                'survey_campaign_list': reverse(
                    'survey_campaign_list', args=(self.account,)),
            })
        return context
