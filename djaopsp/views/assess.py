# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import logging

from django.views.generic import TemplateView

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


class AssessPracticesView(ReportMixin, TemplateView):
    """
    Profile assessment page
    """
    template_name = 'app/assess/index.html'

    def get_template_names(self):
        candidates = ['app/assess/%s.html' % self.sample.campaign]
        candidates += super(AssessPracticesView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(AssessPracticesView, self).get_context_data(**kwargs)
        return context
