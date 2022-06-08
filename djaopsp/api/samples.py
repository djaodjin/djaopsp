# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import copy, logging

from dateutil.relativedelta import relativedelta
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

from ..compat import reverse, six
from ..mixins import AccountMixin, SegmentReportMixin
from ..models import ScorecardCache
from ..scores import freeze_scores, get_score_calculator, populate_rollup
from ..utils import get_leafs, get_practice_serializer, get_scores_tree
from .campaigns import CampaignContentMixin
from .rollups import GraphMixin, RollupMixin, ScoresMixin
from .serializers import (AssessmentContentSerializer, AssessmentNodeSerializer,
    BenchmarkSerializer, HistoricalAssessmentSerializer, UnitSerializer)


LOGGER = logging.getLogger(__name__)


class AssessmentCompleteAPIView(SegmentReportMixin, TimersMixin,
                                SampleFreezeAPIView):

    def post(self, request, *args, **kwargs):
        """
        Freezes a sample of measurements

        **Tags**: assessments

        **Examples

        .. code-block:: http

            POST /api/supplier-1/sample/0123456789abcdef/freeze/construction\
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

    def _populate_scorecard_cache(self, rollup_tree, improvement_sample=None):
        scorecard_cache = []
        for node in six.itervalues(rollup_tree[1]):
            scorecard_cache += self._populate_scorecard_cache(  # recursive call
                node, improvement_sample=improvement_sample)
        path = rollup_tree[0].get('path')
        if path:
            # We do not need the "totals" node here.
            for account in six.itervalues(rollup_tree[0].get('accounts')):
                sample = Sample.objects.get(slug=account.get('sample'))
                nb_planned_improvements = account.get('nb_planned_improvements')
                if nb_planned_improvements is None:
                    if improvement_sample:
                        nb_planned_improvements = \
                            Answer.objects.filter(
                                sample=improvement_sample,
                                question__path__startswith=path,
                                unit_id=self.default_unit_id).count()
                    else:
                        nb_planned_improvements = 0
                scorecard_cache += [
                    ScorecardCache(
                        path=path,
                        sample=sample,
                        normalized_score=account.get(
                            'normalized_score', None),
                        nb_na_answers=account.get(
                            'nb_na_answers', None),
                        nb_planned_improvements=nb_planned_improvements
                    )]
        return scorecard_cache

    def populate_scorecard_cache(self, frozen_assessment_sample,
                                 improvement_sample=None):
        #pylint:disable=too-many-locals
        rollup_tree = [{
            "slug": "totals",
            "title": "Total Score",
            "tag": [
                "scorecard"
            ],
            "score_weight": 1.0,
            "accounts": {}
        }, {}]
        for segment in self.segments_available:
            segment_path = segment.get('path')
            if segment_path:
                slug = segment_path.split('/')[-1]
                prefix = '/'.join(segment_path.split('/')[:-1])
                rollup_tree[1].update(get_scores_tree(
                    roots=[PageElement.objects.get(slug=slug)],
                    prefix=prefix)[1])

        leafs = get_leafs(rollup_tree, frozen_assessment_sample.campaign)
        self._report_queries("freezing assessment: leafs loaded")

        for prefix, values_tuple in six.iteritems(leafs):
            score_calculator = get_score_calculator(prefix)
            if score_calculator:
                title = values_tuple[0].get('title')
                scorecard_cache = score_calculator.get_scorecache(
                    frozen_assessment_sample.campaign,
                    prefix, title=title, includes=[frozen_assessment_sample])
                accounts = values_tuple[0].get('accounts', {})
                account = accounts.get(scorecard_cache.account_id, {})
                account.update({
                    'sample_id': scorecard_cache.id,
                    'slug': scorecard_cache.slug,
                    'created_at': scorecard_cache.created_at,
                    'campaign_id': scorecard_cache.campaign_id,
                    'updated_at': scorecard_cache.updated_at,
                    'is_frozen': scorecard_cache.is_frozen,
                    'extra': scorecard_cache.extra,
                    'segment_path': scorecard_cache.segment_path,
                    'segment_title': scorecard_cache.segment_title,
                    'numerator': scorecard_cache.numerator,
                    'denominator': scorecard_cache.denominator,
                    'nb_answers': scorecard_cache.nb_answers,
                    'nb_questions': scorecard_cache.nb_questions,
                    'nb_na_answers': scorecard_cache.nb_na_answers,
                    'reporting_publicly': scorecard_cache.reporting_publicly,
                    'reporting_fines': scorecard_cache.reporting_fines,
'reporting_energy_consumption': scorecard_cache.reporting_energy_consumption,
'reporting_ghg_generated': scorecard_cache.reporting_ghg_generated,
'reporting_water_consumption': scorecard_cache.reporting_water_consumption,
'reporting_waste_generated': scorecard_cache.reporting_waste_generated,
'reporting_energy_target': scorecard_cache.reporting_energy_target,
'reporting_ghg_target': scorecard_cache.reporting_ghg_target,
'reporting_water_target': scorecard_cache.reporting_water_target,
'reporting_waste_target': scorecard_cache.reporting_waste_target,
                })
                if scorecard_cache.account_id not in accounts:
                    accounts.update({scorecard_cache.account_id: account})
                if 'accounts' not in values_tuple[0]:
                    values_tuple[0].update({'accounts': accounts})
        self._report_queries("freezing assessment: leafs populated")
        populate_rollup(rollup_tree, True, force_score=True)
        self._report_queries("freezing assessment: rollup populated")

        scorecard_caches = self._populate_scorecard_cache(
            rollup_tree, improvement_sample=improvement_sample)

        ScorecardCache.objects.bulk_create(scorecard_caches)


    def create(self, request, *args, **kwargs):
        self._start_time()
        created_at = datetime_or_now()

        if self.nb_required_answers < self.nb_required_questions:
            raise ValidationError({'detail':
                "You have only answered %d of the %d required practices." % (
                self.nb_required_answers, self.nb_required_questions)})

        with transaction.atomic():
            frozen_assessment_sample = freeze_scores(
                self.sample,
                created_at=created_at,
                collected_by=self.request.user,
                segment_path=self.path)

            frozen_improvement_sample = None
            if (self.improvement_sample and
                self.improvement_sample.answers.exists()):
                frozen_improvement_sample = freeze_scores(
                    self.improvement_sample,
                    created_at=created_at,
                    collected_by=self.request.user,
                    segment_path=self.path)
            self._report_queries("freezing assessment: completed")

            self.populate_scorecard_cache(frozen_assessment_sample,
                improvement_sample=frozen_improvement_sample)
            self._report_queries("freezing assessment: scorecard cache created")

        # Next step in the assessment. After complete, scorecard is optional.
        next_url = reverse('share', args=(
            frozen_assessment_sample.account, frozen_assessment_sample))
        frozen_assessment_sample.location = self.request.build_absolute_uri(
            next_url)

        serializer = self.get_serializer(instance=frozen_assessment_sample)
        return http.Response(
            serializer.data, status=http_status.HTTP_201_CREATED)


class AssessmentContentMixin(SegmentReportMixin, CampaignContentMixin,
                             SampleCandidatesMixin, SampleAnswersMixin):

    practice_serializer_class = get_practice_serializer()

    def attach_answers(self, questions_by_key, queryset, key='answers'):
        #pylint:disable=too-many-locals
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
                self.units.update({default_unit.slug: default_unit})
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
                        'system': Unit.SYSTEMS[default_unit.system][1],
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
                if hasattr(self.practice_serializer_class.Meta, 'extra_fields'):
                    for field_name in \
                        self.practice_serializer_class.Meta.extra_fields:
                        value.update({
                            field_name: getattr(question, field_name)})
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
                self.units.update({resp.unit.slug: resp.unit})
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
                        'target', flat=True)
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
                    last_frozen_assessments,
                    prefix=prefix, includes=[self.sample]):
                question_pk = row['question__id']
                opportunity = row.get('opportunity', 0)
                value = questions_by_key.get(question_pk, {})
                value.update({'opportunity': opportunity})
                if question_pk not in questions_by_key:
                    questions_by_key.update({question_pk: value})

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
        self.units = {}
        if not prefix.endswith(self.DB_PATH_SEP):
            prefix = prefix + self.DB_PATH_SEP

        questions_by_key = {}
        self.attach_answers(
            questions_by_key,
            self.get_answers(prefix=prefix, sample=self.sample,
                excludes=self.exclude_questions))

        if not self.sample.is_frozen:
            self.attach_answers(
                questions_by_key,
                self.get_candidates(prefix=prefix,
                    excludes=self.exclude_questions),
                key='candidates')

        self.attach_results(questions_by_key, prefix)

        # Adds planned improvements
        self.attach_answers(
            questions_by_key,
            self.get_planned(prefix=prefix),
            key='planned')
        return list(six.itervalues(questions_by_key))


class AssessmentContentAPIView(AssessmentContentMixin, generics.ListAPIView):
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


class HistoricalAssessmentsAPIView(AccountMixin, generics.ListAPIView):

    serializer_class = HistoricalAssessmentSerializer

    def get_queryset(self):
        return Sample.objects.filter(
            account=self.account,
            extra__isnull=True,
            is_frozen=True).order_by('-created_at').select_related('campaign')


class BenchmarkAPIView(SegmentReportMixin, GraphMixin, RollupMixin,
                       ScoresMixin, generics.ListAPIView):
    """
    Retrieves benchmark graphs

    Returns a list of graphs with anonymized performance of peers
    for paths marked as visible (see ::ref::`api_score`).

    **Tags**: scorecard

    **Examples

    .. code-block:: http

        GET /api/supplier-1/benchmark/ce6dc2c4cf6b40dbacef91fa3e934eed\
/graphs/boxes-and-enclosures HTTP/1.1

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

    @property
    def requested_accounts_pk(self):
        if not hasattr(self, '_requested_accounts_pk'):
            self._requested_accounts_pk = \
                self.account_model.objects.all().values_list('pk', flat=True)
        return self._requested_accounts_pk

    @property
    def scores_tree(self):
        if not hasattr(self, '_scores_tree'):
            segments = self.segments_available
            self._scores_tree = get_scores_tree([PageElement.objects.get(
                slug=seg['slug']) for seg in segments])
        return self._scores_tree

    @property
    def scores_of_interest(self):
        """
        Returns the segments/tiles we are interested in for this query.
        """
        if not hasattr(self, '_scores_of_interest'):
            self._scores_of_interest = flatten_content_tree(self.scores_tree)
        return self._scores_of_interest


    def list(self, request, *args, **kwargs): #pylint:disable=unused-argument
        self._start_time()
        charts = []
        queryset = self.get_queryset()
        for score in queryset:
            self._insert_in_tree(self.scores_tree, score.segment_path, score)
        self._report_queries("rollup_scores completed")
        self.create_distributions(
            self.scores_tree, view_account_id=self.account.pk)
        self._report_queries("create_distributions completed")
        segment_charts, segment_complete = self.flatten_distributions(
            self.scores_tree)
        self._report_queries("flatten_distributions completed")
        charts += segment_charts

        return http.Response(charts)
