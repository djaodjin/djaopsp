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

from ..compat import reverse, NoReverseMatch
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
        candidates = []
        organization = kwargs.get('organization')
        path = kwargs.get('path')
        if path:
            parts = path.split('/')
            for part in parts:
                if part and part.startswith('sustainability-'):
                    candidates += [get_object_or_404(PageElement, slug=part)]
                    break
        elif self.sample:
            for element in PageElement.objects.filter(tag__contains='industry'):
                root_prefix = '/%s/sustainability-%s' % (
                    element.slug, element.slug)
                if Consumption.objects.filter(
                        answer__sample=self.sample,
                        path__contains=root_prefix).exists():
                    candidates += [element]
        if not candidates:
            # On user login, registration and activation,
            # we will end-up here.
            if not organization in self.accessibles(
                    roles=['manager', 'contributor']):
                messages.warning(self.request,
                    VIEWER_SELF_ASSESSMENT_NOT_YET_STARTED % {
                        'organization': organization})
            return HttpResponseRedirect(reverse('homepage')) # XXX app page `organization_app`

        kwargs.update({'sample': self.sample})
        redirects = []
        for element in candidates:
            if element.slug.startswith('sustainability-'):
                root_prefix = '/%s' % element.slug
            else:
                root_prefix = '/sustainability-%s' % element.slug
            kwargs.update({'path': root_prefix})
            url = self.get_redirect_url(*args, **kwargs)
            print_name = element.title
            redirects += [(url, print_name)]

        if len(redirects) > 1:
            context = self.get_context_data(**kwargs)
            context.update({'redirects': redirects})
            return self.render_to_response(context)
        return super(LastCompletedRedirectView, self).get(
            request, *args, **kwargs)
