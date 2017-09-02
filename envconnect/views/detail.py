# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.utils import six

from ..mixins import BestPracticeMixin
from ..models import ColumnHeader


class DetailView(BestPracticeMixin, TemplateView):

    template_name = 'envconnect/detail.html'
    breadcrumb_url = 'summary'

    def get(self, request, *args, **kwargs):
        _, trail = self.breadcrumbs
        if not trail:
            return HttpResponseRedirect(reverse('homepage'))
        return super(DetailView, self).get(request, *args, **kwargs)

    def get_breadcrumb_url(self, path):
        organization = self.kwargs.get('organization', None)
        if organization:
            return reverse('summary_organization', args=(organization, path))
        return super(DetailView, self).get_breadcrumb_url(path)

    def get_context_data(self, *args, **kwargs):
        #pylint:disable=too-many-locals
        context = super(DetailView, self).get_context_data(*args, **kwargs)
        from_root, trail = self.breadcrumbs
        # It is OK here to index by -1 since we would have generated a redirect
        # in the `get` method when the path is "/".
        root = self._build_tree(trail[-1][0], from_root)

        # attach visible column headers
        hidden_columns = {}
        is_envconnect_manager = self.manages(settings.APP_NAME)
        for icon_path, icon_tuple in six.iteritems(root[1]):
            hidden_columns[icon_path] = {}
            hidden = set([row['slug']
                for row in ColumnHeader.objects.filter(
                hidden=True, path=icon_path).values('slug')])
            profitability_headers = []
            for col_header in [
                        {"slug": "avg_energy_saving",
                         "title": "Savings",
                         "tooltip": "The average estimated percentage saved"\
" relative to spend in the area of focus (e.g. site energy, waste) resulting"\
" from the implementation of a best practice.\n***** > 5%\n****   3-5%\n***"\
"     2-3%\n**       1-2%\n*         < 1%\n Click individual best practice"\
" headings and navigate to the \"References\" section for more detail on data"\
" provenance."},
                        {"slug": "capital_cost",
                         "title": "Cost",
                        "tooltip": "The average estimated percentage of cost"\
" relative to spend in the area of focus (e.g. site energy, waste) to"\
" implement a best practice.\n$$$$$ < 10%\n$$$$   5-10%\n$$$     2-5%\n$$"\
"       1-2%\n$         < 1%\nClick individual best practice headings and"\
" navigate to the \"References\" section for more detail on data provenance."},
                        {"slug": "payback_period",
                         "title": "Payback years",
                         "tooltip": "Range: The range of payback values are"\
" calculated for a best practice implemented at a facility by the following"\
" formula: Simple Year-of-Payback = (Implementation Cost) / (Total Energy"\
" Cost Savings)\n\nAverage (in parentheses): The average represents an"\
" average of the totals represented by the range.\n\nClick individual best"\
" practice headings and navigate to the \"References\" section for more"\
" detail on data provenance."}]:
                if is_envconnect_manager:
                    profitability_headers += [col_header]
                    hidden_columns[icon_path][col_header['slug']] = (
                        col_header['slug'] in hidden)
                elif not col_header['slug'] in hidden:
                    profitability_headers += [col_header]
            icon_tuple[0]['profitability_headers'] = profitability_headers
            icon_tuple[0]['profitability_headers_len'] = len(
                profitability_headers) + 1
            value_headers = []
            for col_header in [
                    {"slug": "environmental_value",
                     "title": "/static/img/green-leaf.png",
                     "tooltip": "Environmental value"},
                    {"slug": "business_value",
                     "title": "/static/img/cogs.png",
                     "tooltip": "Ops/Maintenance value"},
                    {"slug": "profitability",
                     "title": "/static/img/dollar-sign.png",
                     "tooltip": "Financial value"},
                    {"slug": "implementation_ease",
                     "title": "/static/img/shovel.png",
                     "tooltip": "Implementation ease"},
                    {"slug": "avg_value",
                     "title": "Average Value"}]:
                if is_envconnect_manager:
                    value_headers += [col_header]
                    hidden_columns[icon_path][col_header['slug']] = (
                        col_header['slug'] in hidden)
                elif not col_header['slug'] in hidden:
                    value_headers += [col_header]
            icon_tuple[0]['value_headers'] = value_headers
            icon_tuple[0]['value_headers_len'] = len(value_headers) + 2
            icon_tuple[0]['colspan'] = max(
                icon_tuple[0]['profitability_headers_len'],
                icon_tuple[0]['value_headers_len'])

        if not is_envconnect_manager:
            context.update({'sort_by': "{'agv_value': 'desc'}"})
        context.update({
            'role': "tab",
            'root': root,
            'entries': json.dumps(root),
            'hidden': json.dumps(hidden_columns)
        })
        return context
