# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

from __future__ import unicode_literals

import logging

from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from django.views.generic.base import TemplateResponseMixin, RedirectView
from django.http import Http404
from survey.models import Sample
from survey.views.portfolios import PortfoliosView

from ..compat import reverse
from ..mixins import ReportMixin, AccountMixin
from ..utils import (get_latest_active_assessments,
    get_latest_completed_assessment)


LOGGER = logging.getLogger(__name__)


class ShareView(ReportMixin, PortfoliosView):
    """
    Shows page at /app/<profile>/share/<slug:sample>/
    """
    template_name = 'app/share/index.html'

    def get_sample(self, url_kwarg=None):
        """
        Returns the ``Sample`` object associated with this URL.
        """
        # The `ShareView` will present portfolio requests. We don't want
        # to present those when the profile is not the owner of the sample.
        if not url_kwarg:
            url_kwarg = self.sample_url_kwarg
        sample_slug = self.kwargs.get(url_kwarg)
        if not sample_slug:
            raise Http404("Cannot find Sample(slug='%s')" % sample_slug)
        try:
            sample = Sample.objects.filter(
                account=self.account, slug=sample_slug).select_related(
                'campaign').distinct().get()
        except Sample.DoesNotExist:
            raise Http404("Cannot find Sample(slug='%s')" % sample_slug)
        return sample

    def get_reverse_kwargs(self):
        """
        List of kwargs taken from the url that needs to be passed through
        to ``get_success_url``.
        """
        if self.account_url_kwarg:
            return [self.account_url_kwarg]
        return []

    def get_context_data(self, **kwargs):
        context = super(ShareView, self).get_context_data(**kwargs)
        latest_completed_assessment = get_latest_completed_assessment(
            self.sample.account, campaign=self.sample.campaign)
        context.update({
            'sample': self.sample,
            'campaign': self.sample.campaign,
            'latest_completed_assessment': latest_completed_assessment,
        })
        update_context_urls(context, {
            'api_organizations': site_url("/api/accounts/profiles"),
            'api_account_candidates': site_url("/api/accounts/profiles"),
            'api_requests': reverse('survey_api_portfolios_received',
                    args=(self.account,)),
        })
        if latest_completed_assessment:
            # XXX We expect a single active assessment for suppliers.
            # When used with a `verifier_notes` sample, this will return
            # all active verifier notes.
            active_assessment = get_latest_active_assessments(
                self.sample.account, campaign=self.sample.campaign).get()
            update_context_urls(context, {
                'update_assessment': reverse('scorecard',
                    args=(active_assessment.account, active_assessment))
            })
        return context


class ShareRedirectView(AccountMixin, TemplateResponseMixin, RedirectView):
    """
    Redirects to a page where a user can share the latest response
    to a campaign.
    """
    template_name = 'app/share/redirects.html'
    breadcrumb_url = 'share'

    def get_redirect_url(self, *args, **kwargs):
        return reverse(self.breadcrumb_url, kwargs=kwargs)

    def get(self, request, *args, **kwargs):
        candidates = get_latest_active_assessments(self.account)

        redirects = []
        for sample in candidates:
            # We insured that all candidates are the prefixed
            # content node at this point.
            kwargs.update({'sample': sample})
            url = self.get_redirect_url(*args, **kwargs)
            print_name = sample.campaign.title
            redirects += [(url, print_name)]

        if len(redirects) > 1 or len(self.campaign_candidates) > 1:
            context = self.get_context_data(**kwargs)
            context.update({
                'redirects': redirects,
                'campaigns': self.campaign_candidates
            })
            return self.render_to_response(context)

        if not redirects:
            if not self.campaign_candidates:
                raise Http404(
                    "No campaigns available for %(account)s" % {
                    'account': self.account})
        return super(ShareRedirectView, self).get(request, *args, **kwargs)
