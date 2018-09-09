# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

import logging
from collections import namedtuple

from deployutils.helpers import datetime_or_now
from django.db import connection, transaction
from django.db.models import Max
from rest_framework import response as http
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView
from rest_framework.status import HTTP_200_OK
from survey.api.sample import AnswerAPIView, SampleAPIView
from survey.models import Answer, Choice, EnumeratedQuestions, Unit
from survey.mixins import SampleMixin
from survey.utils import get_question_model

from ..helpers import freeze_scores
from ..mixins import ExcludeDemoSample, ReportMixin
from ..models import Consumption, get_scored_answers
from ..serializers import AnswerUpdateSerializer, AssessmentMeasuresSerializer


LOGGER = logging.getLogger(__name__)


class AssessmentAnswerAPIView(ExcludeDemoSample, AnswerAPIView):
    """
    Answers about the implementation of a best practice.
    """

    def get_queryset(self):
        return super(AssessmentAnswerAPIView, self).get_queryset().filter(
            metric=self.question.default_metric)

    def get_http_response(self, serializer,
                     status=HTTP_200_OK, headers=None, first_answer=False):
        #pylint:disable=protected-access
        scored_answers = get_scored_answers(
            population=Consumption.objects.get_active_by_accounts(
                excludes=self._get_filter_out_testing()),
            includes=(self.sample,),
            questions=(self.question.pk,))
        with connection.cursor() as cursor:
            cursor.execute(scored_answers, params=None)
            col_headers = cursor.description
            decorated_answer_tuple = namedtuple('DecoratedAnswerTuple',
                [col[0] for col in col_headers])
            decorated_answer = decorated_answer_tuple(*cursor.fetchone())
        data = AnswerUpdateSerializer(context={
            'campaign': self.sample.survey
        }).to_representation({
            'consumption':decorated_answer,
            'first': first_answer
        })
        return http.Response(data, status=status, headers=headers)


class AssessmentAPIView(ReportMixin, SampleAPIView):

    account_url_kwarg = 'interviewee'

    def update(self, request, *args, **kwargs):
        #pylint:disable=unused-argument
        # We donot call super() because the up-to-date assessment should
        # never be frozen.
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance,
            data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            freeze_scores(self.sample,
                includes=self.get_included_samples(),
                excludes=self._get_filter_out_testing(),
                collected_by=self.request.user)
        return http.Response(serializer.data)


class AssessmentMeasuresAPIView(ReportMixin, SampleMixin, ListCreateAPIView):

    account_url_kwarg = 'interviewee'
    lookup_rank_kwarg = 'rank'
    lookup_field = 'rank'
    serializer_class = AssessmentMeasuresSerializer

    @property
    def question(self):
        if not hasattr(self, '_question'):
            self._question = get_question_model().objects.get(
                enumeratedquestions__campaign=self.sample.survey,
                enumeratedquestions__rank=self.kwargs.get(
                    self.lookup_rank_kwarg))
        return self._question

    def perform_create(self, serializer):
        created_at = datetime_or_now()
        rank = EnumeratedQuestions.objects.get(
            campaign=self.sample.survey,
            question=self.question).rank
        with transaction.atomic():
            for datapoint in serializer.validated_data['measures']:
                metric = datapoint['metric']
                try:
                    measured = int(datapoint['measured'])
                except ValueError:
                    if metric.unit.system != Unit.SYSTEM_ENUMERATED:
                        raise ValidationError({'detail':
                            "\"%s\" is invalid for '%s'" % (
                                datapoint['measured'].replace('"', '\\"'),
                                metric.title)})
                    choice_rank = Choice.objects.filter(
                        unit=metric.unit).aggregate(Max('rank')).get(
                            'rank__max', 0)
                    choice_rank = choice_rank + 1 if choice_rank else 1
                    choice = Choice.objects.create(
                        text=datapoint['measured'],
                        unit=metric.unit,
                        rank=choice_rank)
                    measured = choice.id
                Answer.objects.update_or_create(
                    sample=self.sample, question=self.question, metric=metric,
                    defaults={
                        'created_at': created_at,
                        'measured': measured,
                        'collected_by': self.request.user,
                        'rank': rank})
