# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

import logging

from djaopsp.downloads.reporting import ReportingDashboardPPTXView

from ..api.portfolios import (BySegmentsMixin,
    GoalsMixin, GHGEmissionsRateMixin, GHGEmissionsAmountMixin)


LOGGER = logging.getLogger(__name__)


class GoalsPPTXView(GoalsMixin, ReportingDashboardPPTXView):
    """
    Download goals as a .pptx presentation
    """
    basename = 'goals'


class BySegmentsPPTXView(BySegmentsMixin, ReportingDashboardPPTXView):
    """
    Download BySegments as a .pptx presentation
    """
    basename = 'by-segments'


class GHGEmissionsRatePPTXView(GHGEmissionsRateMixin,
                               ReportingDashboardPPTXView):
    """
    Download GHG emissions rate as a .pptx presentation
    """
    basename = 'ghg-emissions-rate'


class GHGEmissionsAmountPPTXView(GHGEmissionsAmountMixin,
                                 ReportingDashboardPPTXView):
    """
    Download GHG emissions amount as a .pptx presentation
    """
    basename = 'ghg-emissions-amount'
