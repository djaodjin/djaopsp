# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import csv, datetime, json, logging, StringIO

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect

from .benchmark import BenchmarkBaseView
from ..models import Consumption


LOGGER = logging.getLogger(__name__)


class SelfAssessmentView(BenchmarkBaseView):

    template_name = 'envconnect/self_assessment.html'
    breadcrumb_url = 'report'

    def get_context_data(self, **kwargs):
        context = super(SelfAssessmentView, self).get_context_data(**kwargs)

        # XXX Hack to show answers, i.e. decorate consumption.implemented
        try:
            view_response = self.sample
        except Http404:
            view_response = None
        self.attach_benchmarks(self.root, view_response=view_response)
        context.update({
            'entries': json.dumps(self.to_representation(self.root))
        })

        if hasattr(self, 'icon') and self.icon is not None:
            icon = self.icon
        else:
            icon = self.breadcrumbs[-1][0][0]
        context.update({
            'page_icon': icon,
            'survey': self.survey,
            'response': self.sample,
            'role': "tab",
            'score_toggle': self.request.GET.get('toggle', False)})
        return context

    def get(self, request, *args, **kwargs):
        from_root, _ = self.breadcrumbs
        if not from_root:
            return HttpResponseRedirect(reverse('homepage'))
        return super(SelfAssessmentView, self).get(request, *args, **kwargs)


class SelfAssessmentCSVView(BenchmarkBaseView):

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
            if consumption:
                row = [indent + root[0].title]
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
        _ = self.get_context_data(**kwargs)
        try:
            view_response = self.sample
        except Http404:
            view_response = None
        self.attach_benchmarks(self.root, view_response=view_response)

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

