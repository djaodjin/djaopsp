# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

from collections import OrderedDict

from rest_framework.response import Response
from survey.pagination import MetricsPagination

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
