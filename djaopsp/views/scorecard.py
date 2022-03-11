# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.helpers import update_context_urls
from django.db import transaction
from django.views.generic import RedirectView, TemplateView
from survey.models import Sample
from survey.utils import get_account_model

from ..compat import reverse
from ..mixins import (AccountMixin, ReportMixin, get_campaigns_available,
    get_latest_assessment_sample, get_segments_available)


LOGGER = logging.getLogger(__name__)


class ScorecardView(ReportMixin, TemplateView):
    """
    Profile scorecard page
    """
    template_name = 'app/scorecard/index.html'
    URL_PATH_SEP = '/'

    def get_template_names(self):
        candidates = ['app/scorecard/%s.html' % self.sample.campaign]
        candidates += super(ScorecardView, self).get_template_names()
        return candidates

    def get_context_data(self, **kwargs):
        context = super(ScorecardView, self).get_context_data(**kwargs)
        segments_available = []
        for segment in get_segments_available(self.sample.campaign):
            segment_path = segment.get('path', "")
            if segment_path and segment_path.startswith('/rfx-core'):
                update_context_urls(context, {
                    'assess_practices': reverse('assess_practices',
                        args=(self.account, self.sample,
                        segment_path.lstrip(self.URL_PATH_SEP))),
                })
            else:
                segments_available += [segment]
        context.update({
            'segments_available': segments_available
        })
        update_context_urls(context, {
            'survey_api_sample_answers': reverse('survey_api_sample_answers',
                args=(self.account, self.sample))
        })
        return context


class ScorecardRedirectView(AccountMixin, RedirectView):
    """
    Redirects to the latest scorecard page
    """

    def get_redirect_url(self, *args, **kwargs):
        lastest_scorecard = get_latest_assessment_sample(self.account)
        if not lastest_scorecard:
            # We don't have a Sample yet. Let's create one while also
            # considering that self.account might not be a model
            # in the database yet.
            account_model = get_account_model()
            with transaction.atomic():
                #pylint:disable=unused-variable
                if isinstance(self.account, account_model):
                    account = self.account
                else:
                    account, unused = account_model.objects.get_or_create(
                        slug=str(self.account))
                # XXX Whenever Sample.campaign_id is null, the survey APIs
                # will not behave properly.
                campaigns = get_campaigns_available(account)
                if campaigns.count() > 1:
                    raise NotImplementedError("XXX More than one Campagin")
                default_campaign = campaigns.get()
                lastest_scorecard = Sample.objects.create(
                    account=account, campaign=default_campaign)
        return reverse('scorecard', args=(self.account, lastest_scorecard))

class ScorecardHistoryView(TemplateView):
    """
    Profile scorecard history page
    """
    template_name = 'app/scorecard/history.html'
