# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.apps.django.redirects import (
    AccountRedirectView as AccountRedirectBaseView)
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.base import (RedirectView,
    ContextMixin, TemplateResponseMixin)
from pages.models import PageElement
from survey.models import Matrix

from ..compat import reverse
from ..mixins import ReportMixin
from ..models import Consumption


LOGGER = logging.getLogger(__name__)

# XXX It isn't clear why we need `ReportMixin` below.
class AccountRedirectView(ReportMixin, AccountRedirectBaseView):

    redirect_roles = ['manager', 'contributor']

    def get_redirect_roles(self, request):
        if self.pattern_name in ['scorecard_organization_redirect']:
            return self.redirect_roles + ['viewer']
        return super(AccountRedirectView, self).get_redirect_roles(request)


class MyTSPRedirectView(AccountRedirectView):

    def get(self, request, *args, **kwargs):
        candidates = Matrix.objects.filter(
            account__slug__in=self.accessibles(roles=self.redirect_roles))
        if not candidates:
            return self.response_class(
                request=self.request,
                template='envconnect/reporting/locked.html',
                context={'request': self.request},
                using=self.template_engine,
                content_type=self.content_type)
        return super(MyTSPRedirectView, self).get(request, *args, **kwargs)


VIEWER_SELF_ASSESSMENT_NOT_YET_STARTED = \
    "%(organization)s has not yet started to complete"\
    " their assessment. You will be able able to see"\
    " %(organization)s as soon as they do."


class LastCompletedRedirectView(ReportMixin, TemplateResponseMixin,
                                ContextMixin, RedirectView):
    """
    On login, by default the user will be redirected to `/app/` which in turn
    will redirect to `/app/:organization/scorecard/$`.

    If *organization* has started an assessment then we have candidates
    to redirect to (i.e. /app/:organization/scorecard/:path).
    """
    template_name = 'envconnect/scorecard/index.html'

    @property
    def sample(self):
        return self.assessment_sample

    def get(self, request, *args, **kwargs):
        #pylint:disable=too-many-locals
        candidates = []
        organization = kwargs.get('organization')
        if self.sample:
            if kwargs.get('path'):
                segment_url, segment_prefix, segment_element = self.segment
                candidates += [segment_element]
                # XXX We need a PageElement for the root here.
                # Top level are tagged industry (not the sustainability one).
            else:
                # XXX We need a PageElement with slug/path and title.
                # XXX The candidates must be derived based on the code
                # in CampaignList.
                for element in self.get_segments():
                    segment_prefix = element['path'] # XXX element['(url_)path']
                    # different from element['prefix'].
                    if Consumption.objects.filter(
                            answer__sample=self.sample,
                            path__contains=segment_prefix).exists():
                        segment_slug = segment_prefix.split('/')[-1]
                        candidates += [
                            get_object_or_404(PageElement, slug=segment_slug)]
        if not candidates:
            # On user login, registration and activation,
            # we will end-up here.
            if not organization in self.accessibles(
                    roles=['manager', 'contributor']):
                messages.warning(self.request,
                    VIEWER_SELF_ASSESSMENT_NOT_YET_STARTED % {
                        'organization': organization})
            return HttpResponseRedirect(
                reverse('organization_app', args=(organization,)))

        kwargs.update({'sample': self.sample})
        redirects = []
        for element in candidates:
            # We insured that all candidates are the sustainability prefixed
            # content node at this point.
            kwargs.update({'path': '/%s' % element.slug})
            url = self.get_redirect_url(*args, **kwargs)
            print_name = element.title
            redirects += [(url, print_name)]

        if len(redirects) > 1:
            context = self.get_context_data(**kwargs)
            context.update({'redirects': redirects})
            return self.render_to_response(context)
        return super(LastCompletedRedirectView, self).get(
            request, *args, **kwargs)
