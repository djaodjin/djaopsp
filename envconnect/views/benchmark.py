# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging, json

from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.base import (RedirectView, TemplateView,
    TemplateResponseMixin)
from django.utils import six
from extended_templates.backends.pdf import PdfTemplateResponse
from pages.models import PageElement
from survey.models import Matrix
from survey.views.matrix import MatrixDetailView

from ..api.benchmark import BenchmarkMixin
from ..mixins import ReportMixin
from ..models import Consumption


LOGGER = logging.getLogger(__name__)


class SelfAssessmentRedirectMixin(object):

    def get_assessment_redirect_url(self, *args, **kwargs):
        #pylint:disable=unused-argument
        path = kwargs.get('path')
        if not isinstance(path, six.string_types):
            path = ""
        messages.warning(self.request,
            "You need to complete a self-assessment before"\
            " moving on to benchmarks.")
        return HttpResponseRedirect(reverse('report_organization',
            kwargs={'organization': kwargs.get('organization'), 'path': path}))

    @staticmethod
    def get_context_data(**kwargs):
        #pylint:disable=unused-argument
        return {}


class ScoreCardRedirectView(ReportMixin, SelfAssessmentRedirectMixin,
                            TemplateResponseMixin, RedirectView):

    pattern_name = 'benchmark_organization'
    template_name = 'envconnect/scorecard/index.html'

    def get(self, request, *args, **kwargs):
        if not self.sample:
            return self.get_assessment_redirect_url(*args, **kwargs)

        candidates = []
        for element in PageElement.objects.get_roots().order_by('title'):
            root_prefix = '/%s/' % element.slug
            if Consumption.objects.filter(answer__response=self.sample,
                path__startswith=root_prefix).exists():
                candidates += [element]
        if not candidates:
            return self.get_assessment_redirect_url(*args, **kwargs)

        redirects = []
        for element in candidates:
            root_prefix = '/sustainability-%s' % element.slug
            kwargs.update({'path': root_prefix})
            url = super(ScoreCardRedirectView, self).get_redirect_url(
                *args, **kwargs)
            print_name = element.title
            redirects += [(url, print_name)]

        if len(redirects) > 1:
            context = super(ScoreCardRedirectView, self).get_context_data(
                *args, **kwargs)
            context.update({'redirects': redirects})
            return self.render_to_response(context)
        return super(ScoreCardRedirectView, self).get(request, *args, **kwargs)


class BenchmarkBaseView(BenchmarkMixin, SelfAssessmentRedirectMixin,
                        TemplateView):

    template_name = 'envconnect/benchmark.html'
    breadcrumb_url = 'benchmark'

    def get_context_data(self, *args, **kwargs):
        #pylint:disable=too-many-locals
        context = super(BenchmarkBaseView, self).get_context_data(
            *args, **kwargs)
        from_root, trail = self.breadcrumbs
        root = self._build_tree(trail[-1][0], from_root, nocuts=True)
        # Flatten icons and practices (i.e. Energy Efficiency) to produce
        # the list of charts.
        charts, complete = self.get_charts(root[1])
        context.update({
            'self_assessment_complete': complete,
            'charts': charts,
            'root': self._cut_tree(root),
            'entries': json.dumps(self.to_representation(root)),
            # XXX move to urls when we are sure how it interacts
            # with envconnect/base.html
            'api_account_benchmark': reverse(
                'api_benchmark', args=(context['organization'], from_root))
        })
        self.root = root # XXX Hack for self-assessment to present results
        return context


class BenchmarkView(BenchmarkBaseView):

    template_name = 'envconnect/benchmark.html'
    breadcrumb_url = 'benchmark'

    def get(self, request, *args, **kwargs):
        if not self.sample:
            return self.get_assessment_redirect_url(*args, **kwargs)
        return super(BenchmarkView, self).get(request, *args, **kwargs)


class ScoreCardView(BenchmarkView):
    """
    Shows the scorecard of an organization, accessible through
    the "My TSP" menu.
    """
    template_name = 'envconnect/scorecard.html'
    breadcrumb_url = 'scorecard'


class ScoreCardDownloadView(ScoreCardView):
    """
    Shows the scorecard of an organization, accessible through
    the "My TSP" menu.
    """

    def get(self, request, *args, **kwargs):
        return PdfTemplateResponse(request, self.template_name,
            self.get_context_data(*args, **kwargs))


class PortfoliosDetailView(BenchmarkMixin, MatrixDetailView):

    matrix_url_kwarg = 'path'

    def get_available_matrices(self):
        return Matrix.objects.filter(account=self.account)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        candidate = self.kwargs.get(self.matrix_url_kwarg)
        if candidate.startswith('/'):
            candidate = candidate[1:]
        return get_object_or_404(queryset, slug=candidate)

    def get_context_data(self, *args, **kwargs):
        context = super(PortfoliosDetailView, self).get_context_data(
            *args, **kwargs)
        context.update({'available_matrices': self.get_available_matrices()})
        from_root, trail = self.breadcrumbs
        root = self._build_tree(trail[-1][0], from_root)
        charts, _ = self.get_charts(root[1])
        url_kwargs = self.get_url_kwargs()
        url_kwargs.update({'matrix': self.object})
        for chart in charts:
            matrix_slug = '/'.join([str(self.object), chart['slug']])
            url_kwargs.update({'matrix': matrix_slug})
            api_urls = {'matrix_api': reverse(
                'matrix_api', kwargs=url_kwargs)}
            chart.update({'urls': api_urls})
        context.update({'charts': charts})
        return context

