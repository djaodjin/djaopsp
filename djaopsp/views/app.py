# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.helpers import update_context_urls
from django.conf import settings
from django.views.generic import TemplateView
from survey.models import Answer

from ..compat import reverse
from ..mixins import AccountMixin
from ..utils import (get_latest_active_assessments,
    get_latest_completed_assessment)

LOGGER = logging.getLogger(__name__)


class AppView(AccountMixin, TemplateView):
    """
    Homepage for an organization.
    """
    template_name = 'app/index.html'

    @property
    def unlock_editors(self):
        is_broker = bool(self.accessible_profiles & settings.UNLOCK_BROKERS)
        accessible_plans = {plan['slug']
            for plan in self.get_accessible_plans(self.request,
                    profile=str(self.account) # if we don't convert to `str`,
                                              # the equality will be `False`.
            )}
        unlock_editors = getattr(settings, 'UNLOCK_EDITORS', [])
        return (is_broker or not unlock_editors or
            accessible_plans & unlock_editors)

    @property
    def unlock_portfolios(self):
        is_broker = bool(self.accessible_profiles & settings.UNLOCK_BROKERS)
        accessible_plans = {plan['slug']
            for plan in self.get_accessible_plans(self.request,
                    profile=str(self.account) # if we don't convert to `str`,
                                              # the equality will be `False`.
            )}
        unlock_portfolios = getattr(settings, 'UNLOCK_PORTFOLIOS', [])
        return (is_broker or not unlock_portfolios or
            accessible_plans & unlock_portfolios)

    def get_template_names(self):
        candidates = ['app/%s.html' % self.account.slug]
        candidates += super(AppView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(AppView, self).get_context_data(**kwargs)
        context.update({
            'latest_completed_assessment': get_latest_completed_assessment(
                self.account),
            'active_assessment_in_progress': Answer.objects.filter(
                sample__in=get_latest_active_assessments(self.account)).exists()
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
        if self.unlock_portfolios:
            update_context_urls(context, {
                'reporting': reverse(
                    'reporting', args=(self.account,)),
            })
        if self.unlock_editors:
            update_context_urls(context, {
                'pages_editables_index': reverse(
                    'pages_editables_index', args=(self.account,)),
                'survey_campaign_list': reverse(
                    'survey_campaign_list', args=(self.account,)),
            })
        return context
