# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

import logging
from collections import OrderedDict

from rest_framework import generics, status
from rest_framework.response import Response as HttpResponse

from ..downloads.base import XLSXRenderer
from ..api.serializers import ExtendedSampleBenchmarksSerializer


LOGGER = logging.getLogger(__name__)


class BenchmarksExportAPIView(generics.CreateAPIView):

    renderer_classes = [XLSXRenderer]
    serializer_class = ExtendedSampleBenchmarksSerializer

    # required by `XLSXRenderer`
    title = "Export"
    descr = ""
    headings = ['dataset', 'choice', 'measured']

    def post(self, request, *args, **kwargs):
        """
        Export benchmarks to .xlsx

        **Examples

        .. code-block:: http

            POST /api/exports HTTP/1.1

        .. code-block:: json

            {
                "title": "All",
                "scale": 1,
                "unit": "profiles",
                "labels": null,
                "results": [
                    {
            "path": "/sustainability/esg-strategy-heading/formalized-esg-strategy",
                        "title": "1.1 Does your company have a formalized ESG strategy and performance targets that: 1/ Define a future vision of ESG performance, 2/ Are clear, actionable, and achievable, 3/ Are resourced effectively, 4/ Address material issues for the business?",
                        "default_unit": {
                            "slug": "yes-no",
                            "title": "Yes/No",
                            "system": "enum",
                            "choices": []
                        },
                        "ui_hint": null,
                        "benchmarks": [
                            {
                                "slug": "all",
                                "title": "All",
                                "values": [
                                    [
                                        "No",
                                        642
                                    ],
                                    [
                                        "Yes",
                                        686
                                    ]
                                ]
                            }
                        ]
                    }
                ]
            }
        """
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        table = []
        for key_idx, val in request.data.items():
            key_idx_parts = key_idx.split('_')
            key = key_idx_parts[0]
            idx = int(key_idx_parts[-1])
            if idx >= len(table):
                for dummy in range(len(table), idx + 1):
                    table += [OrderedDict()]
            if key in ('title', 'unit', 'measured'):
                table[idx].update({key: val})

        data = {'results': table}
        headers = self.get_success_headers(data)
        return HttpResponse(data,
            status=status.HTTP_201_CREATED, headers=headers)
