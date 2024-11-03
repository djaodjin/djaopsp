# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from django.views.generic.base import TemplateView

from ..compat import reverse
from ..mixins import AccountMixin


LOGGER = logging.getLogger(__name__)


class InsightsView(AccountMixin, TemplateView):
    """
    Select between compare side-by-side and aggreagates charts
    """
    template_name = 'app/reporting/insights/index.html'

    def get_context_data(self, **kwargs):
        context = super(InsightsView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'reporting_insights_compare': reverse(
                'reporting_insights_compare', args=(self.account,)),
            'reporting_insights_analyze': reverse(
                'reporting_insights_analyze', args=(self.account,)),
        })
        return context


class InsightsCompareView(AccountMixin, TemplateView):
    """
    Compare responses side-by-side
    """
    template_name = 'app/reporting/insights/compare.html'

    def get_context_data(self, **kwargs):
        context = super(InsightsCompareView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_version': site_url("/api"),
            'api_account_candidates': site_url("/api/accounts/profiles"),
            'api_accounts': site_url("/api/profile"),
            'api_plans': site_url("/api/profile/%(profile)s/plans" % {
                'profile': self.account}),
            'api_subscriptions': site_url(
                "/api/profile/%(profile)s/subscriptions" % {
                    'profile': self.account}),
            'api_units': reverse('survey_api_units'),
            'api_account_groups': reverse('survey_api_accounts_filter_list',
                args=(self.account,)),
            #XXX 'api_question_typeahead': reverse(
            #    'api_campaign_questions', args=(self.campaign,)),
            'pages_index': reverse('pages_index'),
            'api_benchmarks_index': reverse(
                'survey_api_benchmarks_index', args=(self.account,)),
            'api_benchmarks_export': reverse('api_benchmarks_export',
                args=(self.account,)),
            'scorecard_base': reverse(
                'scorecard_redirect', args=(self.account,))
        })
        return context


class InsightsAnalyzeView(AccountMixin, TemplateView):
    """
    Builds aggreagates charts
    """
    # XXX replaces /app/<profile>/reporting/<slug:campaign>/compare/

    template_name = 'app/reporting/insights/analyze.html'

    def get_context_data(self, **kwargs):
        context = super(InsightsAnalyzeView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_version': site_url("/api"),
            'api_account_candidates': site_url("/api/accounts/profiles"),
            'api_accounts': site_url("/api/profile"),
            'api_plans': site_url("/api/profile/%(profile)s/plans" % {
                'profile': self.account}),
            'api_subscriptions': site_url(
                "/api/profile/%(profile)s/subscriptions" % {
                    'profile': self.account}),
            'api_units': reverse('survey_api_units'),
            'api_account_groups': reverse('survey_api_accounts_filter_list',
                args=(self.account,)),
            'api_campaign_typeahead': reverse(
                'survey_api_campaign_list', args=(self.account,)),
            'api_question_typeahead': reverse('api_campaign_base'),
            'pages_index': reverse('pages_index'),
            'api_benchmarks_index': reverse(
                'survey_api_benchmarks_index', args=(self.account,)),
            'api_benchmarks_export': reverse('api_benchmarks_export',
                args=(self.account,)),
        })
        return context
