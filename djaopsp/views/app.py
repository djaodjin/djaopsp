# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.helpers import update_context_urls
from django.views.generic import TemplateView

from ..compat import reverse
from ..mixins import AccountMixin, get_latest_assessment_sample


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
            'latest_assessment': get_latest_assessment_sample(self.account)
        })
        update_context_urls(context, {
            'summary_index': reverse('summary_index'),
            'assess_metrics': reverse('assess_metrics', args=(self.account,)),
            'scorecard_history': reverse(
                'scorecard_history', args=(self.account,)),
            'scorecard_redirect': reverse(
                'scorecard_redirect', args=(self.account,)),
            'reporting': reverse('reporting', args=(self.account,)),
            'survey_campaign_list': reverse(
                'survey_campaign_list', args=(self.account,)),
        })
        return context
