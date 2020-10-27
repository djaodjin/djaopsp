# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from django.db import transaction
from rest_framework import generics
from rest_framework.generics import get_object_or_404
from survey.models import EnumeratedQuestions

from ..serializers import ConsumptionSerializer
from ..mixins import BreadcrumbMixin
from ..models import Consumption


class ConsumptionListAPIView(BreadcrumbMixin, generics.ListCreateAPIView):
    """
    Retrieve consumptions

    XXX It seems only POST is used, and what it is used for is:
    - to duplicate the content sent to PageElement.
    - update the environmental_value, business_value, profitability, etc.

    **Tags**: survey

    **Examples**

    .. code-block:: http

         GET /api/content/editables/consumption/ HTTP/1.1

    responds

    .. code-block:: json

        {
            "count": 1,
            "previous": null,
            "next": null,
            "results": [{
                "created_at": "2020-01-01T00:00:00Z",
                "measured": 12
            }]
        }
    """

    queryset = Consumption.objects.all()
    serializer_class = ConsumptionSerializer

    def post(self, request, *args, **kwargs):
        """
        Creates a consumption

        XXX It seems only POST is used, and what it is used for is:
        - to duplicate the content sent to PageElement.
        - update the environmental_value, business_value, profitability, etc.

        **Tags**: survey

        **Examples**

        .. code-block:: http

             POST /api/content/editables/consumption/ HTTP/1.1

        .. code-block:: json

            {
                "measured": 12
            }

        responds

        .. code-block:: json

            {
                "created_at": "2020-01-01T00:00:00Z",
                "measured": 12
            }
        """
        #pylint:disable=useless-super-delegation
        return super(ConsumptionListAPIView, self).post(
            request, *args, **kwargs)

    def perform_create(self, serializer):
        # Keep database consistent in case we deleted a best practice
        # but not the associated ``Consumption``, then re-created a best
        # practice with the same slug.
        try:
            serializer.instance = self.queryset.get(
                path=serializer.validated_data['path'])
        except Consumption.DoesNotExist:
            pass
        with transaction.atomic():
            consumption = serializer.save()
            EnumeratedQuestions.objects.get_or_create(
                campaign=self.campaign, question=consumption,
                defaults={'rank': self.get_next_rank()})


# Derives from BreadcrumbMixin for ``get_serializer_context``.
class ConsumptionEditableDetailAPIView(BreadcrumbMixin,
                               generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves editable intrinsic value of a practice

    **Tags**: editors

    **Examples

    .. code-block:: http

        GET /api/content/editables/envconnect/values/boxes-enclosures\
/energy-efficiency/air-flow/ HTTP/1.1

    responds

    .. code-block:: json

        {
           "path": "/boxes-enclosures/energy-efficiency/air-flow",
           "environmental_value": 1,
           "business_value": 1,
           "profitability": 3,
           "implementation_ease": 1,
           "avg_value": 2
        }
    """
    queryset = Consumption.objects.all()
    serializer_class = ConsumptionSerializer

    def get_object(self):
        return get_object_or_404(self.get_queryset(), path=self.path)

    def put(self, request, *args, **kwargs):
        """
         Updates intrinsic value of a practice

        **Tags**: editors

        **Examples

        .. code-block:: http

            PUT /api/content/editables/envconnect/values/boxes-enclosures\
/energy-efficiency/air-flow HTTP/1.1

        .. code-block:: json

            {
                "environmental_value": 1,
                "business_value": 1,
                "profitability": 3,
                "implementation_ease": 1
            }

        responds

        .. code-block:: json

            {
                "path": "/boxes-enclosures/energy-efficiency/air-flow",
                "environmental_value": 1,
                "business_value": 1,
                "profitability": 3,
                "implementation_ease": 1,
                "avg_value": 2
            }
        """
        #pylint:disable=useless-super-delegation
        return super(ConsumptionEditableDetailAPIView, self).put(
            request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Deletes intrinsic value of a practice

        **Tags**: editors

        **Examples

        .. code-block:: http

            DELETE /api/content/editables/envconnect/values/boxes-enclosures/\
energy-efficiency/air-flow HTTP/1.1

        """
        #pylint:disable=useless-super-delegation
        return super(ConsumptionEditableDetailAPIView, self).delete(
            request, *args, **kwargs)

    def perform_update(self, serializer):
        # Force "Gold" value to be outside the linear scale.
        for field_name in Consumption.VALUE_SUMMARY_FIELDS:
            if (field_name in serializer.validated_data and
                serializer.validated_data[field_name] == 4):
                serializer.validated_data[field_name] = 6
        return super(ConsumptionEditableDetailAPIView, self).perform_update(
            serializer)
