# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import copy, logging, json
from collections import OrderedDict

from dateutil.relativedelta import relativedelta
from deployutils.crypt import JSONEncoder
from deployutils.helpers import datetime_or_now
from django.db import transaction
from django.db.models import Count, F
from pages.models import PageElement, flatten_content_tree
from rest_framework import generics, response as http, status as http_status
from rest_framework.exceptions import ValidationError
from survey.api.sample import (SampleCandidatesMixin, SampleAnswersMixin,
    SampleFreezeAPIView)
from survey.mixins import TimersMixin
from survey.models import Answer, Choice, Sample, Unit, UnitEquivalences
from survey.utils import get_account_model

from ..compat import reverse, six
from ..mixins import AccountMixin, SectionReportMixin
from ..models import ScorecardCache
from ..scores import freeze_scores, get_score_calculator
from ..utils import get_practice_serializer, get_scores_tree, get_score_weight
from .campaigns import CampaignContentMixin
from .rollups import GraphMixin, RollupMixin, ScoresMixin
from .serializers import (AssessmentContentSerializer, AssessmentNodeSerializer,
    BenchmarkSerializer, HistoricalAssessmentSerializer, UnitSerializer)


LOGGER = logging.getLogger(__name__)


class AssessmentCompleteAPIView(SectionReportMixin, TimersMixin,
                                SampleFreezeAPIView):

    def post(self, request, *args, **kwargs):
        """
        Freezes part of sample

        A frozen sample cannot be edited to add and/or update answers.

        **Tags**: assessments

        **Examples

        .. code-block:: http

            POST /api/supplier-1/sample/0123456789abcdef/freeze/construction \
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
        return super(AssessmentCompleteAPIView, self).post(
            request, *args, **kwargs)


    def populate_scorecard_cache(self, sample, calculator,
                                 segment_path, segment_title):
        LOGGER.info("populate %s scorecard cache for %s based of sample %s",
            sample.account, segment_path, str(sample))
        scorecards = calculator.get_scorecards(
                sample.campaign, segment_path, title=segment_title,
                includes=[sample], bypass_cache=True)
        # XXX fixes highlights that were not set.
        for scorecard in scorecards:
            if scorecard.reporting_publicly is None:
                scorecard.reporting_publicly = False
            if scorecard.reporting_fines is None:
                scorecard.reporting_fines = False
            if scorecard.reporting_environmental_fines is None:
                scorecard.reporting_environmental_fines = False
            if scorecard.reporting_energy_consumption is None:
                scorecard.reporting_energy_consumption = False
            if scorecard.reporting_water_consumption is None:
                scorecard.reporting_water_consumption = False
            if scorecard.reporting_ghg_generated is None:
                scorecard.reporting_ghg_generated = False
            if scorecard.reporting_waste_generated is None:
                scorecard.reporting_waste_generated = False
            if scorecard.reporting_energy_target is None:
                scorecard.reporting_energy_target = False
            if scorecard.reporting_water_target is None:
                scorecard.reporting_water_target = False
            if scorecard.reporting_ghg_target is None:
                scorecard.reporting_ghg_target = False
            if scorecard.reporting_waste_target is None:
                scorecard.reporting_waste_target = False
            if scorecard.nb_planned_improvements is None:
                scorecard.nb_planned_improvements = 0
            if scorecard.nb_na_answers is None:
                scorecard.nb_na_answers = 0
            if scorecard.normalized_score is None:
                scorecard.normalized_score = 0

        ScorecardCache.objects.bulk_create(scorecards)


    def create(self, request, *args, **kwargs):
        self._start_time()
        created_at = datetime_or_now()

        if self.nb_required_answers < self.nb_required_questions:
            raise ValidationError({'detail':
                "You have only answered %d of the %d required practices." % (
                self.nb_required_answers, self.nb_required_questions)})

        frozen_assessment_sample = None
        frozen_improvement_sample = None
        with transaction.atomic():
            for seg in self.segments_available:
                segment_path = seg.get('path')
                frozen_assessment_sample = freeze_scores(
                    self.sample,
                    created_at=created_at,
                    collected_by=self.request.user,
                    segment_path=segment_path,
                    score_sample=frozen_assessment_sample)

                if (self.improvement_sample and
                    self.improvement_sample.answers.exists()):
                    frozen_improvement_sample = freeze_scores(
                        self.improvement_sample,
                        created_at=created_at,
                        collected_by=self.request.user,
                        segment_path=segment_path,
                        score_sample=frozen_improvement_sample)
            self._report_queries("freezing assessment: %s completed" %
                str(frozen_assessment_sample))

            # Populate the scorecard caches
            for segment in self.segments_available:
                segment_path = segment.get('path')
                if segment_path:
                    calculator = get_score_calculator(segment_path)
                    if calculator:
                        segment_title = segment.get('title')
                        self.populate_scorecard_cache(
                            frozen_assessment_sample, calculator,
                            segment_path, segment_title)
            self._report_queries("freezing assessment: scorecard cache created")

        # Next step in the assessment. After complete, scorecard is optional.
        next_url = reverse('share', args=(
            frozen_assessment_sample.account, frozen_assessment_sample))
        frozen_assessment_sample.location = self.request.build_absolute_uri(
            next_url)

        serializer = self.get_serializer(instance=frozen_assessment_sample)
        return http.Response(
            serializer.data, status=http_status.HTTP_201_CREATED)


class AssessmentCompleteIndexAPIView(AssessmentCompleteAPIView):

    def post(self, request, *args, **kwargs):
        """
        Freezes a sample

        A frozen sample cannot be edited to add and/or update answers.

        **Tags**: assessments

        **Examples

        .. code-block:: http

            POST /api/supplier-1/sample/0123456789abcdef/freeze HTTP/1.1

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
        return super(AssessmentCompleteIndexAPIView, self).post(
            request, *args, **kwargs)


class AssessmentContentMixin(SectionReportMixin, CampaignContentMixin,
                             SampleCandidatesMixin, SampleAnswersMixin):

    practice_serializer_class = get_practice_serializer()

    @property
    def exclude_questions(self):
        if not hasattr(self, '_exclude_questions'):
            self._exclude_questions = []
        return self._exclude_questions


    def attach_results(self, questions_by_key, prefix):
        """
        Attach aggregated result to practices
        """
        #pylint:disable=too-many-locals

        # We cannot use the prefix here because some questions might
        # have been dropped from the assessment. As a result we use
        # `questions_by_key.keys()` because it will contain all the
        # relevant questions, whever the sample is frozen or not.

        ends_at = self.sample.created_at + relativedelta(months=1)
        last_frozen_assessments = \
            Sample.objects.get_latest_frozen_by_accounts(
                self.sample.campaign, before=ends_at)

        # total number of answers
        for row in Answer.objects.filter(
                question__in=questions_by_key.keys(),
                unit_id=F('question__default_unit_id'),
                sample_id__in=last_frozen_assessments).values(
                'question__id', 'question__path').annotate(Count('sample_id')):
            path = row['question__path']
            question_pk = row['question__id']
            count = row['sample_id__count']
            value = questions_by_key.get(question_pk, {'path': path})
            value.update({'nb_respondents': count})
            if question_pk not in questions_by_key:
                questions_by_key.update({question_pk: value})

        # per-choice number of answers
        for row in Answer.objects.filter(
                question__in=questions_by_key.keys(),
                unit_id=F('question__default_unit_id'),
                sample_id__in=last_frozen_assessments,
                question__default_unit__system=Unit.SYSTEM_ENUMERATED,
                unit__enums__id=F('measured')).values(
                'question__id', 'question__path',
                'measured', 'unit__enums__text').annotate(
                Count('sample_id')):
            path = row['question__path']
            question_pk = row['question__id']
            count = row['sample_id__count']
            measured = row['unit__enums__text']
            value = questions_by_key.get(question_pk, {'path': path})
            total = value.get('nb_respondents', None)
            rate = value.get('rate', {})
            rate.update({
                measured: (int(count * 100 // total) if total else 0)})
            if 'rate' not in value:
                value.update({'rate': rate})
            if question_pk not in questions_by_key:
                questions_by_key.update({question_pk: value})

        # opportunity to improve score
        score_calculator = get_score_calculator(prefix)
        if score_calculator:
            for row in score_calculator.get_opportunity(
                    self.campaign,
                    includes=[self.sample], prefix=prefix,
                    last_frozen_assessments=last_frozen_assessments):
                question_pk = row['question_id']
                opportunity = row.get('opportunity', 0)
                if question_pk in questions_by_key:
                    # If through other samples we find an opportunity value
                    # to a question which was not answered, or is not
                    # in the current campaign, then we discard it because
                    # we do not have an associated path for that question
                    # later on.
                    value = questions_by_key.get(question_pk)
                    value.update({'opportunity': opportunity})

    def get_planned(self, prefix):
        if not self.improvement_sample:
            return []
        return self.get_answers(
            prefix=prefix, sample=self.improvement_sample,
            excludes=self.exclude_questions)

    def get_questions(self, prefix):
        """
        Overrides CampaignContentMixin.get_questions to return a list
        of questions based on the answers available in the sample.
        """
        if not prefix.endswith(self.DB_PATH_SEP):
            prefix = prefix + self.DB_PATH_SEP

        extra_fields = getattr(
            self.practice_serializer_class.Meta, 'extra_fields', [])
        units = {}
        questions_by_key = {}
        attach_answers(
            units,
            questions_by_key,
            self.get_answers(prefix=prefix, sample=self.sample,
                excludes=self.exclude_questions),
            extra_fields=extra_fields)

        if not self.sample.is_frozen:
            attach_answers(
                units,
                questions_by_key,
                self.get_candidates(prefix=prefix,
                    excludes=self.exclude_questions),
                extra_fields=extra_fields,
                key='candidates')

        self.attach_results(questions_by_key, prefix)

        # Adds planned improvements
        attach_answers(
            units,
            questions_by_key,
            self.get_planned(prefix=prefix),
            extra_fields=extra_fields,
            key='planned')

        if not hasattr(self, 'units'):
            self.units = {}
        self.units.update(units)

        return list(six.itervalues(questions_by_key))


    def get_queryset(self):
        queryset = super(AssessmentContentMixin, self).get_queryset()

        # We will add the normalized_score here
        scores_by_path = {}
        for seg in self.segments_available:
            segment_path =seg.get('path')
            title = seg.get('title')
            score_calculator = get_score_calculator(segment_path)
            if score_calculator:
                for scorecard_cache in score_calculator.get_scorecards(
                        self.campaign, segment_path, title=title,
                        includes=[self.sample]):
                    scores_by_path[scorecard_cache.path] = scorecard_cache

        for row in queryset:
            path = row.get('path')
            scorecard_cache = scores_by_path.get(path)
            if scorecard_cache:
                row.update({
                    'normalized_score': scorecard_cache.normalized_score,
                    'score_weight': get_score_weight(
                        self.campaign, scorecard_cache.path)
                })

        return queryset


class AssessmentContentAPIView(AssessmentContentMixin, generics.ListAPIView):
    """
    Lists part of an assessment

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

         GET /api/andy-shop/sample/f1e2e916eb494b90f9ff0a36982342/content/sustainability HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 4,
          "results": [
            {
              "count": 1,
              "slug": "sustainability",
              "path": "/sustainability",
              "indent": 0,
              "title": "Core Environment, Social and Governance (ESG) Assessment",
              "picture": null,
              "extra": {
                "pagebreak": true,
                "tags": [
                  "scorecard"
                ],
                "visibility": [
                  "public"
                ],
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": null,
              "environmental_value": null,
              "business_value": null,
              "profitability": null,
              "implementation_ease": null,
              "rank": -1,
              "required": false,
              "default_unit": null,
              "ui_hint": null,
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            },
            {
              "count": 1,
              "slug": "governance",
              "path": "/sustainability/governance",
              "indent": 1,
              "title": "Strategy & Governance",
              "picture": "/tspproject/static/img/management-basics.png",
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
              "count": 1,
              "avg_value": null,
              "environmental_value": null,
              "business_value": null,
              "profitability": null,
              "implementation_ease": null,
              "rank": 1,
              "required": false,
              "default_unit": null,
              "ui_hint": null,
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            },
            {
              "count": 1,
              "slug": "esg-strategy-heading",
              "path": "/sustainability/governance/esg-strategy-heading",
              "indent": 2,
              "title": "Environment, Social & Governance (ESG) Strategy",
              "picture": null,
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": null,
              "environmental_value": null,
              "business_value": null,
              "profitability": null,
              "implementation_ease": null,
              "rank": 1,
              "required": false,
              "default_unit": null,
              "ui_hint": null,
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            },
            {
              "count": 1,
              "slug": "formalized-esg-strategy",
              "path": "/sustainability/governance/esg-strategy-heading/formalized-esg-strategy",
              "indent": 3,
              "title": "(3) Does your company have a formalized ESG strategy and performance targets that: 1/ Define a future vision of ESG performance, 2/ Are clear, actionable, and achievable, 3/ Are resourced effectively, 4/ Address material issues for the business?",
              "picture": "/tspproject/static/img/management-basics.png",
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": 0,
              "environmental_value": 1,
              "business_value": 1,
              "profitability": 1,
              "implementation_ease": 1,
              "rank": 4,
              "required": true,
              "default_unit": {
                "slug": "yes-no",
                "title": "Yes/No",
                "system": "enum",
                "choices": [
                  {
                    "text": "Yes",
                    "descr": "Yes"
                  },
                  {
                    "text": "No",
                    "descr": "No"
                  }
                ]
              },
              "ui_hint": "yes-no-comments",
              "answers": [],
              "candidates": [],
              "planned": [],
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            }
          ]
        }
    """
    exclude_param = 'e'
    serializer_class = AssessmentContentSerializer

    @property
    def exclude_questions(self):
        if not hasattr(self, '_exclude_questions'):
            self._exclude_questions = self.request.query_params.get(
                self.exclude_param)
        return self._exclude_questions

    def get_serializer_context(self):
        context = super(AssessmentContentAPIView, self).get_serializer_context()
        context.update({
            'prefix': self.db_path if self.db_path else self.DB_PATH_SEP,
        })
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Ready to serialize
        serializer = AssessmentNodeSerializer(
            queryset, many=True, context=self.get_serializer_context())
        if not hasattr(self, 'units'):
            self.units = {}
        return http.Response(self.get_serializer_class()(
            context=self.get_serializer_context()).to_representation({
                'count': len(serializer.data),
                'results': serializer.data,
                'units': {key: UnitSerializer().to_representation(val)
                    for key, val in six.iteritems(self.units)}
            }))


class AssessmentContentIndexAPIView(AssessmentContentAPIView):
    """
    Lists an assessment

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

         GET /api/andy-shop/sample/f1e2e916eb494b90f9ff0a36982342/content HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 4,
          "results": [
            {
              "count": 1,
              "slug": "sustainability",
              "path": "/sustainability",
              "indent": 0,
              "title": "Core Environment, Social and Governance (ESG) Assessment",
              "picture": null,
              "extra": {
                "pagebreak": true,
                "tags": [
                  "scorecard"
                ],
                "visibility": [
                  "public"
                ],
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": null,
              "environmental_value": null,
              "business_value": null,
              "profitability": null,
              "implementation_ease": null,
              "rank": -1,
              "required": false,
              "default_unit": null,
              "ui_hint": null,
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            },
            {
              "count": 1,
              "slug": "governance",
              "path": "/sustainability/governance",
              "indent": 1,
              "title": "Strategy & Governance",
              "picture": "/tspproject/static/img/management-basics.png",
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": null,
              "environmental_value": null,
              "business_value": null,
              "profitability": null,
              "implementation_ease": null,
              "rank": 1,
              "required": false,
              "default_unit": null,
              "ui_hint": null,
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            },
            {
              "count": 1,
              "slug": "esg-strategy-heading",
              "path": "/sustainability/governance/esg-strategy-heading",
              "indent": 2,
              "title": "Environment, Social & Governance (ESG) Strategy",
              "picture": null,
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": null,
              "environmental_value": null,
              "business_value": null,
              "profitability": null,
              "implementation_ease": null,
              "rank": 1,
              "required": false,
              "default_unit": null,
              "ui_hint": null,
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            },
            {
              "count": 1,
              "slug": "formalized-esg-strategy",
              "path": "/sustainability/governance/esg-strategy-heading/formalized-esg-strategy",
              "indent": 3,
              "title": "(3) Does your company have a formalized ESG strategy and performance targets that: 1/ Define a future vision of ESG performance, 2/ Are clear, actionable, and achievable, 3/ Are resourced effectively, 4/ Address material issues for the business?",
              "picture": "/tspproject/static/img/management-basics.png",
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
              "avg_value": 0,
              "environmental_value": 1,
              "business_value": 1,
              "profitability": 1,
              "implementation_ease": 1,
              "rank": 4,
              "required": true,
              "default_unit": {
                "slug": "yes-no",
                "title": "Yes/No",
                "system": "enum",
                "choices": [
                  {
                    "text": "Yes",
                    "descr": "Yes"
                  },
                  {
                    "text": "No",
                    "descr": "No"
                  }
                ]
              },
              "ui_hint": "yes-no-comments",
              "answers": [],
              "candidates": [],
              "planned": [],
              "nb_respondents": 0,
              "rate": {},
              "opportunity": null
            }
          ]
        }
    """


class HistoricalAssessmentsAPIView(AccountMixin, generics.ListAPIView):
    """
    Lists frozen samples

    Returns a list of frozen samples that belong to a profile. Typically this
    is a list of historical assessments.

    **Tags**: assessments

    **Examples**

    .. code-block:: http

         GET /api/andy-shop/samples HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 1,
          "previous": null,
          "next": null,
          "results": [{
            "slug": "dda134c8b4da487da9169e771794deed",
            "last_completed_at": "2016-07-15T00:35:26.565000Z",
            "campaign": {
              "slug": "sustainability",
              "account": "djaopsp",
              "title": "ESG/Environmental practices",
              "description": "ESG/Environmental practices assessment",
              "active": true
            }
          }]
        }
    """
    serializer_class = HistoricalAssessmentSerializer

    def get_queryset(self):
        return Sample.objects.filter(
            account=self.account,
            extra__isnull=True,
            is_frozen=True).order_by('-created_at').select_related('campaign')


class BenchmarkAPIView(SectionReportMixin, GraphMixin, RollupMixin,
                       ScoresMixin, generics.ListAPIView):
    """
    Retrieves benchmark graphs

    XXX change `resp` to a {count:, results:} format.

    Returns a list of graphs with anonymized performance of peers
    for paths marked as visible (see ::ref::`api_score`).

    **Tags**: scorecard

    **Examples

    .. code-block:: http

        GET /api/supplier-1/sample/ce6dc2c4cf6b40dbacef91fa3e934eed\
/benchmarks/boxes-enclosures HTTP/1.1

    responds

    .. code-block:: json

        [{
            "slug":"totals",
            "title":"Total Score",
            "nb_answers": 4,
            "nb_questions": 4,
            "nb_respondents": 2,
            "numerator": 12.0,
            "improvement_numerator": 8.0,
            "denominator": 26.0,
            "normalized_score": 46,
            "improvement_score": 30,
            "score_weight": 1.0,
            "highest_normalized_score": 88,
            "avg_normalized_score": 67,
            "created_at":"2017-08-02T20:18:19.089",
            "distribution": {
                "y": [0, 1, 0, 1],
                "x": ["0-25%", "25-50%", "50-75%", "75-100%"],
                "organization_rate":"25-50%"
            }
         },
         {
            "slug":"energy-efficiency-management-basics",
            "title":"Management",
            "text":"/media/envconnect/management-basics.png",
            "tag":"management",
            "score_weight":1.0
         },
         {
            "slug":"process-heating",
            "title":"Process heating",
            "text":"/media/envconnect/process-heating.png",
            "nb_questions": 4,
            "nb_answers": 4,
            "nb_respondents": 2,
            "numerator": 12.0,
            "improvement_numerator": 8.0,
            "denominator": 26.0,
            "normalized_score": 46,
            "improvement_score": 12,
            "highest_normalized_score": 88,
            "avg_normalized_score": 67,
            "created_at": "2017-08-02T20:18:19.089",
            "distribution": {
                "y": [0, 1, 0, 1],
                "x": [ "0-25%", "25-50%", "50-75%", "75-100%"],
                "organization_rate": "25-50%"
            },
            "score_weight": 1.0
         }]
    """
    serializer_class = BenchmarkSerializer
    pagination_class = None
    DB_PATH_SEP = '/'
    account_model = get_account_model()

    @property
    def requested_accounts_pk_as_sql(self):
        """
        Returns all accounts available as a string
        that can be used in SQL statements.
        """
        if not hasattr(self, '_requested_accounts_pk_as_sql'):
            self._requested_accounts_pk_as_sql = (
                "(SELECT id FROM %s)" % self.account_model._meta.db_table)
        return self._requested_accounts_pk_as_sql

    @property
    def scores_tree(self):
        if not hasattr(self, '_scores_tree'):
            self._scores_tree = OrderedDict()
            for seg in self.segments_available:
                segment_path = seg.get('path')
                prefix = self.DB_PATH_SEP.join(segment_path.split(
                    self.DB_PATH_SEP)[:-1])
                self._scores_tree.update(get_scores_tree(
                    [PageElement.objects.get(slug=seg['slug'])], prefix=prefix))
        return self._scores_tree

    @property
    def scores_of_interest(self):
        """
        Returns the segments/tiles we are interested in for this query.
        """
        if not hasattr(self, '_scores_of_interest'):
            self._scores_of_interest = flatten_content_tree(self.scores_tree)
        return self._scores_of_interest


    def list(self, request, *args, **kwargs):
        #pylint:disable=unused-argument,too-many-nested-blocks
        self._start_time()
        queryset = self.get_queryset()
        for score in queryset:
            if score.segment_path:
                self._insert_in_tree(
                    self.scores_tree, score.segment_path, score)
        self._report_queries("rollup_scores completed")
        self.create_distributions(
            self.scores_tree, view_account_id=self.account.pk)
        self._report_queries("create_distributions completed")
        charts, unused_segment_complete = self.flatten_distributions(
            self.scores_tree)
        self._report_queries("flatten_distributions completed")

        if not self.sample.is_frozen:
            for segment_path, segment_values in six.iteritems(self.scores_tree):
                title = segment_values[0].get('title')
                score_calculator = get_score_calculator(segment_path)
                if score_calculator:
                    for scorecard_cache in score_calculator.get_scorecards(
                            self.campaign, segment_path, title=title,
                            includes=[self.sample]):
                        for chart in charts:
                            path = chart.get('path')
                            if scorecard_cache.path == path:
                                chart.update({'normalized_score':
                                    scorecard_cache.normalized_score})
                                break
        self._report_queries("sample scorecard_cache computed")

        return http.Response(charts)


class BenchmarkIndexAPIView(BenchmarkAPIView):
    """
    Retrieves benchmark graphs

    Returns a list of graphs with anonymized performance of peers
    for paths marked as visible (see ::ref::`api_score`).

    **Tags**: scorecard

    **Examples

    .. code-block:: http

        GET /api/supplier-1/sample/ce6dc2c4cf6b40dbacef91fa3e934eed\
/benchmarks HTTP/1.1

    responds

    .. code-block:: json

        [{
            "slug":"totals",
            "title":"Total Score",
            "nb_answers": 4,
            "nb_questions": 4,
            "nb_respondents": 2,
            "numerator": 12.0,
            "improvement_numerator": 8.0,
            "denominator": 26.0,
            "normalized_score": 46,
            "improvement_score": 30,
            "score_weight": 1.0,
            "highest_normalized_score": 88,
            "avg_normalized_score": 67,
            "created_at":"2017-08-02T20:18:19.089",
            "distribution": {
                "y": [0, 1, 0, 1],
                "x": ["0-25%", "25-50%", "50-75%", "75-100%"],
                "organization_rate":"25-50%"
            }
         },
         {
            "slug":"energy-efficiency-management-basics",
            "title":"Management",
            "text":"/media/envconnect/management-basics.png",
            "tag":"management",
            "score_weight":1.0
         },
         {
            "slug":"process-heating",
            "title":"Process heating",
            "text":"/media/envconnect/process-heating.png",
            "nb_questions": 4,
            "nb_answers": 4,
            "nb_respondents": 2,
            "numerator": 12.0,
            "improvement_numerator": 8.0,
            "denominator": 26.0,
            "normalized_score": 46,
            "improvement_score": 12,
            "highest_normalized_score": 88,
            "avg_normalized_score": 67,
            "created_at": "2017-08-02T20:18:19.089",
            "distribution": {
                "y": [0, 1, 0, 1],
                "x": [ "0-25%", "25-50%", "50-75%", "75-100%"],
                "organization_rate": "25-50%"
            },
            "score_weight": 1.0
         }]
    """
    # XXX change `resp` to a {count:, results:} format.


def attach_answers(units, questions_by_key, queryset,
                   extra_fields=None, key='answers'):
    """
    Populates `units` and `questions_by_key` from a `queryset` of answers.
    """
    #pylint:disable=too-many-locals
    if extra_fields is None:
        extra_fields = []
    enum_units = {}
    for resp in queryset:
        # First we gather all information required
        # to display the question properly.
        question = resp.question
        path = question.path
        question_pk = question.pk
        value = questions_by_key.get(question_pk)
        if not value:
            default_unit = question.default_unit
            units.update({default_unit.slug: default_unit})
            if default_unit.system == Unit.SYSTEM_ENUMERATED:
                # Enum units might have a per-question choice description.
                # We try to reduce the number of database queries by
                # loading the unit choices here and the per-question choices
                # in a single pass later on.
                default_unit_dict = enum_units.get(default_unit.pk)
                if not default_unit_dict:
                    default_unit_dict = {
                        'slug': default_unit.slug,
                        'title': default_unit.title,
                    'system': default_unit.system,
                        'choices':[{
                            'pk': choice.pk,
                            'text': choice.text,
                    'descr': choice.descr if choice.descr else choice.text
                        } for choice in default_unit.choices]}
                    enum_units[default_unit.pk] = default_unit_dict
                default_unit = copy.deepcopy(default_unit_dict)
            value = {
                'path': path,
                'rank': resp.rank,
                'required': resp.required,
                'default_unit': default_unit,
                'ui_hint': question.ui_hint,
            }
            for field_name in extra_fields:
                value.update({field_name: getattr(question, field_name)})
            questions_by_key.update({question_pk: value})
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
            units.update({resp.unit.slug: resp.unit})
            if key not in value:
                value.update({key: answers})
    # We re-order the answers so the default_unit (i.e. primary)
    # is first.
    for question in six.itervalues(questions_by_key):
        default_unit = question.get('default_unit')
        if isinstance(default_unit, Unit):
            default_units = [default_unit.slug]
            if default_unit.system in Unit.NUMERICAL_SYSTEMS:
                equiv_qs = UnitEquivalences.objects.filter(
                    source__slug=default_unit.slug).values_list(
                    'target__slug', flat=True)
                default_units += list(equiv_qs)
        else:
            default_units = [default_unit.get('slug')]
        primary = []
        remainders = []
        for answer in question.get(key, []):
            if str(answer.get('unit')) in default_units:
                primary = [answer]
            else:
                remainders += [answer]
        question.update({key: primary + remainders})

    # Let's populate the per-question choices as necessary.
    # This is done in a single pass to reduce the number of db queries.
    for choice in Choice.objects.filter(
            question__in=questions_by_key,
            unit=F('question__default_unit')).order_by(
                'question', 'unit', 'rank'):
        default_unit = questions_by_key[choice.question_id].get(
            'default_unit')
        for default_unit_choice in default_unit.get('choices'):
            if choice.text == default_unit_choice.get('text'):
                default_unit_choice.update({'descr': choice.descr})
                break
