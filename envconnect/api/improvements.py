# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from django.db import transaction
from rest_framework import serializers, status
from rest_framework.generics import (get_object_or_404, ListAPIView,
     GenericAPIView)
from rest_framework.mixins import (CreateModelMixin, RetrieveModelMixin,
    DestroyModelMixin)
from rest_framework.response import Response
from survey.models import Answer, Question, EnumeratedQuestions

from ..mixins import ImprovementQuerySetMixin
from ..models import Consumption


class ImprovementSerializer(serializers.ModelSerializer):

    consumption = serializers.SerializerMethodField()

    class Meta(object):
        model = Answer
        fields = ('consumption',)

    @staticmethod
    def get_consumption(obj):
        return obj.question.consumption.path


class ImprovementListAPIView(ImprovementQuerySetMixin, ListAPIView):

    serializer_class = ImprovementSerializer

    def get_serializer_context(self):
        """
        Provides a list of opportunities, one for each ``Question``.
        """
        context = super(ImprovementListAPIView, self).get_serializer_context()
        context.update({'opportunities': Consumption.objects.with_opportunity(
            filter_out_testing=self._get_filter_out_testing())})
        return context


class ImprovementToggleAPIView(ImprovementQuerySetMixin,
                                CreateModelMixin, RetrieveModelMixin,
                                DestroyModelMixin, GenericAPIView):

    serializer_class = ImprovementSerializer

    def get_object(self):
        return get_object_or_404(self.get_queryset(),
            question__consumption__path=self.kwargs.get('path'))

    def create(self, request, *args, **kwargs):
        question = get_object_or_404(Question.objects.all(),
            consumption__path=self.kwargs.get('path'))
        with transaction.atomic():
            self.get_or_create_improve_sample()
            with transaction.atomic():
                # Implementation Note: We need to set the `text` field
                # otherwise `get_scored_answers` will return a numerator
                # of zero. We use `NEEDS_SIGNIFICANT_IMPROVEMENT` such
                # as to be conservative in the calculation.
                rank = EnumeratedQuestions.objects.get(
                    campaign=self.improvement_sample.survey,
                    question=question).rank
                _, created = self.model.objects.get_or_create(
                    sample=self.improvement_sample,
                    question=question,
                    defaults={
                        'measured': Consumption.NEEDS_SIGNIFICANT_IMPROVEMENT,
                        'rank': rank})
        return Response({},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        # get_queryset() will filter by `account`. We filter by `path`
        # as in `get_object`. It should return a single result but
        # in case the db was corrupted, let's just fix it on the fly here.
        # XXX In the future the improvements must relate to a specific year.
        self.get_queryset().filter(
            question__consumption__path=self.kwargs.get('path')).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

