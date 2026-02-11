# Copyright (c) 2026, DjaoDjin inc.
# see LICENSE.

from collections import OrderedDict

from rest_framework.pagination import (
    PageNumberPagination as BasePageNumberPagination)
from rest_framework.response import Response
from survey.pagination import MetricsPagination

from .compat import gettext_lazy as _


class PageNumberPagination(BasePageNumberPagination):

    max_page_size = 100
    page_size_query_param = 'page_size'
    page_size_query_description = _("Number of results to return per page"\
    " between 1 and 100 (defaults to 25).")

    def get_paginated_response_schema(self, schema):
        if 'description' not in schema:
            schema.update({'description': "Records in the queryset"})
        return {
            'type': 'object',
            'properties': {
                'count': {
                    'type': 'integer',
                    'description': "The number of records"
                },
                'next': {
                    'type': 'string',
                    'description': "API end point to get the next page"\
                        " of records matching the query",
                    'nullable': True,
                    'format': 'uri',
                },
                'previous': {
                    'type': 'string',
                    'description': "API end point to get the previous page"\
                        " of records matching the query",
                    'nullable': True,
                    'format': 'uri',
                },
                'results': schema,
            },
        }


class BenchmarksPagination(MetricsPagination):
    """
    Decorate the results of an API call with min, avg and max scores
    """

    def paginate_queryset(self, queryset, request, view=None):
        super(BenchmarksPagination, self).paginate_queryset(
            queryset, request, view=view)
        #pylint:disable=attribute-defined-outside-init
        self.view = view
        self.avg_normalized_score = None
        self.highest_normalized_score = None
        if queryset:
            self.avg_normalized_score = queryset[0].get('avg_normalized_score')
            self.highest_normalized_score = queryset[0].get('highest_normalized_score')
        return queryset

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('title', getattr(self.view, 'title', "")),
            ('scale', getattr(self.view, 'scale', 1)),
            ('unit', getattr(self.view, 'unit', None)),
            ('nb_accounts', getattr(self.view, 'nb_accounts', None)),
            ('labels', getattr(self.view, 'labels', None)),
            ('count', len(data)),
            ('avg_normalized_score', self.avg_normalized_score),
            ('highest_normalized_score', self.highest_normalized_score),
            ('results', data)
        ]))

    def get_paginated_response_schema(self, schema):
        resp = super(BenchmarksPagination, self).get_paginated_response_schema(
            schema)
        resp['properties'].update({
                'avg_normalized_score': {
                    'type': 'integer',
                    'description': "Average score for the campaign"
                },
                'highest_normalized_score': {
                    'type': 'integer',
                    'description': "Highest score for the campaign"
                }
        })
        return resp


class AccessiblesPagination(PageNumberPagination):
    """
    Decorate the results of the accessibles API call.
    """
    def paginate_queryset(self, queryset, request, view=None):
        self.view = view
        return super(AccessiblesPagination, self).paginate_queryset(
            queryset, request, view=view)


    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('title', getattr(self.view, 'title', "")),
            ('scale', getattr(self.view, 'scale', 1)),
            ('unit', getattr(self.view, 'unit', None)),
            ('nb_accounts', getattr(self.view, 'nb_accounts', None)),
            ('labels', getattr(self.view, 'labels', None)),
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))

    def get_paginated_response_schema(self, schema):
        if 'description' not in schema:
            schema.update({'description': "Items in the queryset"})
        return {
            'type': 'object',
            'properties': {
                'title': {
                    'type': 'integer',
                    'description': "Title for the results table"
                },
                'scale': {
                    'type': 'integer',
                    'description': "The scale of the number reported"\
                    " in the tables (ex: 1000 when numbers are reported"\
                    " in thousands)"
                },
                'unit': {
                    'type': 'integer',
                    'description': "Unit the measured field is in"
                },
                'nb_accounts': {
                    'type': 'integer',
                    'description': "Total number of accounts evaluated"
                },
                'labels': {
                    'type': 'array',
                    'description': "Labels for the x-axis when present"
                },
                'count': {
                    'type': 'integer',
                    'description': "The number of records"
                },
                'next': {
                    'type': 'string',
                    'description': "API end point to get the next page"\
                        "of results matching the query",
                    'nullable': True,
                    'format': 'uri',
                },
                'previous': {
                    'type': 'string',
                    'description': "API end point to get the previous page"\
                        "of results matching the query",
                    'nullable': True,
                    'format': 'uri',
                },
                'results': schema,
            },
        }
