# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

import logging
from collections import namedtuple

from deployutils.helpers import datetime_or_now
from django.db import connection, transaction
from rest_framework.status import HTTP_200_OK
from rest_framework import response as http
from survey.api.sample import AnswerAPIView, SampleAPIView
from survey.models import Answer, Sample

from ..mixins import ReportMixin
from ..models import get_scored_answers
from ..serializers import ConsumptionSerializer


LOGGER = logging.getLogger(__name__)


class AssessmentAnswerAPIView(AnswerAPIView):
    """
    Answers about the implementation of a best practice.
    """

    def get_queryset(self):
        return super(AssessmentAnswerAPIView, self).get_queryset().filter(
            metric=self.question.default_metric)

    def get_http_response(self, serializer,
                     status=HTTP_200_OK, headers=None):
        scored_answers = get_scored_answers(
            includes=(self.sample.pk,), questions=(self.question.pk,))
        with connection.cursor() as cursor:
            cursor.execute(scored_answers, params=None)
            col_headers = cursor.description
            decorated_answer_tuple = namedtuple('DecoratedAnswerTuple',
                [col[0] for col in col_headers])
            decorated_answer = decorated_answer_tuple(*cursor.fetchone())
        data = ConsumptionSerializer(context={
            'campaign': self.sample.survey
        }).to_representation(decorated_answer)
        return http.Response(data, status=status, headers=headers)


class AssessmentAPIView(ReportMixin, SampleAPIView):

    account_url_kwarg = 'interviewee'

    def update(self, request, *args, **kwargs):
        #pylint:disable=too-many-locals
        with transaction.atomic():
            result = super(AssessmentAPIView, self).update(
                request, *args, **kwargs)
            if self.sample.is_frozen:
                LOGGER.info("freeze scores for %s", self.sample.account)
                created_at = datetime_or_now()
                scored_answers = get_scored_answers(
                    includes=self.get_included_samples(),
                    excludes=self._get_filter_out_testing())
                score_sample = Sample.objects.create(
                    created_at=created_at,
                    survey=self.sample.survey,
                    account=self.sample.account,
                    extra='completed',
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
                                question_id=decorated_answer.question_id,
                                metric_id=2,
                                measured=numerator,
                                denominator=denominator,
                                collected_by=self.request.user,
                                sample=score_sample,
                                rank=decorated_answer.rank)
                self.sample.created_at = datetime_or_now()
                self.sample.save()
        return result
