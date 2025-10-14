# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.apps.django_deployutils.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from survey.views.matrix import CompareView as CompareBaseView

from ..compat import gettext_lazy as _, reverse
from .portfolios import UpdatedMenubarMixin

LOGGER = logging.getLogger(__name__)

# Deprecated
class CompareView(UpdatedMenubarMixin, CompareBaseView):
    """
    Compare samples side-by-side
    """
    breadcrumb_url = 'matrix_compare_path'

    def get_context_data(self, **kwargs):
        context = super(CompareView, self).get_context_data(**kwargs)
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
            'api_question_typeahead': reverse(
                'api_campaign_questions', args=(self.campaign,)),
            'pages_index': reverse('pages_index'),
            'api_benchmarks_index': reverse(
                'survey_api_benchmarks_index', args=(self.account,)),
            'api_benchmarks_export': reverse('api_benchmarks_export',
                args=(self.account,)),
        })
        url_kwargs = self.get_url_kwargs()
        if 'path' in self.kwargs:
            url_kwargs.update({'path': self.kwargs.get('path')})
            update_context_urls(context, {
                'download': reverse(
                    'download_matrix_compare_path', kwargs=url_kwargs),
            })
        else:
            update_context_urls(context, {
                'download': reverse(
                    'download_matrix_compare', kwargs=url_kwargs),
            })
        return context
