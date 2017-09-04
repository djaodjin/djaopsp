# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from __future__ import unicode_literals

import io, logging, json, re, subprocess, tempfile

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.views.generic.base import (RedirectView, TemplateView,
    ContextMixin, TemplateResponseMixin)
from django.utils import six
from deployutils.helpers import datetime_or_now
from extended_templates.backends.pdf import PdfTemplateResponse
from pages.models import PageElement
from survey.models import Matrix
from survey.views.matrix import MatrixDetailView

from ..api.benchmark import BenchmarkMixin, BenchmarkAPIView
from ..mixins import ReportMixin
from ..models import Consumption


LOGGER = logging.getLogger(__name__)

VIEWER_SELF_ASSESSMENT_NOT_YET_STARTED = \
    "%(organization)s has not yet started to complete"\
    " their self-assessment. You will be able able to see"\
    " %(organization)s as soon as they do."


class ScoreCardRedirectView(ReportMixin, TemplateResponseMixin,
                            ContextMixin, RedirectView):
    """
    On login, by default the user will be redirected to `/app/` which in turn
    will redirect to `/app/:organization/scorecard/$`.

    If *organization* has started a self-assessment then we have candidates
    to redirect to (i.e. /app/:organization/scorecard/:path).
    """

    template_name = 'envconnect/scorecard/index.html'

    def get_redirect_url(self, *args, **kwargs):
        if self.kwargs.get('organization') in self.accessibles(
                ['manager', 'contributor']):
            # If the user has a more than a `viewer` role on the organization,
            # we force the redirect to the benchmark page such that
            # the contextual menu with self-assessment, etc. appears.
            try:
                return reverse('benchmark_organization',
                    args=args, kwargs=kwargs)
            except NoReverseMatch:
                return None
        return super(ScoreCardRedirectView, self).get_redirect_url(
            *args, **kwargs)

    def get(self, request, *args, **kwargs):
        candidates = []
        organization = kwargs.get('organization')
        if self.sample:
            for element in PageElement.objects.get_roots().order_by('title'):
                root_prefix = '/%s/sustainability-%s' % (
                    element.slug, element.slug)
                if Consumption.objects.filter(answer__response=self.sample,
                    path__startswith=root_prefix).exists():
                    candidates += [element]
        if not candidates:
            # On user login, registration and activation,
            # we will end-up here.
            if not organization in self.accessibles(
                    roles=['manager', 'contributor']):
                messages.warning(self.request,
                    VIEWER_SELF_ASSESSMENT_NOT_YET_STARTED % {
                        'organization': organization})
            return HttpResponseRedirect(reverse('homepage'))

        redirects = []
        for element in candidates:
            root_prefix = '/sustainability-%s' % element.slug
            kwargs.update({'path': root_prefix})
            url = self.get_redirect_url(*args, **kwargs)
            print_name = element.title
            redirects += [(url, print_name)]

        if len(redirects) > 1:
            context = self.get_context_data(*args, **kwargs)
            context.update({'redirects': redirects})
            return self.render_to_response(context)
        return super(ScoreCardRedirectView, self).get(request, *args, **kwargs)


class BenchmarkBaseView(BenchmarkMixin, TemplateView):
    """
    Subclasses are meant to define `template_name` and `breadcrumb_url`.
    """

    def get_context_data(self, *args, **kwargs):
        #pylint:disable=too-many-locals
        context = super(BenchmarkBaseView, self).get_context_data(
            *args, **kwargs)
        from_root, trail = self.breadcrumbs
        root = None
        if trail:
            root = self._build_tree(trail[-1][0], from_root, cut=None)
            # Flatten icons and practices (i.e. Energy Efficiency) to produce
            # the list of charts.
            charts, complete = self.get_charts(root[1], path=from_root)
            cut_tree = self._cut_tree(root)
            context.update({
                'self_assessment_complete': complete,
                'charts': charts,
                'root': self._cut_tree(root),
                'entries': json.dumps(root),
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

    def get_assessment_redirect_url(self, *args, **kwargs):
        #pylint:disable=unused-argument
        path = kwargs.get('path')
        organization = kwargs.get('organization')
        if not isinstance(path, six.string_types):
            path = ""
        if organization in self.accessibles(
                roles=['manager', 'contributor']):
            # /app/:organization/scorecard/:path
            # Only when accessing an actual scorecard and if the request user
            # is a manager/contributor for the organization will we prompt
            # to start the self-assessment.
            messages.warning(self.request,
                "You need to complete a self-assessment before"\
                " moving on to the scorecard.")
            return HttpResponseRedirect(reverse('report_organization',
                kwargs={'organization': organization, 'path': path}))
        return HttpResponseRedirect(reverse('summary_organization',
            kwargs={'organization': organization, 'path': path}))

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

    def get(self, request, *args, **kwargs):
        organization = kwargs.get('organization')
        if not self.sample:
            if not organization in self.accessibles(
                    roles=['manager', 'contributor']):
                # /app/:organization/scorecard/:path
                # Only when accessing an actual scorecard and if the request
                # user is a viewer will we explain why the scorecard is not
                # visible. If the request user is manager/contributor
                # for the organization, calling `get_assessment_redirect_url`
                # will prompt the message to complete the self-assessment.
                messages.warning(self.request,
                    VIEWER_SELF_ASSESSMENT_NOT_YET_STARTED % {
                        'organization': organization})
            return self.get_assessment_redirect_url(*args, **kwargs)
        return super(ScoreCardView, self).get(request, *args, **kwargs)


class ScoreCardDownloadView(BenchmarkAPIView):
    """
    Shows the scorecard of an organization, accessible through
    the "My TSP" menu.
    """
    template_name = 'envconnect/prints/scorecard.html'

    def get_printable_charts(self):
        if not hasattr(self, '_printable_charts'):
            self._printable_charts = self.get_queryset()
            for chart in self._printable_charts:
                if ('text' in chart
                    and chart['text'].startswith('/')):
                    chart['text'] = \
                        "file://{{base_dir}}/htdocs" + chart['text']
        return self._printable_charts

    def get_context_data(self, *args, **kwargs):
        context = {'base_dir': settings.BASE_DIR}
        organization = self.kwargs.get('organization', None)
        if organization:
            for accessible in self.get_accessibles(self.request):
                if accessible['slug'] == organization:
                    context.update({'organization': accessible})
                    break
        from_root, trail = self.breadcrumbs
        root = None
        if trail:
            root = self._build_tree(trail[-1][0], from_root, cut=None)
            # Flatten icons and practices (i.e. Energy Efficiency) to produce
            # the list of charts.
            charts = self.get_printable_charts()
            for element in six.itervalues(root[1]):
                for chart in charts:
                    if element[0]['slug'] == chart['slug']:
                        if 'normalized_score' in chart:
                            element[0]['normalized_score'] = "%s%%" % chart.get(
                                'normalized_score')
                        else:
                            element[0]['normalized_score'] = "N/A"
                        element[0]['score_weight'] = chart.get(
                            'score_weight', "N/A")
                        break
            for chart in charts:
                if chart['slug'] == 'total-score':
                    context.update({
                        'total_chart': chart,
                        'nb_respondents': chart.get('nb_respondents', "N/A")})
                    break
            context.update({
                'charts': [chart
                    for chart in charts if chart['slug'] != 'total-score'],
                'breadcrumbs': trail,
                'root': self._cut_tree(root),
                'at_time': datetime_or_now()
            })
        return context

    def generate_chart_image(self, slug, template_name, context,
                             js_content, cache_storage, on_start=True,
                             width=400, height=300, delay=1):
        #pylint:disable=too-many-arguments
        context.update({'base_dir': settings.BASE_DIR})
        template = get_template(template_name)
        content = template.render(context, self.request)
        cache_storage.save('%s.html' % slug, io.StringIO(content))
        phantomjs_url = 'file://%s/%s.html' % (
            cache_storage.location, slug)
        img_path = cache_storage.path('%s.png' % slug)
        if on_start:
            js_content.write("""casper.start('%(url)s', function() {
    this.echo("starting...");
});
""" % {'url': phantomjs_url})
        js_content.write("""
casper.viewport(%(width)s, %(height)s).thenOpen('%(url)s', function() {
    this.wait(%(delay)d, function() {
        this.capture('%(img_path)s', {top: 0, left: 0, width: %(width)s, height: %(height)s});
    });
});
""" % {'width': width, 'height': height, 'delay': delay,
       'url': phantomjs_url, 'img_path': img_path})
        return "file://" + img_path

    def generate_printable_html(self):
        charts = self.get_printable_charts()
        location = tempfile.mkdtemp(
            prefix=settings.APP_NAME + "-", dir=settings.MEDIA_ROOT)
        base_url = settings.MEDIA_URL
        cache_storage = FileSystemStorage(
            location=location, base_url=base_url)
        js_content = io.StringIO()
        js_content.write("""var casper = require('casper').create();

""")
        on_start = True
        for chart in charts:
            if chart['slug'] == 'total-score':
                chart['image'] = self.generate_chart_image(chart['slug'],
                    'envconnect/prints/total_score.html',
                    context={'total_score': chart},
                    js_content=js_content,
                    cache_storage=cache_storage,
                    on_start=on_start,
                    width=300, height=200, delay=1000)
            else:
                chart['distribution'] = json.dumps(
                    chart.get('distribution', {}))
                chart['image'] = self.generate_chart_image(chart['slug'],
                    'envconnect/prints/benchmark_graph.html',
                    context={'chart': chart},
                    js_content=js_content,
                    cache_storage=cache_storage,
                    on_start=on_start,
                    width=210, height=204)
            on_start = False
        js_content.write("""
casper.run();
""")
        js_content.seek(0)
        js_generate_images = 'generate-images.js'
        cache_storage.save(js_generate_images, js_content)
        phantomjs_script_path = cache_storage.path(js_generate_images)
        cmd = [settings.PHANTOMJS_BIN.replace('bin/phantomjs', 'bin/casperjs'),
            phantomjs_script_path]
        LOGGER.info("RUN: %s", ' '.join(cmd))
        subprocess.check_call(cmd)

    def get(self, request, *args, **kwargs):
        self.generate_printable_html()
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
        #pylint:disable=too-many-locals
        candidate = self.kwargs.get(self.matrix_url_kwarg)
        if candidate.startswith("/"):
            candidate = candidate[1:]
        parts = candidate.split("/")
        if len(parts) > 1:
            candidate = parts[0]
        try:
            PageElement.objects.get(slug=candidate)
        except PageElement.DoesNotExist:
            # It is not a breadcrumb path (ex: totals).
            #pylint:disable=unsubscriptable-object
            del self.kwargs[self.matrix_url_kwarg]

        context = super(PortfoliosDetailView, self).get_context_data(
            *args, **kwargs)
        context.update({'available_matrices': self.get_available_matrices()})

        from_root, trail = self.breadcrumbs
        parts = from_root.split("/")
        if len(parts) > 1:
            root = self._build_tree(trail[-1][0], from_root)
            charts, _ = self.get_charts(root[1], path=from_root)
        else:
            # totals
            charts = []
            for cohort in self.object.cohorts.all():
                candidate = cohort.slug
                look = re.match(r"(\S+)(-\d+)$", candidate)
                if look:
                    candidate = look.group(1)
                element = PageElement.objects.filter(slug=candidate).first()
                charts += [{
                    'slug': cohort.slug,
                    'breadcrumbs': [cohort.title],
                    'text': element.text if element is not None else "",
                    'tag': element.tag if element is not None else ""
                }]
        url_kwargs = self.get_url_kwargs()
        url_kwargs.update({'matrix': self.object})
        for chart in charts:
            candidate = chart['slug']
            look = re.match(r"(\S+)(-\d+)$", candidate)
            if look:
                matrix_slug = '/'.join([look.group(1)])
            else:
                matrix_slug = '/'.join([str(self.object), candidate])
            url_kwargs.update({'matrix': matrix_slug})
            api_urls = {'matrix_api': reverse('matrix_api', kwargs=url_kwargs)}
            chart.update({'urls': api_urls})
        context.update({'charts': charts})
        return context

