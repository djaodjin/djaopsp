# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging, json

from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from survey.models import Matrix, Response
from survey.views.matrix import MatrixDetailView

from ..api.benchmark import BenchmarkMixin
from ..models import Consumption

LOGGER = logging.getLogger(__name__)


class BenchmarkBaseView(BenchmarkMixin, TemplateView):

    template_name = 'envconnect/benchmark.html'
    breadcrumb_url = 'benchmark'

    @property
    def survey(self):
        if not hasattr(self, '_survey'):
            self._survey = self.sample.survey
        return self._survey

    def get_context_data(self, *args, **kwargs):
        #pylint:disable=too-many-locals
        context = super(BenchmarkBaseView, self).get_context_data(
            *args, **kwargs)
        if len(context['breadcrumbs']) > 0:
            root, _, _ = context['breadcrumbs'][-1]
            root = self._build_tree(root, context['from_root'], nocuts=True)
            # Flatten icons and practices (i.e. Energy Efficiency) to produce
            # the list of charts.
            charts, complete = self.get_charts(root[1])
            context.update({
                'self_assessment_complete': complete,
                'charts': charts,
                'root': self._cut_tree(root),
                'entries': json.dumps(self.to_representation(root))
            })
            self.root = root # XXX Hack for self-assessment to present results
        return context


class BenchmarkView(BenchmarkBaseView):

    template_name = 'envconnect/benchmark.html'
    breadcrumb_url = 'benchmark'

    def get(self, request, *args, **kwargs):
        from_root, _ = self.breadcrumbs
        if not from_root:
            # We don't have a ``path`` here so we will try to determine
            # the most likely candidate (see ``AccountRedirectView.get``).
            org_slug = self.kwargs.get('organization')
            queryset = Response.objects.filter(
                account__slug=org_slug,
                survey__title=self.report_title)
            response = queryset.first()
            if response:
                queryset = Consumption.objects.filter(
                    answer__response=response).order_by('-path')
                candidate = queryset.first()
                if candidate and candidate.path:
                    return HttpResponseRedirect(
                        reverse('%s_organization' % self.breadcrumb_url,
                          args=(org_slug, '/' + candidate.path.split('/')[1])))
            return HttpResponseRedirect(reverse('homepage'))
        try:
            self.sample
        except Http404:
            if not self.manages('envconnect'):
                messages.warning(request,
                    "You need to complete the self-assessment before"\
                    " moving on to benchmarks.")
                return HttpResponseRedirect(reverse(
                    'report', kwargs={'path': self.kwargs.get('path')}))
        return super(BenchmarkView, self).get(request, *args, **kwargs)


class ScoreCardView(BenchmarkView):
    """
    Shows the scorecard of an organization, accessible through
    the "My TSP" menu.
    """
    template_name = 'envconnect/scorecard.html'
    breadcrumb_url = 'scorecard'



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
        if len(context['breadcrumbs']) > 0:
            root, _, _ = context['breadcrumbs'][-1]
            root = self._build_tree(root, context['from_root'])
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
