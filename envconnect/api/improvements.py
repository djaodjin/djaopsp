# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from django.db import transaction

from rest_framework import response as http
from rest_framework import status
from rest_framework.generics import (get_object_or_404, ListAPIView,
     GenericAPIView)
from rest_framework.mixins import (CreateModelMixin, RetrieveModelMixin,
    DestroyModelMixin, UpdateModelMixin)
from rest_framework.response import Response
from survey.api.sample import AnswerAPIView
from survey.api.serializers import AnswerSerializer
from survey.models import EnumeratedQuestions, get_question_model

from ..mixins import ImprovementQuerySetMixin
from ..models import Consumption
from ..scores import freeze_scores


class ImprovementListAPIView(ImprovementQuerySetMixin, ListAPIView):
    """
    List improvements

    **Tags**: survey

    **Examples**

    .. code-block:: http

         GET /api/xia/improvement HTTP/1.1

    responds

    .. code-block:: json

        {
            "count": 2,
            "previous": null,
            "next": null,
            "results": [
                {
                    "created_at": "2020-01-01T00:00:00Z",
                    "measured": 12,
                    "consumption": "water-use"
                },
            "results": [
                {
                    "created_at": "2020-01-01T00:00:00Z",
                    "measured": 10,
                    "consumption": "gas-emissions"
                }
            ]
        }
    """
    serializer_class = AnswerSerializer

    def get_serializer_context(self):
        """
        Provides a list of opportunities, one for each ``Question``.
        """
        context = super(ImprovementListAPIView, self).get_serializer_context()
# XXX This code does not seem to be used since ``with_opportunity`` changed
# prototype a while ago. ``_get_filter_out_testing`` also returns accounts
# instead of samples now.
#        context.update({'opportunities': Consumption.objects.with_opportunity(
#            filter_out_testing=self._get_filter_out_testing())})
        return context


class ImprovementAnswerAPIView(ImprovementQuerySetMixin, AnswerAPIView):
    """
    Retrieves a single improvement

    implementation rate, nb respondents
    "implemented by you?"
    opportunity score
    selected from improvement

    **Tags**: survey

    **Examples

    .. code-block:: http

        GET /api/xia/improvement/1/ HTTP/1.1

    """
    serializer_class = AnswerSerializer

    @property
    def sample(self):
        return self.improvement_sample

    def get_object(self):
        return get_object_or_404(self.get_queryset(),
            question__path=self.kwargs.get('path'))

    @property
    def question(self):
        if not hasattr(self, '_question'):
            self._question = get_object_or_404(
                get_question_model().objects.all(),
                path=self.kwargs.get('path'))
        return self._question

    def get_serializer_context(self):
        context = super(ImprovementAnswerAPIView, self).get_serializer_context()
        context.update({'question': self.question})
        return context

    def destroy(self, request, *args, **kwargs):
        # get_queryset() will filter by `account`. We filter by `path`
        # as in `get_object`. It should return a single result but
        # in case the db was corrupted, let's just fix it on the fly here.
        # XXX In the future the improvements must relate to a specific year.
        self.get_queryset().filter(
            question__path=self.kwargs.get('path')).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, *args, **kwargs):
        """
        Removes a single improvement

        **Tags**: survey

        **Examples

        .. code-block:: http

            DELETE /api/xia/improvement/1/ HTTP/1.1

        """
        return self.destroy(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Adds a single improvement

        **Tags**: survey

        **Examples

        .. code-block:: http

            POST /api/xia/improvement/1/ HTTP/1.1

        """
        return self.create(request, *args, **kwargs)
