# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

import logging
from collections import OrderedDict

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.db.models import Q
from pages.docs import extend_schema
from pages.models import PageElement, flatten_content_tree
from rest_framework import generics, response as http, status as http_status
from rest_framework.exceptions import ValidationError
from survey.api.base import QuestionListAPIView
from survey.api.sample import (attach_answers,
    SampleCandidatesMixin, SampleAnswersMixin, SampleFreezeAPIView,
    SampleRecentCreateAPIView as SampleRecentCreateBaseAPIView)
from survey.api.matrix import (
    SampleBenchmarksAPIView as SampleBenchmarksBaseAPIView)
from survey.filters import OrderingFilter, SearchFilter
from survey.helpers import datetime_or_now
from survey.mixins import SampleMixin, TimersMixin
from survey.models import Sample
from survey.settings import DB_PATH_SEP
from survey.utils import get_account_model

from ..compat import gettext_lazy as _, reverse, six
from ..mixins import AccountMixin, SectionReportMixin
from ..models import VerifiedSample
from ..notifications.serializers import UserDetailSerializer
from ..pagination import BenchmarksPagination
from ..queries import get_scored_assessments
from ..reminders import send_reminders
from ..scores import (freeze_scores, get_score_calculator,
    get_top_normalized_score, populate_scorecard_cache)
from ..signals import sample_frozen
from ..utils import get_practice_serializer, get_scores_tree, get_score_weight
from .campaigns import CampaignDecorateMixin
from .rollups import GraphMixin, RollupMixin
from .serializers import (AssessmentNodeSerializer, RespondentAccountSerializer,
    ExtendedSampleSerializer, ExtendedSampleBenchmarksSerializer,
    UnitSerializer)


LOGGER = logging.getLogger(__name__)


class SampleNotesMixin(SampleMixin):

    def get_notes(self, prefix=None, excludes=None):
        """
        Returns verifier notes on a sample.

        The answers can be filtered such that only questions with a path
        starting by `prefix` are included. Questions included whose
        extra field does not contain `excludes` can be further removed
        from the results.
        """
        if not prefix:
            prefix = self.path
        verification = self.get_or_create_verification()
        if not verification:
            return []
        return self.get_answers(
            prefix=prefix, sample=verification.verifier_notes,
            excludes=excludes)


class AssessmentCompleteAPIView(SectionReportMixin, TimersMixin,
                                SampleFreezeAPIView):

    def post(self, request, *args, **kwargs):
        """
        Freezes answers matching prefix

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


    def get_prefixes(self):
        return [seg.get('path') for seg in self.segments_available
            if seg.get('path')]


    def create(self, request, *args, **kwargs):
        #pylint:disable=too-many-locals
        self._start_time()
        created_at = datetime_or_now()

        if self.sample.is_frozen:
            raise ValidationError({'detail': _("sample is already frozen")})

        prefixes = self.get_prefixes()
        if not prefixes:
            raise ValidationError({'detail':
                _("You cannot freeze a sample with no answers")})

        # All questions with required answers for which no answer is present.
        required_unanswered_questions = self.get_required_unanswered_questions(
            prefixes=prefixes)
        if required_unanswered_questions.exists():
            raise ValidationError({'detail': _("You have only answered"\
" %(nb_required_answers)d of the %(nb_required_questions)d required"\
" practices. Locate practices with a red vertical bar on the right side"\
" of the page. Then scroll back up to the section title, click 'Update' under"\
" the section title. Assess the missing practices, then come back"\
" to the 'REVIEW' step.") % {
    'nb_required_answers': self.nb_required_answers,
    'nb_required_questions': self.nb_required_questions},
                'results': list(required_unanswered_questions)})

        if not self.force:
            latest_completed = Sample.objects.filter(
                is_frozen=True,
                account=self.sample.account,
                campaign=self.sample.campaign,
                extra=self.sample.extra).order_by('created_at').first()
            if latest_completed:
                if self.sample.has_identical_answers(latest_completed):
                    raise ValidationError({'detail': _("This sample contains"\
                    " the same answers has the previously frozen sample.")})

        # freeze a verifier notes
        verified_sample = self.verification
        if verified_sample and self.sample == verified_sample.verifier_notes:
            # verification notes are just frozen. We don't create a copy.
            verified_sample.verified_by = self.request.user
            verified_sample.verified_status = \
                VerifiedSample.STATUS_REVIEW_COMPLETED
            verified_sample.verifier_notes.is_frozen = True
            with transaction.atomic():
                verified_sample.verifier_notes.save()
                verified_sample.save()
            serializer = self.get_serializer(
                instance=verified_sample.verifier_notes)
            return http.Response(
                serializer.data, status=http_status.HTTP_201_CREATED)

        # freeze sample
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
                        populate_scorecard_cache(
                            frozen_assessment_sample, calculator,
                            segment_path, segment_title)
            self._report_queries("freezing assessment: scorecard cache created")

        # After a sample is frozen, send the signal.
        sample_frozen.send(sender=self.__class__,
            sample=frozen_assessment_sample, request=request)

        # Next step in the assessment. After complete, scorecard is optional.
        next_url = reverse('share', args=(
            frozen_assessment_sample.account, frozen_assessment_sample))
        frozen_assessment_sample.location = self.request.build_absolute_uri(
            next_url)

        serializer = self.get_serializer(instance=frozen_assessment_sample)
        return http.Response(
            serializer.data, status=http_status.HTTP_201_CREATED)


class AssessmentCompleteIndexAPIView(AssessmentCompleteAPIView):

    @extend_schema(operation_id='sample_freeze_create_index')
    def post(self, request, *args, **kwargs):
        """
        Freezes answers

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


class AssessmentContentMixin(SectionReportMixin, CampaignDecorateMixin,
                             SampleNotesMixin, SampleCandidatesMixin,
                             SampleAnswersMixin):

    practice_serializer_class = get_practice_serializer()

    @property
    def exclude_questions(self):
        if not hasattr(self, '_exclude_questions'):
            self._exclude_questions = [] # Why we are not using
                 # `self.request.query_params.get(self.exclude_param)` here?
        return self._exclude_questions


    def get_decorated_questions(self, prefix=None):
        # XXX Because we do not derive from `QuestionListAPIView`.
        return list(six.itervalues(self.get_questions_by_key(
            prefix=prefix if prefix else DB_PATH_SEP)))


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
                self.sample.campaign, ends_at=ends_at, tags=[])

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

    def get_questions_by_key(self, prefix=None, initial=None):
        """
        Overrides CampaignContentMixin.get_questions to return a list
        of questions based on the answers available in the sample.
        """
        questions_by_key = initial if isinstance(initial, dict) else {}

        extra_fields = getattr(
            self.practice_serializer_class.Meta, 'extra_fields', [])
        units = {}
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

        elif self.verification_available:
            # Verification notes are only available to verifiers
            attach_answers(
                units,
                questions_by_key,
                self.get_notes(prefix=prefix,
                    excludes=self.exclude_questions),
                extra_fields=extra_fields,
                key='answers') # Implementation note: attaching the notes
                               # as 'answers' instead of 'notes' because
                               # so far they are distinct questions and
                               # it simplifies the Javascript client.

        # Attach scores
        calculator = get_score_calculator(prefix)
        if False and calculator:
            calculator_answers = calculator.get_scored_answers(
                self.sample.campaign, includes=[self.sample], prefix=prefix)
            attach_answers(
                units,
                questions_by_key,
                calculator_answers,
                extra_fields=extra_fields)

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

        return questions_by_key


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


class AssessmentContentAPIView(TimersMixin, AssessmentContentMixin,
                               QuestionListAPIView):
    """
    Formats answers matching prefix

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
              "title": "(3) Does your company have a formalized ESG strategy?",
              "picture": "/tspproject/static/img/management-basics.png",
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
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
    serializer_class = AssessmentNodeSerializer

    @property
    def exclude_questions(self):
        #pylint:disable=attribute-defined-outside-init
        if not hasattr(self, '_exclude_questions'):
            self._exclude_questions = self.request.query_params.get(
                self.exclude_param)
        return self._exclude_questions

    def get_serializer_context(self):
        context = super(AssessmentContentAPIView, self).get_serializer_context()
        context.update({
            'prefix': self.db_path if self.db_path else DB_PATH_SEP,
        })
        return context

    def list(self, request, *args, **kwargs):
        self._start_time()
        queryset = self.filter_queryset(self.get_queryset())

        # Ready to serialize
        serializer = self.get_serializer_class()(
            queryset, many=True, context=self.get_serializer_context())

        resp = self.get_paginated_response(serializer.data)
        self._report_queries("AssessmentContentAPIView.list done")
        return resp

    def get_paginated_response(self, data):
        if not hasattr(self, 'units'):
            #pylint:disable=attribute-defined-outside-init
            self.units = {}

        # Pick a top normalized_score:
        # If present, use the score for the mandatory segment,
        # otherwise take the maxium of segment scores.
        top_normalized_score = None
        if self.sample.is_frozen:
            top_normalized_score = get_top_normalized_score(self.sample)
        elif data:
            top_normalized_score = data[0].get('normalized_score')

        verified_sample = VerifiedSample.objects.filter(
            sample=self.sample).first()

        return http.Response(OrderedDict([
            ('count', len(data)),
            ('path', self.path),
            ('normalized_score', top_normalized_score),
            ('verified_status', VerifiedSample.STATUSES[
                verified_sample.verified_status if verified_sample
                else VerifiedSample.STATUS_NO_REVIEW][1]),
            ('results', data),
            ('units', {key: UnitSerializer().to_representation(val)
                    for key, val in six.iteritems(self.units)})
        ]))


class AssessmentContentIndexAPIView(AssessmentContentAPIView):
    """
    Formats answers

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
              "title": "(3) Does your company have a formalized ESG strategy?",
              "picture": "/tspproject/static/img/management-basics.png",
              "extra": {
                "segments": [
                  "/sustainability"
                ]
              },
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

    @extend_schema(operation_id='sample_content_index')
    def get(self, request, *args, **kwargs):
        return super(AssessmentContentIndexAPIView, self).get(
            request, *args, **kwargs)


class SampleBenchmarksAPIView(TimersMixin, GraphMixin, RollupMixin,
                              SectionReportMixin, CampaignDecorateMixin,
                              SampleBenchmarksBaseAPIView):
    """
    Benchmarks against all peers for a subset of questions

    Returns a list of graphs with anonymized performance of peers
    for paths marked as visible (see ::ref::`api_score`).

    **Tags**: benchmarks

    **Examples

    .. code-block:: http

        GET /api/supplier-1/sample/ce6dc2c4cf6b40dbacef91fa3e934eed\
/benchmarks/boxes-enclosures HTTP/1.1

    responds

    .. code-block:: json

        {
            "avg_normalized_score": 50,
            "highest_normalized_score": 100,
            "results": [{
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
                "avg_normalized_score": 67,
                "created_at":"2017-08-02T20:18:19.089",
                "distribution": {
                    "y": [0, 1, 0, 1],
                    "x": ["0-25%", "25-50%", "50-75%", "75-100%"]
                }
             },
             {
                "slug":"energy-efficiency-management-basics",
                "title":"Management",
                "text":"/media/djaopsp/management-basics.png",
                "tag":"management",
                "score_weight":1.0
             },
             {
                "slug":"process-heating",
                "title":"Process heating",
                "text":"/media/djaopsp/process-heating.png",
                "nb_questions": 4,
                "nb_answers": 4,
                "nb_respondents": 2,
                "numerator": 12.0,
                "improvement_numerator": 8.0,
                "denominator": 26.0,
                "normalized_score": 46,
                "improvement_score": 12,
                "avg_normalized_score": 67,
                "created_at": "2017-08-02T20:18:19.089",
                "distribution": {
                    "y": [0, 1, 0, 1],
                    "x": [ "0-25%", "25-50%", "50-75%", "75-100%"]
                },
                "score_weight": 1.0
             }]
        }
    """
    # XXX This class should inherit from
    # `survey.api.matrix.SampleBenchmarksIndexAPIView`, and add benchmarks
    # for scores.
    pagination_class = BenchmarksPagination
    account_model = get_account_model()
    serializer_class = ExtendedSampleBenchmarksSerializer

    @property
    def scores_tree(self):
        #pylint:disable=attribute-defined-outside-init
        if not hasattr(self, '_scores_tree'):
            self._scores_tree = OrderedDict()
            for seg in self.segments_available:
                segment_path = seg.get('path')
                prefix = DB_PATH_SEP.join(segment_path.split(DB_PATH_SEP)[:-1])
                self._scores_tree.update(get_scores_tree(
                    [PageElement.objects.get(slug=seg['slug'])], prefix=prefix))
        return self._scores_tree

    @property
    def scores_of_interest(self):
        """
        Returns the segments/tiles we are interested in for this query.
        """
        #pylint:disable=attribute-defined-outside-init
        if not hasattr(self, '_scores_of_interest'):
            self._scores_of_interest = flatten_content_tree(self.scores_tree)
        return self._scores_of_interest

    def list(self, request, *args, **kwargs):
        self._start_time()
        queryset = self.filter_queryset(self.get_queryset())
        self.decorate_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        self._report_queries("SampleBenchmarksAPIView.list done")
        return http.Response(serializer.data)


    def decorate_queryset(self, queryset):
        #pylint:disable=unused-argument,too-many-nested-blocks,too-many-locals
        # `queryset` is a list of questions

        accounts = None # XXX self.get_accessible_accounts()
        scored_assessments = get_scored_assessments(
            self.campaign, accounts=accounts,
            scores_of_interest=self.scores_of_interest, db_path=self.db_path,
            ends_at=self.ends_at)
        for score in scored_assessments:
            if score.segment_path:
                self._insert_in_tree(
                    self.scores_tree, score.segment_path, score)
        self._report_queries("frozen scorecards inserted")

        if not self.sample.is_frozen:
            # If we have a work-in-progress assessment, let's compute
            # the score as it would show up Today and insert it in the tree
            # such that `organization_rate` is computed correctly.
            # Note that if a previously frozen sample score already exists
            # it will be present in the tree. We need to override it.
            for segment_path, segment_values in six.iteritems(self.scores_tree):
                title = segment_values[0].get('title')
                score_calculator = get_score_calculator(segment_path)
                if score_calculator:
                    for score in score_calculator.get_scorecards(
                            self.campaign, segment_path, title=title,
                            includes=[self.sample]):
                        self._insert_in_tree(
                            self.scores_tree, score.path, score)
        self._report_queries("(optional) active sample scores inserted")

        self.create_distributions(
            self.scores_tree, view_account_id=self.account.pk)
        self._report_queries("create_distributions completed")
        charts, unused_segment_complete = self.flatten_distributions(
            self.scores_tree)
        self._report_queries("flatten_distributions completed")

        for question in queryset:
            question_path = question.get('path')
            for chart in charts:
                chart_path = chart.get('path')
                if question_path == chart_path:
                    question.update({
                        'benchmarks': chart.get('benchmarks'),
                        'nb_respondents': chart.get('nb_respondents'),
                        'avg_normalized_score':
                            chart.get('avg_normalized_score'),
                        'highest_normalized_score':
                            chart.get('highest_normalized_score')
                    })
                    break
        self._report_queries("merge into JSON response completed")



class SampleBenchmarksIndexAPIView(SampleBenchmarksAPIView):
    """
    Benchmarks against all peers

    Returns a list of graphs with anonymized performance of peers
    for paths marked as visible (see ::ref::`api_score`).

    **Tags**: benchmarks

    **Examples

    .. code-block:: http

        GET /api/supplier-1/sample/ce6dc2c4cf6b40dbacef91fa3e934eed\
/benchmarks HTTP/1.1

    responds

    .. code-block:: json

        {
            "highest_normalized_score": 100,
            "avg_normalized_score": 50,
            "results": [{
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
                "avg_normalized_score": 67,
                "created_at":"2017-08-02T20:18:19.089",
                "distribution": {
                    "y": [0, 1, 0, 1],
                    "x": ["0-25%", "25-50%", "50-75%", "75-100%"]
                }
             },
             {
                "slug":"energy-efficiency-management-basics",
                "title":"Management",
                "tag":"management",
                "score_weight":1.0
             },
             {
                "slug":"process-heating",
                "title":"Process heating",
                "nb_questions": 4,
                "nb_answers": 4,
                "nb_respondents": 2,
                "numerator": 12.0,
                "improvement_numerator": 8.0,
                "denominator": 26.0,
                "normalized_score": 46,
                "improvement_score": 12,
                "avg_normalized_score": 67,
                "created_at": "2017-08-02T20:18:19.089",
                "distribution": {
                    "y": [0, 1, 0, 1],
                    "x": [ "0-25%", "25-50%", "50-75%", "75-100%"]
                },
                "score_weight": 1.0
             }]
        }
    """

    @extend_schema(operation_id='sample_benchmarks_index')
    def get(self, request, *args, **kwargs):
        return super(SampleBenchmarksIndexAPIView, self).get(
            request, *args, **kwargs)


class RespondentsAPIView(generics.ListAPIView):
    """
    Lists profiles with a frozen response

    Returns {{PAGE_SIZE}} profiles with a frozen response

    **Tags**: assessments

    **Examples**

    .. code-block:: http

         GET /api/respondents HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 4,
          "results": [{
            "picture": null,
            "printable_name": "S1"
          }, {
            "picture": null,
            "printable_name": "S2"
          }, {
            "picture": null,
            "printable_name": "S3"
          }, {
            "picture": null,
            "printable_name": "S4"
          }]
        }
    """
    authentication_classes = []

    search_fields = (
        'full_name',
        'email'
    )
    ordering_fields = (
        ('full_name', 'printable_name'),
        ('created_at', 'created_at')
    )
    ordering = ('printable_name',)

    filter_backends = (OrderingFilter, SearchFilter)
    serializer_class = RespondentAccountSerializer

    def get_queryset(self):
        queryset = get_account_model().objects.filter(
            samples__extra__isnull=True,
            samples__is_frozen=True).exclude(
            Q(email__isnull=True)|Q(email="")).distinct()
        return queryset


class SampleRecentCreateAPIView(SampleRecentCreateBaseAPIView):
    """
    Lists samples

    Returns all samples for a profile

    **Tags**: assessments

    **Examples**

    .. code-block:: http

        GET /api/supplier-1/sample HTTP/1.1

    responds

    .. code-block:: json

        {
            "count": 1,
            "previous": null,
            "next": null,
            "results": [
            {
                "slug": "46f66f70f5ad41b29c4df08f683a9a7a",
                "created_at": "2018-01-24T17:03:34.926193Z",
                "campaign": "sustainability",
                "is_frozen": false,
                "extra": null,
                "verified_status": "no-review"
            }
            ]
        }
    """
    serializer_class = ExtendedSampleSerializer

    def decorate_queryset(self, queryset):
        verified_samples = {verified_sample.sample_id: verified_sample
            for verified_sample in VerifiedSample.objects.filter(
                sample__in=queryset,
                verified_status=VerifiedSample.STATUS_REVIEW_COMPLETED)}
        by_verifier_notes = {verified_sample.verifier_notes_id: verified_sample
            for verified_sample in VerifiedSample.objects.filter(
                verifier_notes__in=queryset)}
        for sample in queryset:
            sample.location = reverse('scorecard', args=(self.account, sample))
            verified_sample = verified_samples.get(sample.pk)
            sample.verified_status = (verified_sample.verified_status
                if verified_sample else VerifiedSample.STATUS_NO_REVIEW)
            # When listing samples for a verifier, we want to show the scorecard
            # of the verified sample alongside the verifier notes.
            verified_sample = by_verifier_notes.get(sample.pk)
            if verified_sample:
                sample.location = reverse(
                    'scorecard', args=(self.account, verified_sample.sample))
        return super(SampleRecentCreateAPIView, self).decorate_queryset(
            queryset)


class PortfolioRequestsSend(AccountMixin, generics.CreateAPIView):

    serializer_class = UserDetailSerializer

    def post(self, request, *args, **kwargs):
        """
        Resends all requests directed to {profile}

        **Tags**: portfolios

        **Examples

        .. code-block:: http

            POST /api/supplier-1/portfolios/requests/send HTTP/1.1

        .. code-block:: json

            {
              "email": "steve@example.com"
            }

        responds

        .. code-block:: json

            {}
        """
        return self.create(request, *args, **kwargs)


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        send_reminders(self.account,
            email=serializer.validated_data.get('email'))
        return http.Response({}, status=http_status.HTTP_201_CREATED)
