# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

import logging

from django.db.models import Q
from rest_framework import generics, response as http, status as http_status
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import UpdateModelMixin
from rest_framework.exceptions import ValidationError

from survey.api.serializers import AnswerSerializer
from survey.models import Answer, UnitEquivalences
from survey.queries import datetime_or_now
from survey.settings import DB_PATH_SEP
from survey.utils import get_question_model

from ..compat import is_authenticated, six
from ..models import VerifiedAnswer, VerifiedSample
from .serializers import AssessmentNodeSerializer, VerifiedSampleSerializer
from .samples import AssessmentContentMixin, attach_answers

LOGGER = logging.getLogger(__name__)


class VerifierNotesAPIView(AssessmentContentMixin, generics.ListCreateAPIView):
    """
    Lists answers

    The list returned contains at least one measurement for each question
    in the campaign. If there are no measurement yet on a question, ``measured``
    will be null.

    There might be more than one measurement per question as long as there are
    no duplicated ``unit`` per question. For example, to the question
    ``adjust-air-fuel-ratio``, there could be a measurement with unit
    ``assessment`` (Mostly Yes/ Yes / No / Mostly No) and a measurement with
    unit ``freetext`` (i.e. a comment).

    The {sample} must belong to {organization}.

    {path} can be used to filter the tree of questions by a prefix.

    **Tags**: assessments

    **Examples**

    .. code-block:: http

         GET /api/supplier-1/sample/46f66f70f5ad41b29c4df08f683a9a7a/answers\
/construction HTTP/1.1

    responds

    .. code-block:: json

    {
        "count": 3,
        "previous": null,
        "next": null,
        "results": [
            {
                "question": {
                    "path": "/construction/governance/the-assessment\
-process-is-rigorous",
                    "title": "The assessment process is rigorous",
                    "default_unit": {
                        "slug": "assessment",
                        "title": "assessments",
                        "system": "enum",
                        "choices": [
                        {
                            "rank": 1,
                            "text": "mostly-yes",
                            "descr": "Mostly yes"
                        },
                        {
                            "rank": 2,
                            "text": "yes",
                            "descr": "Yes"
                        },
                        {
                            "rank": 3,
                            "text": "no",
                            "descr": "No"
                        },
                        {
                            "rank": 4,
                            "text": "mostly-no",
                            "descr": "Mostly no"
                        }
                        ]
                    },
                    "ui_hint": "radio"
                },
                "required": true,
                "measured": "yes",
                "unit": "assessment",
                "created_at": "2020-09-28T00:00:00.000000Z",
                "collected_by": "steve"
            },
            {
                "question": {
                    "path": "/construction/governance/the-assessment\
-process-is-rigorous",
                    "title": "The assessment process is rigorous",
                    "default_unit": {
                        "slug": "assessment",
                        "title": "assessments",
                        "system": "enum",
                        "choices": [
                        {
                            "rank": 1,
                            "text": "mostly-yes",
                            "descr": "Mostly yes"
                        },
                        {
                            "rank": 2,
                            "text": "yes",
                            "descr": "Yes"
                        },
                        {
                            "rank": 3,
                            "text": "no",
                            "descr": "No"
                        },
                        {
                            "rank": 4,
                            "text": "mostly-no",
                            "descr": "Mostly no"
                        }
                        ]
                    },
                    "ui_hint": "radio"
                },
                "measured": "Policy document on the public website",
                "unit": "freetext",
                "created_at": "2020-09-28T00:00:00.000000Z",
                "collected_by": "steve"
            },
            {
                "question": {
                    "path": "/construction/production/adjust-air-fuel\
-ratio",
                    "title": "Adjust Air fuel ratio",
                    "default_unit": {
                        "slug": "assessment",
                        "title": "assessments",
                        "system": "enum",
                        "choices": [
                        {
                            "rank": 1,
                            "text": "mostly-yes",
                            "descr": "Mostly yes"
                        },
                        {
                            "rank": 2,
                            "text": "yes",
                            "descr": "Yes"
                        },
                        {
                            "rank": 3,
                            "text": "no",
                            "descr": "No"
                        },
                        {
                            "rank": 4,
                            "text": "mostly-no",
                            "descr": "Mostly no"
                        }
                        ]
                    },
                    "ui_hint": "radio"
                },
                "required": true,
                "measured": null,
                "unit": null
            }
         ]
    }
    """
    serializer_class = AssessmentNodeSerializer

    # Used to POST and create an answer.
    @property
    def question(self):
        #pylint:disable=attribute-defined-outside-init
        if not hasattr(self, '_question'):
            self._question = get_object_or_404(
                get_question_model().objects.all(), path=self.path)
        return self._question

    def get_questions(self, prefix):
        """
        Overrides CampaignContentMixin.get_questions to return a list
        of questions based on the answers available in the sample.
        """
        if not prefix.endswith(DB_PATH_SEP):
            prefix = prefix + DB_PATH_SEP

        extra_fields = getattr(
            self.practice_serializer_class.Meta, 'extra_fields', [])
        units = {}
        questions_by_key = {}
        attach_answers(
            units,
            questions_by_key,
            self.get_notes(prefix=prefix, sample=self.sample,
                excludes=self.exclude_questions),
            extra_fields=extra_fields,
            key='notes')

        return list(six.itervalues(questions_by_key))

    def get_serializer_class(self):
        if self.request.method.lower() == 'post':
            return AnswerSerializer
        return super(VerifierNotesAPIView, self).get_serializer_class()

    def get_serializer(self, *args, **kwargs):
        if isinstance(self.request.data, list):
            kwargs.update({'many': True})
        return super(VerifierNotesAPIView, self).get_serializer(
            *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Adds notes by verifier

        A frozen sample cannot be edited to add and/or update answers.

        **Tags**: assessments

        **Examples

        .. code-block:: http

            POST /api/supplier-1/sample/0123456789abcdef/notes/construction \
 HTTP/1.1

        .. code-block:: json

            {}

        responds

        .. code-block:: json

            {
              "slug": "0123456789abcdef",
              "account": "supplier-1",
              "created_at": "2020-01-01T00:00:00Z",
              "is_frozen": true,
              "campaign": null,
              "updated_at": "2020-01-01T00:00:00Z"
            }
        """
        #pylint:disable=useless-super-delegation
        return super(VerifierNotesAPIView, self).post(
            request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        #pylint:disable=unused-argument,too-many-locals,too-many-statements
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        if not isinstance(serializer.validated_data, list):
            validated_data = [serializer.validated_data]

        user = self.request.user if is_authenticated(self.request) else None
        created_at = datetime_or_now()
        at_least_one_created = False
        results = []
        errors = []

        for datapoint in validated_data:
            measured = datapoint.get('measured', None)
            if not measured:
                continue
            defaults = {
                'created_at': created_at,
                'verified_by': user,
                'text': measured
            }
            answer = Answer.objects.get(
                Q(unit=self.question.default_unit) |
                Q(unit__in=UnitEquivalences.objects.filter(
                    source=self.question.default_unit).values('target')),
                sample=self.sample,
                question=self.question)
            verified_answer, created = \
                VerifiedAnswer.objects.update_or_create(
                    defaults=defaults, answer=answer)
            results += [verified_answer]
            if created:
                at_least_one_created = True
        if errors:
            raise ValidationError(errors)

        serializer = self.get_serializer(results, many=True)
        headers = self.get_success_headers(serializer.data)
        return http.Response(serializer.data,
            status=http_status.HTTP_201_CREATED if at_least_one_created
                else http_status.HTTP_200_OK,
            headers=headers)


class VerifierNotesIndexAPIView(UpdateModelMixin, VerifierNotesAPIView):
    """
        Adds notes by verifier

        A frozen sample cannot be edited to add and/or update answers.

        **Tags**: assessments

        **Examples

        .. code-block:: http

            POST /api/supplier-1/sample/0123456789abcdef/notes/construction \
 HTTP/1.1

        .. code-block:: json

            {}

        responds

        .. code-block:: json

            {
              "slug": "0123456789abcdef",
              "account": "supplier-1",
              "created_at": "2020-01-01T00:00:00Z",
              "is_frozen": true,
              "campaign": null,
              "updated_at": "2020-01-01T00:00:00Z"
            }
    """

    def get_serializer_class(self):
        if self.request.method.lower() in ['put', 'patch']:
            return VerifiedSampleSerializer
        return super(VerifierNotesAPIView, self).get_serializer_class()

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Updates verified status

        Updates the verification status

        **Tags**: assessments

        **Examples

        .. code-block:: http

            PUT /api/supplier-1/sample/0123456789abcdef/notes \
 HTTP/1.1

        .. code-block:: json

            {
              "verified_status": ""
            }

        responds

        .. code-block:: json

            {
              "slug": "0123456789abcdef",
              "account": "supplier-1",
              "created_at": "2020-01-01T00:00:00Z",
              "is_frozen": true,
              "campaign": null,
              "updated_at": "2020-01-01T00:00:00Z"
            }
        """
        return self.update(request, *args, **kwargs)

    def get_object(self):
        #pylint:disable=unused-variable
        verified_sample, created = VerifiedSample.objects.update_or_create(
            defaults={'verified_by': self.request.user}, sample=self.sample)
        return verified_sample
