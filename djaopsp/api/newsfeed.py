# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.

import logging
from collections import OrderedDict

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import models
from pages.api.newsfeed import NewsFeedListAPIView as NewsfeedBaseAPIView
from survey.helpers import datetime_or_now
from survey.models import PortfolioDoubleOptIn
from survey.utils import get_account_model

from ..api.serializers import UserNewsSerializer
from ..compat import reverse, gettext_lazy as _
from ..mixins import VisibilityMixin
from ..utils import (get_campaign_candidates, get_latest_active_assessments,
    get_latest_completed_assessment)


LOGGER = logging.getLogger(__name__)


class NewsfeedAPIView(VisibilityMixin, NewsfeedBaseAPIView):
    """
    Lists feed elements

    **Tags: content

    **Example

    .. code-block:: http

        GET /api/content/supplier-1/newsfeed HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 2,
          "next": null,
          "previous": null,
          "results": [
            {
              "slug": "sustainability",
              "picture": null,
              "title": "ESG/Environmental practices",
              "reading_time": null,
              "account": "supplier-1",
              "extra": null,
              "upvote": null,
              "follow": null,
              "last_read_at": null,
              "nb_comments_since_last_read": null,
              "descr": "Assess your organization's environmental, social\
 and governance policies against best practices.",
              "grantees": [
                {
                  "created_at": "2026-01-01T00:00:00+00:00",
                  "grantee": "energy-utility"
                }
              ],
              "ends_at": "2026-12-31T00:00:00+00:00",
              "last_completed_at": "2026-01-31T00:17:49.082061Z",
              "respondents": [
                "steve"
              ],
              "share_url": "https://tspproject.org/app/supplier-1/share/\
1812dff6ab1544958a6bde472431a1d3/",
              "update_url": "https://tspproject.org/app/supplier-1/assess/"
            },
            {
              "slug": "adjust-air-fuel-ratio",
              "picture": null,
              "title": "Adjust air/fuel ratio",
              "content_format": "MD",
              "text_updated_at": "2026-01-01T00:00:00Z",
              "reading_time": "00:00:00",
              "lang": "en-us",
              "account": "djaopsp",
              "extra": {
                "searchable": true,
                "visibility": [
                  "public"
                ],
                "tags": [
                  "Energy & Emissions"
                ]
              },
              "nb_upvotes": 1,
              "nb_followers": 1,
              "upvote": true,
              "follow": 1,
              "last_read_at": 0,
              "nb_comments_since_last_read": 0,
                "descr": "<p>Some manufacturing processes may involve heating\
 operations.<a href='/app/info/adjust-air-fuel-ratio/'>... read more</a></p>"
              }
          ]
        }
    """
    account_url_kwarg = 'profile'
    serializer_class = UserNewsSerializer
    URL_PATH_SEP = "/"

    @property
    def user(self):
        return self.request.user

    @property
    def accounts(self):
        account_model = get_account_model()
        try:
            account = account_model.objects.get(
                slug=self.kwargs.get(self.account_url_kwarg))
            return [account]
        except account_model.DoesNotExist:
            pass
        return account_model.objects.filter(slug__in=self.accessible_profiles)

    @staticmethod
    def _get_pending_request_initial_data(campaign, account=None):
        initial_data = {
            'slug': campaign.slug,
            'title': campaign.title,
            'descr': campaign.description,
            'ends_at': None,
            'last_completed_at': None,
            'share_url': None,
            'update_url': reverse('getstarted_campaign', args=(campaign,)),
            'grantees': [],
            'respondents': []}
        if account:
            initial_data.update({
                'account': account,
                'update_url': reverse('profile_getstarted_campaign', args=(
                    account, campaign)),
            })
        return initial_data


    def get_pending_requests(self, at_time=None):
        if not at_time:
            at_time = datetime_or_now()

        assessments = []
        for account in self.accounts:
            by_campaigns = OrderedDict()
            # XXX `pending_for` will also include grants pending acceptance.
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
                        by_campaigns[optin.campaign] = \
                            self._get_pending_request_initial_data(
                                campaign, account=account)
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
                    by_campaigns[sample.campaign] = \
                        self._get_pending_request_initial_data(
                                sample.campaign, account=account)
                # We would use `reverse('assess_index', args=(account, sample))`
                # if the template was not written to always make a POST request.
                by_campaigns[sample.campaign]['update_url'] = reverse(
                    'assess_redirect', args=(account,))
                latest_completed = get_latest_completed_assessment(account,
                    campaign=sample.campaign)
                if latest_completed:
                    by_campaigns[sample.campaign]['last_completed_at'] = \
                        latest_completed.created_at
                    #if relativedelta(
                    #        at_time, latest_completed.created_at).months < 6:
                    by_campaigns[sample.campaign]['share_url'] = reverse(
                            'share', args=(account, latest_completed))
                    by_campaigns[sample.campaign]['respondents'] = \
                        get_user_model().objects.filter(
                            answer__sample=sample).distinct()

            assessments += by_campaigns.values()

        if not assessments:
            # THere are no pending requests, we will add candidates
            # so default questionnaires shows up.
            account = None
            if len(self.accounts) == 1:
                account = next(iter(self.accounts))
            by_campaigns = OrderedDict()
            campaign_candidates = get_campaign_candidates(
                    accounts=self.accessible_profiles,
                    tags=(set(['public']) | {plan['slug']
                        for plan in self.get_accessible_plans(self.request)
            }))
            for campaign in campaign_candidates:
                if not campaign in by_campaigns:
                    by_campaigns[campaign] = \
                        self._get_pending_request_initial_data(
                            campaign, account=account)
            assessments += by_campaigns.values()

        return assessments


    def get_serializer_context(self):
        context = super(NewsfeedAPIView, self).get_serializer_context()
        context.update({'prefix': self.URL_PATH_SEP})
        return context

    def get_queryset(self):
        return list(self.get_pending_requests()) + list(
            self.get_updated_elements())
