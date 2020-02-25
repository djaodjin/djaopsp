# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

#pylint: no-init
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from pages.models import PageElement
from pages.serializers import PageElementSerializer as BasePageElementSerializer
from survey.models import Answer, EnumeratedQuestions, Metric, Unit
from survey.api.serializers import AnswerSerializer

from .models import ColumnHeader, Consumption

class NoModelSerializer(serializers.Serializer):

    def create(self, validated_data):
        raise RuntimeError('`create()` should not be called.')

    def update(self, instance, validated_data):
        raise RuntimeError('`update()` should not be called.')

class DistributionSerializer(NoModelSerializer):

    x = serializers.ListField(child=serializers.IntegerField())
    y = serializers.ListField(serializers.CharField())
    organization_rate = serializers.CharField()


class BenchmarkSerializer(NoModelSerializer):

    metric = serializers.CharField()
    title = serializers.CharField()
    nb_answers = serializers.IntegerField()
    nb_questions = serializers.IntegerField()
    nb_respondents = serializers.IntegerField()
    numerator = serializers.FloatField()
    improvement_numerator = serializers.FloatField()
    denominator = serializers.FloatField()
    normalized_score = serializers.IntegerField()
    improvement_score = serializers.IntegerField()
    score_weight = serializers.FloatField()
    highest_normalized_score = serializers.IntegerField()
    avg_normalized_score = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    distribution = DistributionSerializer()


class ColumnHeaderSerializer(serializers.ModelSerializer):

    class Meta:
        model = ColumnHeader
        fields = ('slug', 'hidden',)
        read_only_fields = ('slug',)


class MeasureSerializer(serializers.ModelSerializer):

    metric = serializers.SlugRelatedField(
        queryset=Metric.objects.all(), slug_field='slug')
    unit = serializers.SlugRelatedField(required=False,
        queryset=Unit.objects.all(), slug_field='slug')
    measured = serializers.CharField()
    text = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = ('metric', 'unit', 'measured',
            'created_at', 'collected_by', 'text')
        read_only_fields = ('created_at', 'collected_by')

    @staticmethod
    def get_text(obj):
        if hasattr(obj, 'text'):
            return obj.text
        if isinstance(obj, dict) and 'text' in obj:
            return obj['text']
        return ""


class ConsumptionSerializer(serializers.ModelSerializer):

    path = serializers.CharField(required=False)
    rank = serializers.SerializerMethodField()
    metric = serializers.CharField(required=False)
    nb_respondents = serializers.SerializerMethodField()
    rate = serializers.SerializerMethodField()
    opportunity = serializers.SerializerMethodField()
    implemented = serializers.SerializerMethodField()
    planned = serializers.SerializerMethodField()
    measures = MeasureSerializer(many=True, required=False)

    class Meta:
        model = Consumption
        fields = (
            "path",
            # description
            #XXX "text",
            #XXX "avg_energy_saving", "avg_fuel_saving",
            #XXX "capital_cost", "payback_period",
            # value summary
            "environmental_value", "business_value", "profitability",
            "implementation_ease", "avg_value",
            # benchmarks
            "nb_respondents", "rate", "opportunity",
            "rank", "implemented", "planned", "metric",
            "measures")

    @staticmethod
    def get_nb_respondents(obj):
        return obj.nb_respondents if hasattr(obj, 'nb_respondents') else 0

    def get_rank(self, obj):
        if hasattr(obj, 'rank') and obj.rank:
            return obj.rank
        return EnumeratedQuestions.objects.filter(
            campaign=self.context['campaign'],
            question_id=obj.id).first().rank

    @staticmethod
    def get_rate(obj):
        return obj.rate if hasattr(obj, 'rate') else 0

    @staticmethod
    def get_implemented(obj):
        return obj.implemented if hasattr(obj, 'implemented') else (
            obj.measured if hasattr(obj, 'measured') else "")

    def get_opportunity(self, obj):
        if hasattr(obj, 'opportunity'):
            return obj.opportunity
        # XXX This is used in ``ImprovementListAPIView``.
        opportunities = self.context.get('opportunities', None)
        if opportunities is not None:
            return opportunities.get(obj.pk, 0) * 3
        return 0

    def get_planned(self, obj):
        if hasattr(obj, 'planned'):
            return bool(obj.planned)
        return self.context.get('planned', None)


class AnswerUpdateSerializer(NoModelSerializer):

    consumption = ConsumptionSerializer()
    first = serializers.BooleanField()

    class Meta:
        fields = ('consumption', 'first')


class AccountSerializer(NoModelSerializer):
    """
    Used to list accessible suppliers
    """
    REPORTING_NOT_STARTED = 0
    REPORTING_ABANDONED = 1
    REPORTING_EXPIRED = 2
    REPORTING_ASSESSMENT_PHASE = 3
    REPORTING_PLANNING_PHASE = 4
    REPORTING_COMPLETED = 5

    REPORTING_STATUS = (
        (REPORTING_NOT_STARTED, 'Not started'),
        (REPORTING_ABANDONED, 'Abandoned'),
        (REPORTING_EXPIRED, 'Expired'),
        (REPORTING_ASSESSMENT_PHASE, 'Assessment phase'),
        (REPORTING_PLANNING_PHASE, 'Planning phase'),
        (REPORTING_COMPLETED, 'Completed'),
    )

    slug = serializers.CharField(
        help_text=_("Unique identifier that can be used in a URL"))
    printable_name = serializers.CharField(
        help_text=_("Printable name"))
    email = serializers.EmailField(
        help_text=_("Primary contact e-mail"))
    last_activity_at = serializers.DateTimeField(required=False,
        help_text=_("Most recent time an assessment was updated"))
    requested_at = serializers.DateTimeField(required=False,
        help_text=_("Datetime at which the scorecard was requested"))
    reporting_status = serializers.SerializerMethodField(required=False,
        help_text=_("current reporting status"))

    segment = serializers.CharField(
        help_text=_("segment that was answered"))
    score_url = serializers.CharField(
        help_text=_("link to the scorecard"))
    normalized_score = serializers.IntegerField(
        help_text=_("score"))
    nb_na_answers = serializers.IntegerField(
        help_text=_("number of answers marked N/A"))
    reporting_publicly = serializers.BooleanField(
        help_text=_("also reporting publicly"))

    nb_planned_improvements = serializers.IntegerField(required=False,
        help_text=_("number of planned improvements"))
    targets = serializers.ListField(required=False,
        child=serializers.CharField(),
        help_text=_("improvement targets"))
    supplier_initiated = serializers.BooleanField(required=False,
        help_text=_("share was supplier initiated"))
    tags = serializers.SerializerMethodField(required=False,
        help_text=_("extra information tags"))

    def get_reporting_status(self, obj):
        return self.REPORTING_STATUS[obj.get(
            'reporting_status', self.REPORTING_NOT_STARTED)][1]

    @staticmethod
    def get_tags(obj):
        extra = obj.get('extra')
        if isinstance(extra, dict):
            return extra.keys()
        return []

class AssessmentMeasuresSerializer(NoModelSerializer):
    """
    measures which are not just Yes/No.
    """
    measures = MeasureSerializer(many=True)


class ImprovementSerializer(AnswerSerializer):

    measured = serializers.CharField(required=False)
    consumption = serializers.SerializerMethodField()

    class Meta(object):
        model = Answer
        fields = ('created_at', 'measured', 'consumption')

    @staticmethod
    def get_consumption(obj):
        if obj and obj.question:
            return obj.question.path
        return None


class KeyValueTuple(serializers.ListField):

    child = serializers.CharField() # XXX (String, Integer)
    min_length = 2
    max_length = 2


class TableSerializer(NoModelSerializer):

    # XXX use `key` instead of `slug` here?
    key = serializers.CharField(
        help_text="Unique key in the table for the data series")
    values = serializers.ListField(
        child=KeyValueTuple(),
        help_text="Datapoints in the serie")


class MetricsSerializer(NoModelSerializer):

    title = serializers.CharField(
        help_text="Title for the table")
    results = TableSerializer(many=True)


class MoveRankSerializer(NoModelSerializer):
    """
    Move a best practice into the tree of best practices.
    """
    source = serializers.CharField(write_only=True)


class PageElementSerializer(BasePageElementSerializer):

    consumption = ConsumptionSerializer(required=False)
    is_empty = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()

    class Meta:
        model = PageElement
        fields = ('slug', 'path', 'title', 'text', 'tag',
            'rank', 'is_empty', 'consumption')

    @staticmethod
    def get_rank(obj):
        return obj.rank if hasattr(obj, 'rank') else None

    @staticmethod
    def get_is_empty(obj):
        return not obj.text


class ScoreWeightSerializer(NoModelSerializer):

    weight = serializers.DecimalField(decimal_places=2, max_digits=3,
        required=True,
        help_text=_("weight to apply to the score at the content node"))

    class Meta:
        fields = ('weight',)
