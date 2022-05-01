# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from pages.serializers import (
    NodeElementSerializer as BaseNodeElementSerializer,
    PageElementSerializer as BasePageElementSerializer)
from survey.api.serializers import AnswerSerializer, UnitSerializer

from ..utils import get_practice_serializer


class NoModelSerializer(serializers.Serializer):

    def create(self, validated_data):
        raise RuntimeError('`create()` should not be called.')

    def update(self, instance, validated_data):
        raise RuntimeError('`update()` should not be called.')


class PracticeSerializer(BaseNodeElementSerializer):

    avg_value = serializers.SerializerMethodField()

    class Meta(BaseNodeElementSerializer.Meta):
        model = BaseNodeElementSerializer.Meta.model
        fields = BaseNodeElementSerializer.Meta.fields + (
            'avg_value',)

    @staticmethod
    def get_avg_value(obj):
        if hasattr(obj, 'avg_value'):
            return obj.avg_value
        if 'avg_value' in obj:
            return obj['avg_value']
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


class TableSerializer(NoModelSerializer):

    # XXX use `key` instead of `slug` here?
    key = serializers.CharField(
        help_text="Unique key in the table for the data series")
    created_at = serializers.DateTimeField(
        help_text="date/time at which the series was recorded")
    values = serializers.ListField(
        child=KeyValueTuple(),
        help_text="Datapoints in the serie")


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
    nb_respondents = serializers.SerializerMethodField(required=False)
    rate = serializers.SerializerMethodField(required=False)
    opportunity = serializers.SerializerMethodField(required=False)

    class Meta(PRACTICE_SERIALIZER.Meta):
        fields = PRACTICE_SERIALIZER.Meta.fields + (
            'rank', 'required', 'default_unit', 'ui_hint',
            'answers', 'candidates', 'planned',
            'nb_respondents', 'rate', 'opportunity')
        read_only_fields = PRACTICE_SERIALIZER.Meta.read_only_fields + (
            'rank', 'required', 'default_unit', 'ui_hint',
            'answers', 'candidates', 'planned',
            'nb_respondents', 'rate', 'opportunity')

    def get_default_unit(self, obj):
        default_unit = None
        if hasattr(obj, 'default_unit'):
            default_unit = obj.default_unit
        elif 'default_unit' in obj:
            default_unit = obj['default_unit']
        if default_unit:
            return UnitSerializer(context=self._context).to_representation(
                default_unit)
        return None

    @staticmethod
    def get_nb_respondents(obj):
        if hasattr(obj, 'nb_respondents'):
            return obj.nb_respondents
        if 'nb_respondents' in obj:
            return obj['nb_respondents']
        return 0

    @staticmethod
    def get_opportunity(obj):
        if hasattr(obj, 'opportunity'):
            return obj.opportunity
        if 'opportunity' in obj:
            return obj['opportunity']
        return None

    @staticmethod
    def get_rank(obj):
        if hasattr(obj, 'rank'):
            return obj.rank
        if 'rank' in obj:
            return obj['rank']
        return 0

    @staticmethod
    def get_rate(obj):
        if hasattr(obj, 'rate'):
            return obj.rate
        if 'rate' in obj:
            return obj['rate']
        return {}

    @staticmethod
    def get_required(obj):
        if hasattr(obj, 'required'):
            return obj.required
        if 'required' in obj:
            return obj['required']
        return False

    @staticmethod
    def get_ui_hint(obj):
        if hasattr(obj, 'ui_hint'):
            return obj.ui_hint
        if 'ui_hint' in obj:
            return obj['ui_hint']
        return None


class AssessmentContentSerializer(BasePageElementSerializer):

    count = serializers.IntegerField()
    results = serializers.ListField(AssessmentNodeSerializer())
    units = serializers.DictField(UnitSerializer(), required=False)

    class Meta(object):
        model = BasePageElementSerializer.Meta.model
        fields = BasePageElementSerializer.Meta.fields + ('units',)
        read_only_fields = BasePageElementSerializer.Meta.read_only_fields + (
            'units',)
