# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.helpers import update_context_urls
from django.views.generic import TemplateView
from pages.mixins import TrailMixin

from ..compat import reverse
from ..mixins import AccountMixin, ReportMixin


LOGGER = logging.getLogger(__name__)


class TrackMetricsView(AccountMixin, TemplateView):
    """
    Profile metrics page
    """
    template_name = 'app/track/index.html'

    def get_template_names(self):
        candidates = []
        metric = self.kwargs.get('metric')
        if metric:
            candidates += ['app/track/%s.html' % str(metric)]
        candidates += super(TrackMetricsView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(TrackMetricsView, self).get_context_data(**kwargs)
        return context


class AssessPracticesView(ReportMixin, TrailMixin, TemplateView):
    """
    Profile assessment page
    """
    template_name = 'app/assess/index.html'
    breadcrumb_url = 'assess_practices'

    def get_reverse_kwargs(self):
        """
        List of kwargs taken from the url that needs to be passed through
        to ``reverse``.
        """
        return [self.account_url_kwarg, self.sample_url_kwarg,
            self.path_url_kwarg]

    def get_template_names(self):
        candidates = ['app/assess/%s.html' % self.sample.campaign]
        candidates += super(AssessPracticesView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(AssessPracticesView, self).get_context_data(**kwargs)
        context.update({'prefix': self.full_path})
        update_context_urls(context, {
            'context_base': reverse('pages_index'),
            'api_content': reverse('api_sample_content',
                args=(self.account, self.sample,
                      self.full_path.lstrip(self.URL_PATH_SEP))),
            'api_assessment_sample': reverse(
                'survey_api_sample', args=(self.account, self.sample))
        })
        return context
