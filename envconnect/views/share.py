# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from __future__ import unicode_literals

import logging, json

from django.contrib import messages
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.views.generic.base import TemplateView
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_prefixed)
from deployutils.helpers import update_context_urls
from survey.models import Answer, Sample

from ..compat import reverse
from ..mixins import ReportMixin
from ..suppliers import get_supplier_managers


LOGGER = logging.getLogger(__name__)


class ShareView(ReportMixin, TemplateView):

    template_name = 'envconnect/share/index.html'
    breadcrumb_url = 'share'

    def get_context_data(self, **kwargs):
        context = super(ShareView, self).get_context_data(**kwargs)
        from_root, trail = self.breadcrumbs
        # Find supplier managers subscribed to this profile
        # to share scorecard with.
        is_account_manager = self.manages(self.account)
        if is_account_manager:
            context.update({
                'is_account_manager': is_account_manager})
        context.update({
            'supplier_managers': json.dumps(
                get_supplier_managers(self.account))})
        update_context_urls(context, {
            'api_scorecard_share': reverse('api_scorecard_share',
                args=(context['organization'], from_root)),
            'api_organizations': site_prefixed("/api/profile/"),
            'api_viewers': site_prefixed(
                "/api/profile/%s/roles/viewers/" % self.account),
        })
        breadcrumbs = context.get('breadcrumbs', [])
        if breadcrumbs:
            context.update({'segment_title': breadcrumbs[0][0].title})
        context.update({'sample': self.sample})
        return context

    def get(self, request, *args, **kwargs):
        if not self.sample.is_frozen:
            # Matching code in ShareScorecardAPIView
            segment_url, segment_prefix, segment_element = self.segment

            last_activity_at = Answer.objects.filter(
                sample=self.assessment_sample,#XXX self.get_included_samples() ?
                question__path__startswith=segment_prefix).aggregate(
                    last_activity_at=Max('created_at')).get(
                    'last_activity_at', None)
            last_scored_assessment = Sample.objects.filter(
                is_frozen=True,
                extra__isnull=True,
                survey=self.survey,
                account=self.account).order_by('-created_at').first()

            if (self.nb_required_answers < self.nb_required_questions
                or (not last_scored_assessment or
                    last_scored_assessment.created_at < last_activity_at)):
                messages.warning(self.request,
                    "You must mark an assessment as complete before"\
                    " you share it with customers, clients and/or investors.")
                return HttpResponseRedirect(reverse('complete_organization',
                    args=(self.account, self.sample, self.kwargs.get('path'))))

        return super(ShareView, self).get(request, *args, **kwargs)
