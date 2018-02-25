# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

from django.db import transaction
from rest_framework import generics
from survey.models import EnumeratedQuestions

from ..serializers import ConsumptionSerializer
from ..mixins import BreadcrumbMixin
from ..models import Consumption


class ConsumptionListAPIView(BreadcrumbMixin, generics.ListCreateAPIView):

    queryset = Consumption.objects.all()
    serializer_class = ConsumptionSerializer

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
                campaign=self.survey, question=consumption,
                defaults={'rank': self.get_next_rank()})


# Derives from BreadcrumbMixin for ``get_serializer_context``.
class ConsumptionDetailAPIView(BreadcrumbMixin,
                               generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update and delete a `Consumption`.

    **Example request**:

    .. sourcecode:: http

        PUT /api/consumption/boxes-enclosures/energy-efficiency/air-flow/
        {
        }

    **Example response**:

    .. sourcecode:: http

    """

    queryset = Consumption.objects.all()
    serializer_class = ConsumptionSerializer
    lookup_field = 'path'

    def perform_update(self, serializer):
        # Force "Gold" value to be outside the linear scale.
        for field_name in Consumption.VALUE_SUMMARY_FIELDS:
            if (field_name in serializer.validated_data and
                serializer.validated_data[field_name] == 4):
                serializer.validated_data[field_name] = 6
        return super(ConsumptionDetailAPIView, self).perform_update(serializer)
