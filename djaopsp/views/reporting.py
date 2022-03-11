# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import logging

from django.views.generic import TemplateView


LOGGER = logging.getLogger(__name__)


class ReportsRequestedView(TemplateView):
    """
    Tracking requested reports
    """
    template_name = 'app/reporting/index.html'
