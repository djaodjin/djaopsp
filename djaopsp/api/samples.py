# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import logging

from dateutil.relativedelta import relativedelta
from django.db.models import Count, F
from rest_framework import generics, response as http
from survey.api.sample import SampleCandidatesMixin, SampleAnswersMixin
from survey.models import Answer, Sample, Unit, UnitEquivalences

from ..compat import six
from ..mixins import ReportMixin, VisibilityMixin
from ..scores import get_score_calculator
from .campaigns import CampaignContentMixin
from .serializers import (AssessmentContentSerializer, AssessmentNodeSerializer,
    UnitSerializer)


LOGGER = logging.getLogger(__name__)


class AssessmentContentAPIView(ReportMixin, CampaignContentMixin,
                               SampleCandidatesMixin, SampleAnswersMixin,
                               generics.ListAPIView):
    """
    Lists measurements from a sample

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
                        "slug": "assessments",
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
                        "slug": "assessments",
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
                        "slug": "assessments",
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
    # The order ReportMixin followed by CampaignContentMixin is important
    # because we want `campaign` and `segments_available` from ReportMixin
    # to override the definitions in CampaignContentMixin.
    serializer_class = AssessmentContentSerializer

    @property
    def campaign(self):
        if not hasattr(self, '_campaign'):
            self._campaign = self.sample.campaign
        return self._campaign

    def attach_answers(self, values_by_path, queryset, key='answers'):
        for resp in queryset:
            # First we gather all information required
            # to display the question properly.
            question = resp.question
            path = question.path
            value = values_by_path.get(path)
            if not value:
                default_unit = question.default_unit
                value = {
                    'path': path,
                    'rank': resp.rank,
                    'required': resp.required,
                    'default_unit': default_unit,
                    'ui_hint': question.ui_hint,
                }
                values_by_path.update({path: value})
                self.units.update({default_unit.slug: default_unit})
            if resp.pk:
                # We have an actual answer to the question,
                # so let's populate it.
                answers = value.get(key, [])
                answers += [{
                    'measured': resp.measured_text,
                    'unit': resp.unit,
                    'created_at': resp.created_at,
                    'collected_by': resp.collected_by,
                }]
                self.units.update({resp.unit.slug: resp.unit})
                if key not in value:
                    value.update({key: answers})
        # We re-order the answers so the default_unit (i.e. primary)
        # is first.
        for question in six.itervalues(values_by_path):
            default_units = [question.get('default_unit')]
            if (question.get('default_unit').system
                in Unit.NUMERICAL_SYSTEMS):
                equiv_qs = UnitEquivalences.objects.filter(
                    source__slug=default_units[0].slug).values_list(
                    'target', flat=True)
                default_units += list(equiv_qs)
            primary = None
            remainders = []
            for answer in question.get(key, []):
                if answer.get('unit') in default_units:
                    primary = answer
                else:
                    remainders += [answer]
            if not primary:
                primary = {
                    'measured': None,
                    'unit': default_units[0],
                }
            question.update({key: [primary] + remainders})

    def attach_results(self, values_by_path, prefix):
        """
        Attach aggregated result to practices
        """
        #pylint:disable=too-many-locals
        ends_at = self.sample.created_at + relativedelta(months=1)
        last_frozen_assessments = \
            Sample.objects.get_latest_frozen_by_accounts(
                self.sample.campaign, before=ends_at)

        # total number of answers
        for row in Answer.objects.filter(
                question__path__startswith=prefix,
                unit_id=F('question__default_unit_id'),
                sample_id__in=last_frozen_assessments).values(
                'question__path').annotate(Count('sample_id')):
            question_key = row['question__path']
            count = row['sample_id__count']
            value = values_by_path.get(question_key, {'path': question_key})
            value.update({'nb_respondents': count})
            if question_key not in values_by_path:
                values_by_path.update({question_key: value})

        # per-choice number of answers
        for row in Answer.objects.filter(
                question__path__startswith=prefix,
                question__default_unit__system=Unit.SYSTEM_ENUMERATED,
                unit_id=F('question__default_unit_id'),
                unit__enums__id=F('measured'),
                sample_id__in=last_frozen_assessments).values(
                'question__path', 'measured', 'unit__enums__text').annotate(
                Count('sample_id')):
            question_key = row['question__path']
            count = row['sample_id__count']
            measured = row['unit__enums__text']
            value = values_by_path.get(question_key, {'path': question_key})
            total = value.get('nb_respondents', None)
            rate = value.get('rate', {})
            rate.update({
                measured: (int(count * 100 // total) if total else 0)})
            if 'rate' not in value:
                value.update({'rate': rate})
            if question_key not in values_by_path:
                values_by_path.update({question_key: value})

        # opportunity to improve score
        assessment_units_qs = Unit.objects.filter(
            system=Unit.SYSTEM_ENUMERATED,
            question__path__startswith=prefix,
            question__campaigns=self.sample.campaign).annotate(
                nb_questions=Count('question__id')).order_by(
            '-nb_questions')
        assessment_unit_id = assessment_units_qs.values_list(
            'id', flat=True).first()
        score_calculator = get_score_calculator(prefix)
        for row in score_calculator.get_opportunity(last_frozen_assessments,
                prefix=prefix, includes=[self.sample]):
            question_key = row['question__path']
            opportunity = row.get('opportunity', 0)
            value = values_by_path.get(question_key, {})
            value.update({'opportunity': opportunity})
            if question_key not in values_by_path:
                values_by_path.update({question_key: value})

    def get_planned(self, prefix):
        return []

    def get_questions(self, prefix):
        """
        Overrides CampaignContentMixin.get_questions to return a list
        of questions based on the answers available in the sample.
        """
        if not prefix.endswith(self.DB_PATH_SEP):
            prefix = prefix + self.DB_PATH_SEP

        values_by_path = {}
        self.attach_answers(
            values_by_path,
            self.get_answers(prefix=prefix, sample=self.sample))

        if not self.sample.is_frozen:
            self.attach_answers(
                values_by_path,
                self.get_candidates(prefix=prefix),
                key='candidates')

        self.attach_results(values_by_path, prefix)

        # Adds planned improvements
        self.attach_answers(
            values_by_path,
            self.get_planned(prefix=prefix),
            key='planned')
        return list(six.itervalues(values_by_path))

    def get_serializer_context(self):
        context = super(AssessmentContentAPIView, self).get_serializer_context()
        context.update({
            'prefix': self.db_path if self.db_path else self.DB_PATH_SEP
        })
        return context

    def list(self, request, *args, **kwargs):
        self.units = {}
        queryset = self.filter_queryset(self.get_queryset())

        serializer = AssessmentNodeSerializer(
            queryset, many=True, context=self.get_serializer_context())
        return http.Response(self.get_serializer_class()(
            context=self.get_serializer_context()).to_representation({
                'count': len(serializer.data),
                'results': serializer.data,
                'units': {key: UnitSerializer().to_representation(val)
                    for key, val in six.iteritems(self.units)}
            }))
