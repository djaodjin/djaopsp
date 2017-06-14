# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import csv, datetime, json, logging, StringIO

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from survey.models import Response, SurveyModel

from .benchmark import BenchmarkBaseView
from ..models import Consumption


LOGGER = logging.getLogger(__name__)


class SelfAssessmentBaseView(BenchmarkBaseView):

    def attach_benchmarks(self, root, view_response=None):
        if not view_response:
            self._sample = Response.objects.create(account=self.account,
                survey=SurveyModel.objects.get(title=self.report_title))
        super(SelfAssessmentBaseView, self).attach_benchmarks(
            root, view_response=self._sample)


class SelfAssessmentView(SelfAssessmentBaseView):

    template_name = 'envconnect/self_assessment.html'
    breadcrumb_url = 'report'

    def get_context_data(self, **kwargs):
        context = super(SelfAssessmentView, self).get_context_data(**kwargs)
        if self.root:
            self.attach_benchmarks(self.root, view_response=self.sample)
            context.update({
                'entries': json.dumps(self.to_representation(self.root))
            })

        context.update({
            'page_icon': self.icon,
            'response': self.sample,
            'survey': self.sample.survey,
            'role': "tab",
            'score_toggle': self.request.GET.get('toggle', False)})
        urls = {'api_self_assessment_response': reverse(
            'survey_api_response', args=(context['organization'], self.sample))}
        self.update_context_urls(context, urls)
        return context

    def get(self, request, *args, **kwargs):
        from_root, _ = self.breadcrumbs
        if not from_root or from_root == "/":
            return HttpResponseRedirect(reverse('homepage'))
        return super(SelfAssessmentView, self).get(request, *args, **kwargs)


class SelfAssessmentCSVView(SelfAssessmentBaseView):

    basename = 'self-assessment'

    def insert_path(self, tree, parts=None):
        if not parts:
            return tree
        if not parts[0] in tree:
            tree[parts[0]] = {}
        return self.insert_path(tree[parts[0]], parts[1:])

    def write_tree(self, root, csv_writer, indent=''):
        """
        The *root* parameter looks like:
        (PageElement, [(PageElement, [...]), (PageElement, [...]), ...])
        """
        if not root[1]:
            # We reached a leaf
            consumption = getattr(root[0], 'consumption', None)
            row = [indent + root[0].title]
            if consumption:
                for heading in self.get_headings(root[0].tag):
                    if consumption.implemented == heading:
                        row += ['X']
                    else:
                        row += ['']
            csv_writer.writerow([rec.encode('utf-8') for rec in row])
        else:
            csv_writer.writerow([indent + root[0].title])
            for element in root[1]:
                self.write_tree(element, csv_writer, indent=indent + '  ')

    def get(self, *args, **kwargs): #pylint: disable=unused-argument
        # All self-assessment questions for an industry, regardless
        # of the actual from_path.
        # XXX if we do that, we shouldn't use from_root (i.e. system pages)
        _, trail = self.breadcrumbs
        from_trail_head = "/" + "/".join([element.slug
            for element in self.get_full_element_path("/" + trail[0][0].slug)])
        self.root = self._build_tree(trail[0][0], from_trail_head, nocuts=True)
        self.attach_benchmarks(self.root, view_response=self.sample)

        content = StringIO.StringIO()
        csv_writer = csv.writer(content)
        csv_writer.writerow(["The Sustainability Project - Self-assessment"])
        csv_writer.writerow([self.root[0].title])
        indent = ' '
        for nodes in self.root[1]:
            csv_writer.writerow([indent + nodes[0].title]
                + self.get_headings(nodes[0].tag))
            for elements in nodes[1]:
                self.write_tree(elements, csv_writer, indent=indent + ' ')
        content.seek(0)
        resp = HttpResponse(content, content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())
        return resp

    @staticmethod
    def get_headings(tag):
        return list(Consumption.ASSESSMENT_CHOICES.get(tag,
            Consumption.ASSESSMENT_CHOICES.get('default')))

    def get_filename(self):
        return datetime.datetime.now().strftime(self.basename + '-%Y%m%d.csv')

