# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import logging

from django.views.generic import TemplateView

from ..mixins import AccountMixin


LOGGER = logging.getLogger(__name__)


class AssessMetricsView(AccountMixin, TemplateView):
    """
    Profile assessment page
    """
    template_name = 'app/assess/metrics/ghg-emissions.html'

    def get_template_names(self):
        candidates = []
        candidates += super(AssessMetricsView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(AssessMetricsView, self).get_context_data(**kwargs)
        return context


class AssessPracticesView(AccountMixin, TemplateView):
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
