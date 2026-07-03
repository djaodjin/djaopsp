# Copyright (c) 2026, DjaoDjin inc.
# see LICENSE.

import logging
from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.db import models
from rest_framework.settings import api_settings
from rest_framework.generics import get_object_or_404
from pages.api.newsfeed import NewsFeedListAPIView as NewsfeedBaseAPIView
from survey.helpers import datetime_or_now
from survey.models import Campaign, PortfolioDoubleOptIn
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
    campaign_url_kwarg = 'campaign'
    search_param = api_settings.SEARCH_PARAM
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

    ### `get_query_param` might be better in pages
    def get_query_param(self, key, default_value=None):
        try:
            return self.request.query_params.get(key, default_value)
        except AttributeError:
            pass
        return self.request.GET.get(key, default_value)

    def get_pending_requests(self, show_all=False, at_time=None):
        #pylint:disable=too-many-locals
        if not at_time:
            at_time = datetime_or_now()

        assessments = []
        campaign_slug = self.kwargs.get(self.campaign_url_kwarg)
        campaign_filtered = (get_object_or_404(
            Campaign.objects.all(), slug=campaign_slug)
            if campaign_slug else None)
        for account in self.accounts:
            by_campaigns = OrderedDict()
            # XXX `pending_for` will also include grants pending acceptance.
            requests = PortfolioDoubleOptIn.objects.pending_for(
                account, at_time=at_time, campaign=campaign_filtered).exclude(
                    models.Q(grantee__slug=account) &
                    models.Q(state=PortfolioDoubleOptIn.OPTIN_GRANT_INITIATED)
            ).order_by('campaign__pk')
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

            # We asume it is a work-in-progress worthy to show in the newsfeed
            # when `updated_at > created_at`. Otherwise the user will have
            # to go through the "History" page to update the response.
            candidates = get_latest_active_assessments(
                account, campaign=campaign_filtered).exclude(
                campaign__slug__endswith='-verified') # XXX Ad-hoc exclude
                                               # of verification campaigns.

            if not show_all:
                # Show responses for which we have an active request
                # or we are currently editing.
                candidates = candidates.filter(
                    models.Q(campaign__in=by_campaigns) |
                    models.Q(updated_at__gt=models.F('created_at')))

            for sample in candidates:
                campaign = sample.campaign
                if not campaign in by_campaigns:
                    by_campaigns[campaign] = \
                        self._get_pending_request_initial_data(
                                campaign, account=account)
                # We would use `reverse('assess_index', args=(account, sample))`
                # if the template was not written to always make a POST request.
                by_campaigns[campaign]['update_url'] = reverse(
                    'assess_redirect', args=(account,))
                latest_completed = get_latest_completed_assessment(account,
                    campaign=campaign)
                if latest_completed:
                    by_campaigns[campaign]['last_completed_at'] = \
                        latest_completed.created_at
                    if latest_completed.created_at > campaign.updated_at:
                        # The profile is forced to update the response when
                        # the questionnaire was last completed before the
                        # questionnaire was updated.
                        by_campaigns[campaign]['share_url'] = reverse(
                            'share', args=(account, latest_completed))
                    by_campaigns[campaign]['respondents'] = \
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
            if campaign_filtered:
                campaign_candidates = [campaign_filtered]
            else:
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
                # We would use `reverse('assess_index', args=(account, sample))`
                # if the template was not written to always make a POST request.
                by_campaigns[campaign]['update_url'] = reverse(
                    'assess_redirect', args=(account,))
                latest_completed = get_latest_completed_assessment(account,
                    campaign=campaign)
                if latest_completed:
                    by_campaigns[campaign]['last_completed_at'] = \
                        latest_completed.created_at
                    if latest_completed.created_at > campaign.updated_at:
                        # The profile is forced to update the response when
                        # the questionnaire was last completed before the
                        # questionnaire was updated.
                        by_campaigns[campaign]['share_url'] = reverse(
                            'share', args=(account, latest_completed))
                    by_campaigns[campaign]['respondents'] = \
                        get_user_model().objects.filter(
                            answer__sample=latest_completed).distinct()

            assessments += by_campaigns.values()

        return assessments


    def get_serializer_context(self):
        context = super(NewsfeedAPIView, self).get_serializer_context()
        context.update({'prefix': self.URL_PATH_SEP})
        return context

    def get_queryset(self):
        search_term = self.get_query_param(self.search_param)
        show_all = bool(search_term == 'requests')
        results = list(self.get_pending_requests(show_all=show_all))
        if search_term != 'requests':
            results += list(self.get_updated_elements())
        return results
