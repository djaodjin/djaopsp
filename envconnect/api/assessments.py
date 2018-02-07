# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

from collections import namedtuple

from django.db import connection
from rest_framework.status import HTTP_200_OK
from rest_framework import response as http
from survey.api.sample import AnswerAPIView

from ..models import get_scored_answers
from ..serializers import ConsumptionSerializer


class AssessmentAPIView(AnswerAPIView):
    """
    Answers about the implementation of a best practice.
    """

    def get_queryset(self):
        return super(AssessmentAPIView, self).get_queryset().filter(
            metric=self.question.default_metric)

    def get_http_response(self, serializer,
                     status=HTTP_200_OK, headers=None):
        scored_answers = get_scored_answers(
            includes=(self.sample.pk,), questions=(self.question.pk,))
        with connection.cursor() as cursor:
            cursor.execute(scored_answers, params=None)
            col_headers = cursor.description
            decorated_answer_tuple = namedtuple('DecoratedAnswerTuple',
                ['rank'] + [col[0] for col in col_headers])
            decorated_answer = decorated_answer_tuple(
                self.rank, *cursor.fetchone())
        data = ConsumptionSerializer(context={
            'campaign': self.sample.survey
        }).to_representation(decorated_answer)
        return http.Response(data, status=status, headers=headers)
