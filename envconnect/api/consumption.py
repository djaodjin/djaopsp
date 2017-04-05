# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from answers.models import Question
from django.db import transaction
from django.db.models import Max
from rest_framework import generics
from survey.models import SurveyModel

from ..serializers import ConsumptionSerializer
from ..mixins import ReportMixin
from ..models import Consumption


class ConsumptionListAPIView(ReportMixin, generics.ListCreateAPIView):
    # XXX ``ReportMixin`` because we want to access ``report_title``.

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
            survey = generics.get_object_or_404(
                SurveyModel.objects.all(), title=self.report_title)
            last_rank = survey.questions.aggregate(Max('rank')).get(
                'rank__max', 0)
            serializer.save(survey=survey, rank=last_rank + 1)
            last = serializer.validated_data['path'].split('/')[-1]
            Question.objects.get_or_create(slug=last,
                defaults={'user': self.request.user})


class ConsumptionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Consumption.objects.all()
    serializer_class = ConsumptionSerializer
    lookup_field = 'path'
