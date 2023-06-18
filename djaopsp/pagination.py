# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

from collections import OrderedDict

from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class BenchmarksPagination(BasePagination):
    """
    Decorate the results of an API call with min, avg and max scores
    """

    def paginate_queryset(self, queryset, request, view=None):
        #pylint:disable=attribute-defined-outside-init
        self.view = view
        self.avg_normalized_score = queryset[0].get('avg_normalized_score')
        self.highest_normalized_score = queryset[0].get('highest_normalized_score')
        return queryset

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('avg_normalized_score', self.avg_normalized_score),
            ('highest_normalized_score', self.highest_normalized_score),
            ('results', data)
        ]))

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'avg_normalized_score': {
                    'type': 'integer',
                    'description': "Average score for the campaign"
                },
                'highes_normalized_score': {
                    'type': 'integer',
                    'description': "Highest score for the campaign"
                },
                'results': schema,
            },
        }
