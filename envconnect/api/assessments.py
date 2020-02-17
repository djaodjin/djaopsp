# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

import decimal, logging
from collections import namedtuple

from deployutils.helpers import datetime_or_now
from django.db import connection, transaction
from django.db.models import Max
from django.db.utils import DataError
from rest_framework import response as http
from rest_framework.exceptions import ValidationError
from rest_framework.generics import DestroyAPIView, ListCreateAPIView
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from survey.api.sample import AnswerAPIView, SampleAPIView
from survey.api.serializers import AnswerSerializer
from survey.models import Answer, Choice, EnumeratedQuestions, Unit
from survey.mixins import SampleMixin
from survey.utils import get_question_model

from ..helpers import freeze_scores
from ..mixins import ExcludeDemoSample, ReportMixin
from ..models import Consumption, get_scored_answers
from ..serializers import (AnswerUpdateSerializer, AssessmentMeasuresSerializer,
    NoModelSerializer)


LOGGER = logging.getLogger(__name__)


class AssessmentAnswerAPIView(ExcludeDemoSample, AnswerAPIView):
    """
    Answers about the implementation of a best practice.

    **Tags**: survey

    **Examples

    .. code-block:: http

        POST /api/energy-utility/sample/724bf9648af6420ba79c8a37f962e97e/3/ \
          HTTP/1.1

    .. code-block:: json

        {}

    responds

    .. code-block:: json

        {}
    """
    serializer_class = AnswerSerializer # otherwise API doc is not generated.

    def get_queryset(self):
        # XXX Same as AnswerAPIView but filters only the `default_metric`
        return super(AssessmentAnswerAPIView, self).get_queryset().filter(
            metric=self.question.default_metric)

    def get_http_response(self, serializer,
                     status=HTTP_200_OK, headers=None, first_answer=False):
        #pylint:disable=protected-access,arguments-differ
        scored_answers = get_scored_answers(
            Consumption.objects.get_active_by_accounts(
                self.sample.survey, excludes=self._get_filter_out_testing()),
            self.question.default_metric_id,
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
    """
    Retrieve a sample

    Providing {sample} is a set of datapoints for {interviewee}, returns
    a subset of datapoints whose question starts with a {path} prefix.

    **Tags**: survey

    **Examples**

    .. code-block:: http

         GET /api/steve-shop/sample/0123456789abcdef/water-use/ HTTP/1.1

    responds

    .. code-block:: json

        {
            "slug": "0123456789abcdef",
            "account": "steve-shop",
            "created_at": "2020-01-01T00:00:00Z",
            "is_frozen": true,
            "campaign": null,
            "time_spent": null,
            "answers": []
        }
    """
    account_url_kwarg = 'interviewee'

    def delete(self, request, *args, **kwargs):
        """
        Resets all answers whose question's path starts with a specified prefix.

        **Examples

        .. code-block:: http

            DELETE /api/steve-shop/sample/0123456789abcdef/water-use/ HTTP/1.1
        """
        return self.destroy(request, *args, **kwargs)

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

    def destroy(self, request, *args, **kwargs):
        prefix = kwargs.get('path', '')
        if prefix:
            queryset = Answer.objects.filter(
                sample=self.sample,
                question__path__startswith=prefix)
            queryset.delete()
            _, trail = self.breadcrumbs
            segment = trail[0][1] if trail else None
            if segment:
                nb_questions = Consumption.objects.filter(
                    path__startswith=segment).count()
                nb_answers = Answer.objects.filter(sample=self.sample,
                    question__path__startswith=segment).count()
                data = {'nb_answers': nb_answers, 'nb_questions': nb_questions}
                return http.Response(data, status=HTTP_200_OK)
            return http.Response(data, status=HTTP_204_NO_CONTENT)
        return super(AssessmentAPIView, self).destroy(request, *args, **kwargs)


class AssessmentMeasuresAPIView(ReportMixin, SampleMixin, ListCreateAPIView):
    """
    Adds a measurement or comment to an answer.

    **Tags**: survey

    **Examples

    .. code-block:: http

        POST /api/energy-utility/sample/724bf9648af6420ba79c8a37f962e97e/\
3/measures/ HTTP/1.1

    .. code-block:: json

        {}

    responds

    .. code-block:: json

        {}
    """
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
        errors = []
        for datapoint in serializer.validated_data['measures']:
            measured = datapoint.get('measured', None)
            try:
                with transaction.atomic():
                    metric = datapoint.get(
                        'metric', self.question.default_metric)
                    unit = datapoint.get('unit', metric.unit)
                    if unit.system in Unit.NUMERICAL_SYSTEMS:
                        try:
                            try:
                                measured = str(int(measured))
                            except ValueError:
                                measured = '{:.0f}'.format(
                                    decimal.Decimal(measured))
                            Answer.objects.update_or_create(
                                sample=self.sample, question=self.question,
                                metric=metric, defaults={
                                    'measured': int(measured),
                                    'unit': unit,
                                    'created_at': created_at,
                                    'collected_by': self.request.user,
                                    'rank': rank})
                        except (ValueError,
                            decimal.InvalidOperation, DataError) as err:
                            # We cannot convert to integer (ex: "12.8kW/h")
                            # or the value exceeds 32-bit representation.
                            # XXX We store as a text value so it is not lost.
                            LOGGER.warning(
                                "\"%(measured)s\": %(err)s for '%(metric)s'" % {
                                'measured': measured.replace('"', '\\"'),
                                'err': str(err).strip(),
                                'metric': metric.title})
                            unit = Unit.objects.get(slug='freetext')

                    if unit.system not in Unit.NUMERICAL_SYSTEMS:
                        if unit.system != Unit.SYSTEM_ENUMERATED:
                            choice_rank = Choice.objects.filter(
                                unit=unit).aggregate(Max('rank')).get(
                                    'rank__max', 0)
                            choice_rank = choice_rank + 1 if choice_rank else 1
                            choice = Choice.objects.create(
                                text=measured,
                                unit=unit,
                                rank=choice_rank)
                            measured = choice.pk
                        Answer.objects.update_or_create(
                            sample=self.sample, question=self.question,
                            metric=metric, defaults={
                                'measured': measured,
                                'unit': unit,
                                'created_at': created_at,
                                'collected_by': self.request.user,
                                'rank': rank})
            except DataError as err:
                LOGGER.exception(err)
                errors += [
                    "\"%(measured)s\": %(err)s for '%(metric)s'" % {
                        'measured': measured.replace('"', '\\"'),
                        'err': str(err).strip(),
                        'metric': metric.title}
                ]
        if errors:
            raise ValidationError(errors)


class DestroyMeasureAPIView(SampleMixin, DestroyAPIView):
    """
    Deletes a comment or reported measure on an assessment.

    **Tags**: survey

    **Examples

    .. code-block:: http

        DELETE /api/supplier1/sample/abcdef1234567/1/measures/comments/ HTTP/1.1
    """
    serializer_class = NoModelSerializer

    def get_object(self):
        measures = Answer.objects.filter(
            sample=self.sample,
            sample__is_frozen=False,
            metric__slug=self.kwargs.get('metric'))
        return measures
