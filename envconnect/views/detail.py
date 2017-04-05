# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import json

from django.views.generic import TemplateView

from ..mixins import BreadcrumbMixin
from ..models import ColumnHeader

class DetailView(BreadcrumbMixin, TemplateView):

    template_name = 'envconnect/detail.html'
    breadcrumb_url = 'sustainability'

    def get_template_names(self):
        if self.breadcrumb_url == 'basic':
            return 'envconnect/detail_%s.html' % self.breadcrumb_url
        return super(DetailView, self).get_template_names()

    def get_context_data(self, *args, **kwargs):
        #pylint:disable=too-many-locals
        context = super(DetailView, self).get_context_data(*args, **kwargs)
        if len(context['breadcrumbs']) > 0:
            root, _, _ = context['breadcrumbs'][-1]
            root = self._build_tree(root, context['from_root'])
            # attach visible column headers
            hidden_columns = {}
            is_envconnect_manager = self.manages('envconnect')
            for icon_tuple in root[1]:
                path = '/'.join([context['from_root'], icon_tuple[0].slug])
                hidden_columns[path] = {}
                hidden = set([row['slug']
                    for row in ColumnHeader.objects.filter(
                    hidden=True, path=path).values('slug')])
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
                        hidden_columns[path][col_header['slug']] = (
                            col_header['slug'] in hidden)
                    elif not col_header['slug'] in hidden:
                        profitability_headers += [col_header]
                setattr(icon_tuple[0], 'profitability_headers',
                    profitability_headers)
                setattr(icon_tuple[0], 'profitability_headers_len',
                    len(profitability_headers) + 1)
                value_headers = []
                for col_header in [
                        {"slug": "environmental_value",
                         "title": "Environmental value"},
                        {"slug": "business_value",
                         "title": "Social value"},
                        {"slug": "profitability",
                         "title": "Profitability"},
                        {"slug": "implementation_ease",
                         "title": "Implementation ease"},
                        {"slug": "avg_value",
                         "title": "Average Value"}]:
                    if is_envconnect_manager:
                        value_headers += [col_header]
                        hidden_columns[path][col_header['slug']] = (
                            col_header['slug'] in hidden)
                    elif not col_header['slug'] in hidden:
                        value_headers += [col_header]
                setattr(icon_tuple[0], 'value_headers',
                    value_headers)
                setattr(icon_tuple[0], 'value_headers_len',
                    len(value_headers) + 2)
            context.update({
                'role': "tab",
                'root': root,
                'entries': json.dumps(self.to_representation(root)),
                'hidden': json.dumps(hidden_columns)
            })
        return context
