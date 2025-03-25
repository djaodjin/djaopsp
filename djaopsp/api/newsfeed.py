# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.

import logging
from collections import OrderedDict

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import models
from rest_framework import generics

from survey.helpers import datetime_or_now
from survey.models import PortfolioDoubleOptIn

from ..api.serializers import PendingRequestsFeedSerializer
from ..compat import reverse, gettext_lazy as _
from ..mixins import VisibilityMixin
from ..utils import (get_campaign_candidates, get_latest_active_assessments,
    get_latest_completed_assessment)


LOGGER = logging.getLogger(__name__)


class NewsfeedAPIView(VisibilityMixin, generics.ListAPIView):
    """
    """
    account_url_kwarg = 'profile'
    serializer_class = PendingRequestsFeedSerializer

    @property
    def user(self):
        return self.request.user

    @property
    def accounts(self):
        return self.accessible_profiles

    def get_pending_requests(self, at_time=None):
        if not at_time:
            at_time = datetime_or_now()

        # XXX `pending_for` will also include grants pending acceptance.
        assessments = []
        for account in self.accounts:
            by_campaigns = OrderedDict()
            requests = PortfolioDoubleOptIn.objects.pending_for(
                account, at_time=at_time).exclude(
                    models.Q(grantee__slug=account) &
                    models.Q(state=PortfolioDoubleOptIn.OPTIN_GRANT_INITIATED)
            ).order_by('campaign__title')
            for optin in requests:
                campaign = optin.campaign
                if campaign:
                    # XXX It is possible the request isn't limited
                    #     to a single campaign.
                    if not campaign in by_campaigns:
                        by_campaigns[optin.campaign] = {
                            'account': account,
                            'campaign': campaign,
                            'ends_at': None,
                            'last_completed_at': None,
                            'share_url': None,
                            'update_url': None,
                            'grantees': [],
                            'respondents': []}
                    if optin.ends_at:
                        campaign_ends_at = by_campaigns[campaign]['ends_at']
                        by_campaigns[campaign]['ends_at'] = (optin.ends_at
                            if not campaign_ends_at
                            else min(datetime_or_now(campaign_ends_at),
                                optin.ends_at)).isoformat()
                    by_campaigns[campaign]['grantees'] += [{
                        'created_at': optin.created_at.isoformat(),
                        'grantee': optin.grantee.slug
                    }]

            candidates = get_latest_active_assessments(account).exclude(
                campaign__slug__endswith='-verified') # XXX Ad-hoc exclude
                                               # of verification campaigns.
            for sample in candidates:
                if not sample.campaign in by_campaigns:
                    by_campaigns[sample.campaign] = {
                        'account': account,
                        'campaign': sample.campaign,
                        'ends_at': None,
                        'last_completed_at': None,
                        'share_url': None,
                        'update_url': None,
                        'grantees': [],
                        'respondents': []}
                by_campaigns[sample.campaign]['update_url'] = reverse(
                    'assess_index', args=(account, sample))
                latest_completed = get_latest_completed_assessment(account,
                    campaign=sample.campaign)
                if latest_completed:
                    by_campaigns[sample.campaign]['last_completed_at'] = \
                        latest_completed.created_at
                    if relativedelta(
                            at_time, latest_completed.created_at).months < 6:
                        by_campaigns[sample.campaign]['share_url'] = reverse(
                            'share', args=(account, latest_completed))
                    by_campaigns[sample.campaign]['respondents'] = \
                        get_user_model().objects.filter(
                            answer__sample=sample).distinct()

            if False:
                campaign_candidates = get_campaign_candidates(
                        accounts=self.accessible_profiles,
                        tags=(set(['public']) | {plan['slug']
                            for plan in self.get_accessible_plans(self.request)
                }))
                for campaign in campaign_candidates:
                    if not campaign in by_campaigns:
                        by_campaigns[campaign] = {
                            'account': account,
                            'campaign': campaign,
                            'ends_at': None,
                            'last_completed_at': None,
                            'share_url': None,
                            'update_url': None,
                            'grantees': [],
                            'respondents': []}
            assessments += by_campaigns.values()

        return assessments

    def get_queryset(self):
        return list(self.get_pending_requests())
