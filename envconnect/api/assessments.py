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
from survey.models import Answer, Choice, EnumeratedQuestions, Sample, Unit
from survey.mixins import SampleMixin
from survey.utils import get_question_model

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

    @staticmethod
    def freeze_scores(sample, includes=None, excludes=None,
                      collected_by=None, created_at=None):
        LOGGER.info("freeze scores for %s", sample.account)
        created_at = datetime_or_now(created_at)
        scored_answers = get_scored_answers(
            population=Consumption.objects.get_active_by_accounts(
                excludes=excludes),
            includes=includes)
        score_sample = Sample.objects.create(
            created_at=created_at,
            survey=sample.survey,
            account=sample.account,
            is_frozen=True)
        with connection.cursor() as cursor:
            cursor.execute(scored_answers, params=None)
            col_headers = cursor.description
            decorated_answer_tuple = namedtuple(
                'DecoratedAnswerTuple', [col[0] for col in col_headers])
            for decorated_answer in cursor.fetchall():
                decorated_answer = decorated_answer_tuple(
                    *decorated_answer)
                if decorated_answer.answer_id:
                    numerator = decorated_answer.numerator
                    denominator = decorated_answer.denominator
                    _ = Answer.objects.create(
                        created_at=created_at,
                        question_id=decorated_answer.id,
                        metric_id=2,
                        measured=numerator,
                        denominator=denominator,
                        collected_by=collected_by,
                        sample=score_sample,
                        rank=decorated_answer.rank)
        sample.created_at = datetime_or_now()
        sample.save()
        return score_sample

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            result = super(AssessmentAPIView, self).update(
                request, *args, **kwargs)
            if self.sample.extra is None and self.sample.is_frozen:
                self.freeze_scores(self.sample,
                    includes=self.get_included_samples(),
                    excludes=self._get_filter_out_testing(),
                    collected_by=self.request.user)
        return result


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
