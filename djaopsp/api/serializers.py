# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from pages.serializers import (
    NodeElementSerializer as BaseNodeElementSerializer,
    PageElementSerializer as BasePageElementSerializer)
from survey.api.serializers import (AccountSerializer, AnswerSerializer,
    CampaignSerializer, PortfolioOptInSerializer, UnitSerializer)

from ..compat import reverse
from ..utils import get_practice_serializer


class NoModelSerializer(serializers.Serializer):

    def create(self, validated_data):
        raise RuntimeError('`create()` should not be called.')

    def update(self, instance, validated_data):
        raise RuntimeError('`update()` should not be called.')


class DistributionSerializer(NoModelSerializer):

    x = serializers.ListField(serializers.CharField())
    y = serializers.ListField(child=serializers.IntegerField())
    organization_rate = serializers.CharField()


class BenchmarkSerializer(NoModelSerializer):

    slug = serializers.CharField()
    title = serializers.CharField()
    nb_answers = serializers.IntegerField(required=False)
    nb_questions = serializers.IntegerField(required=False)
    nb_respondents = serializers.IntegerField(required=False)
    numerator = serializers.FloatField(required=False)
    improvement_numerator = serializers.FloatField(required=False)
    denominator = serializers.FloatField(required=False)
    normalized_score = serializers.IntegerField(required=False)
    improvement_score = serializers.IntegerField(required=False)
    score_weight = serializers.FloatField()
    highest_normalized_score = serializers.IntegerField(required=False)
    avg_normalized_score = serializers.IntegerField(required=False)
    created_at = serializers.DateTimeField(required=False)
    distribution = DistributionSerializer(required=False)


class PracticeSerializer(BaseNodeElementSerializer):

    default_unit = serializers.SerializerMethodField()
    score_weight = serializers.SerializerMethodField(required=False)

    class Meta(BaseNodeElementSerializer.Meta):
        model = BaseNodeElementSerializer.Meta.model
        fields = BaseNodeElementSerializer.Meta.fields + (
            'default_unit', 'score_weight')

    def get_default_unit(self, obj):
        default_unit = None
        if hasattr(obj, 'default_unit'):
            default_unit = obj.default_unit
        else:
            try:
                default_unit = obj['default_unit']
            except (TypeError, KeyError):
                pass
        if default_unit and isinstance(default_unit, UnitSerializer.Meta.model):
            default_unit = UnitSerializer(
                context=self._context).to_representation(default_unit)
        return default_unit

    @staticmethod
    def get_score_weight(obj):
        if hasattr(obj, 'score_weight'):
            return obj.score_weight
        try:
            return obj['score_weight']
        except (TypeError, KeyError):
            pass
        return None


PRACTICE_SERIALIZER = get_practice_serializer()


class ContentNodeSerializer(PRACTICE_SERIALIZER):

    url = serializers.CharField(required=False)
    nb_referencing_practices = serializers.IntegerField(required=False)
    segments = serializers.ListSerializer(child=serializers.CharField(),
        required=False)

    class Meta(PRACTICE_SERIALIZER.Meta):
        fields = PRACTICE_SERIALIZER.Meta.fields + (
            'url', 'nb_referencing_practices', 'segments')


class ContentElementSerializer(BasePageElementSerializer):
    """
    Serializes a PageElement extended with intrinsic values
    """
    results = serializers.ListField(required=False,
        child=ContentNodeSerializer())


class CreateParentSerializer(NoModelSerializer):

    slug = serializers.CharField(required=False)
    title = serializers.CharField(required=False)


class CreateContentElementSerializer(ContentNodeSerializer):

    parents = CreateParentSerializer(many=True)

    class Meta(ContentNodeSerializer.Meta):
        model = ContentNodeSerializer.Meta.model
        fields = ContentNodeSerializer.Meta.fields + (
            'parents',)


class DatetimeValueTuple(serializers.ListField):

    child = serializers.CharField() # XXX (Datetime, Integer)
    min_length = 2
    max_length = 2


class KeyValueTuple(serializers.ListField):

    child = serializers.CharField() # XXX (String, Integer)
    min_length = 3
    max_length = 3


class AssessmentNodeSerializer(PRACTICE_SERIALIZER):
    """
    One practice retrieved through the assess content API
    """
    rank = serializers.SerializerMethodField()
    required = serializers.SerializerMethodField(required=False)
    ui_hint = serializers.SerializerMethodField(required=False)
    default_unit = serializers.SerializerMethodField(required=False)
    answers = serializers.ListField(child=AnswerSerializer(), required=False)
    candidates = serializers.ListField(child=AnswerSerializer(), required=False)
    planned = serializers.ListField(child=AnswerSerializer(), required=False)

    # assessment results
    normalized_score = serializers.SerializerMethodField(required=False)
    nb_respondents = serializers.SerializerMethodField(required=False)
    rate = serializers.SerializerMethodField(required=False)
    opportunity = serializers.SerializerMethodField(required=False)

    class Meta(PRACTICE_SERIALIZER.Meta):
        fields = PRACTICE_SERIALIZER.Meta.fields + (
            'rank', 'required', 'default_unit', 'ui_hint',
            'answers', 'candidates', 'planned',
            'normalized_score', 'nb_respondents', 'rate', 'opportunity')
        read_only_fields = PRACTICE_SERIALIZER.Meta.read_only_fields + (
            'rank', 'required', 'default_unit', 'ui_hint',
            'answers', 'candidates', 'planned',
            'normalized_score', 'nb_respondents', 'rate', 'opportunity')

    def get_default_unit(self, obj):
        default_unit = None
        if hasattr(obj, 'default_unit'):
            default_unit = obj.default_unit
        else:
            try:
                default_unit = obj['default_unit']
            except (TypeError, KeyError):
                pass
        if default_unit:
            return UnitSerializer(context=self._context).to_representation(
                default_unit)
        return None

    @staticmethod
    def get_normalized_score(obj):
        if hasattr(obj, 'normalized_score'):
            return obj.normalized_score
        try:
            return obj['normalized_score']
        except (TypeError, KeyError):
            pass
        return None

    @staticmethod
    def get_nb_respondents(obj):
        if hasattr(obj, 'nb_respondents'):
            return obj.nb_respondents
        try:
            return obj['nb_respondents']
        except (TypeError, KeyError):
            pass
        return 0

    @staticmethod
    def get_opportunity(obj):
        if hasattr(obj, 'opportunity'):
            return obj.opportunity
        try:
            return obj['opportunity']
        except (TypeError, KeyError):
            pass
        return None

    @staticmethod
    def get_rank(obj):
        if hasattr(obj, 'rank'):
            return obj.rank
        try:
            return obj['rank']
        except (TypeError, KeyError):
            pass
        return 0

    @staticmethod
    def get_rate(obj):
        if hasattr(obj, 'rate'):
            return obj.rate
        try:
            return obj['rate']
        except (TypeError, KeyError):
            pass
        return {}

    @staticmethod
    def get_required(obj):
        if hasattr(obj, 'required'):
            return obj.required
        try:
            return obj['required']
        except (TypeError, KeyError):
            pass
        return False

    @staticmethod
    def get_ui_hint(obj):
        if hasattr(obj, 'ui_hint'):
            return obj.ui_hint
        try:
            return obj['ui_hint']
        except (TypeError, KeyError):
            pass
        return None


class CompareNodeSerializer(PRACTICE_SERIALIZER):
    """
    One practice retrieved through the assess content API
    """
    default_unit = serializers.SerializerMethodField(required=False)
    values = serializers.ListField(
        child=serializers.ListField(child=AnswerSerializer()), required=False)

    class Meta(PRACTICE_SERIALIZER.Meta):
        fields = PRACTICE_SERIALIZER.Meta.fields + (
            'default_unit', 'values',)
        read_only_fields = PRACTICE_SERIALIZER.Meta.read_only_fields + (
            'default_unit', 'values',)

    def get_default_unit(self, obj):
        default_unit = None
        if hasattr(obj, 'default_unit'):
            default_unit = obj.default_unit
        else:
            try:
                default_unit = obj['default_unit']
            except (TypeError, KeyError):
                pass
        if default_unit:
            return UnitSerializer(context=self._context).to_representation(
                default_unit)
        return None


class AssessmentContentSerializer(serializers.ListSerializer):

    count = serializers.IntegerField()
    labels = serializers.ListField(serializers.CharField(), required=False)
    units = serializers.DictField(UnitSerializer(), required=False)
    results = serializers.ListField(AssessmentNodeSerializer())

    class Meta(object):
        model = BasePageElementSerializer.Meta.model
        fields = BasePageElementSerializer.Meta.fields + ('labels', 'units',)
        read_only_fields = BasePageElementSerializer.Meta.read_only_fields + (
            'labels', 'units',)


class ReportingSerializer(NoModelSerializer):
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

    slug = serializers.CharField(source='account_slug',
        help_text=_("Unique identifier that can be used in a URL"))
    printable_name = serializers.CharField(
        help_text=_("Printable name"))
    email = serializers.EmailField(
        help_text=_("Primary contact e-mail"))
    last_activity_at = serializers.DateTimeField(required=False,
        help_text=_("Most recent time an assessment was updated"))
    requested_at = serializers.DateTimeField(required=False, allow_null=True,
        help_text=_("Datetime at which the scorecard was requested"))
    reporting_status = serializers.SerializerMethodField(required=False,
        help_text=_("current reporting status"))

    last_completed_at = serializers.DateTimeField(required=False,
        help_text=_("Most recent time an assessment was completed"))
    segment = serializers.CharField(allow_blank=True,
        help_text=_("segment that was answered"))
    score_url = serializers.CharField(required=False, allow_blank=True,
        help_text=_("link to the scorecard"))
    normalized_score = serializers.IntegerField(required=False, allow_null=True,
        help_text=_("score"))
    nb_na_answers = serializers.IntegerField(allow_null=True,
        help_text=_("number of answers marked N/A"))
    reporting_publicly = serializers.BooleanField(allow_null=True,
        help_text=_("also reporting publicly"))
    reporting_fines = serializers.BooleanField(allow_null=True,
        help_text=_("reporting environmental fines"))

    reporting_energy_consumption = serializers.BooleanField(required=False,
        allow_null=True,
        help_text=_("energy measured and trended"))
    reporting_ghg_generated = serializers.BooleanField(required=False,
        allow_null=True,
        help_text=_("ghg emissions measured and trended"))
    reporting_water_consumption = serializers.BooleanField(required=False,
        allow_null=True,
        help_text=_("water measured and trended"))
    reporting_waste_generated = serializers.BooleanField(required=False,
        allow_null=True,
        help_text=_("waste measured and trended"))

    nb_planned_improvements = serializers.IntegerField(required=False,
        allow_null=True,
        help_text=_("number of planned improvements"))
    targets = serializers.ListField(required=False,
        child=serializers.CharField(),
        help_text=_("improvement targets"))
    supplier_initiated = serializers.BooleanField(required=False,
        help_text=_("share was supplier initiated"))
    tags = serializers.SerializerMethodField(required=False,
        help_text=_("extra information tags"))

    def get_reporting_status(self, obj):
        if (hasattr(obj, 'reporting_status') and
            obj.reporting_status < len(self.REPORTING_STATUS)):
            reporting_status_tuple = self.REPORTING_STATUS[obj.reporting_status]
            if reporting_status_tuple:
                return reporting_status_tuple[1]
        return self.REPORTING_STATUS[0][1] # REPORTING_NOT_STARTED

    @staticmethod
    def get_tags(obj):
        extra = obj.extra
        if isinstance(extra, dict):
            return extra.keys()
        return []


class EngagementSerializer(AccountSerializer):

    REPORTING_INVITED = 'invited'
    REPORTING_UPDATED = 'updated'
    REPORTING_COMPLETED = 'completed'
    REPORTING_COMPLETED_DENIED = 'completed-denied'
    REPORTING_COMPLETED_NOTSHARED = 'completed-notshared'
    REPORTING_INVITED_DENIED = 'invited-denied'

    REPORTING_STATUS = {
        'invited': "Invited",
        'updated': "Work-in-progress",
        'completed': "Completed",
        'completed-denied': "Completed",
        'completed-notshared': "Completed",
        'invited-denied': "Invited"
    }

    sample = serializers.SlugField(required=False)
    score_url = serializers.SerializerMethodField(
        help_text=_("link to the scorecard"))
    reporting_status = serializers.CharField(required=False,
        help_text=_("current reporting status"))
    last_activity_at = serializers.DateTimeField(required=False,
        allow_null=True,
        help_text=_("Most recent time an assessment was updated"))
    last_reminder_at = serializers.DateTimeField(required=False,
        allow_null=True,
        help_text=_("Most recent time a reminder was sent"))
    requested_at = serializers.DateTimeField(required=False, allow_null=True,
        help_text=_("Datetime at which the scorecard was requested"))
    normalized_score = serializers.IntegerField(required=False)

    class Meta(PortfolioOptInSerializer.Meta):
        fields = AccountSerializer.Meta.fields + (
            'extra', 'sample', 'score_url', 'reporting_status',
            'last_activity_at', 'last_reminder_at', 'requested_at',
            'normalized_score')

    def get_score_url(self, obj):
        if hasattr(obj, 'sample'):
            return reverse('scorecard', args=(
                self.context['account'], obj.sample))
        return None


class HistoricalAssessmentSerializer(NoModelSerializer):

    slug = serializers.SlugField()
    last_completed_at = serializers.DateTimeField(source='created_at',
        read_only=True,
        help_text=_("Date/time an assessment was completed"))
    campaign = CampaignSerializer()
