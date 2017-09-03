# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

#pylint: disable=old-style-class,no-init

from rest_framework import serializers

from pages.models import PageElement
from pages.serializers import PageElementSerializer as BasePageElementSerializer

from envconnect.models import ColumnHeader, Consumption


class ColumnHeaderSerializer(serializers.ModelSerializer):

    class Meta:
        model = ColumnHeader
        fields = ('slug', 'hidden',)
        readonly_fields = ('slug',)


class ConsumptionSerializer(serializers.ModelSerializer):

    path = serializers.CharField(required=False)
    text = serializers.CharField(required=False)
    rank = serializers.SerializerMethodField()
    implemented = serializers.SerializerMethodField()
    planned = serializers.SerializerMethodField()

    class Meta:
        model = Consumption
        fields = (
            "path", "text",
            # description
            "avg_energy_saving", "avg_fuel_saving",
            "capital_cost", "payback_period",
            # value summary
            "environmental_value", "business_value", "profitability",
            "implementation_ease", "avg_value",
            # benchmarks
            "rank", "implemented", "planned", "requires_measurements")

    @staticmethod
    def get_rank(obj):
        return obj.rank

    @staticmethod
    def get_implemented(obj):
        return obj.implemented if hasattr(obj, 'implemented') else ""

    @staticmethod
    def get_planned(obj):
        return obj.planned if hasattr(obj, 'planned') else False

    def get_opportunity(self, obj):
        if hasattr(obj, 'opportunity'):
            return obj.opportunity
        opportunities = self.context.get('opportunities', None)
        if opportunities is not None:
            return opportunities.get(obj.pk, 0) * 3
        return 0


class AccountSerializer(serializers.Serializer):
    """
    Used to list accessible suppliers
    """
    slug = serializers.CharField()
    printable_name = serializers.CharField()
    normalized_score = serializers.IntegerField(required=False)
    last_activity_at = serializers.DateTimeField(required=False)
    nb_questions = serializers.IntegerField(required=False)
    nb_answers = serializers.IntegerField(required=False)

    def create(self, validated_data):
        raise NotImplementedError('This serializer is read-only')

    def update(self, instance, validated_data):
        raise NotImplementedError('This serializer is read-only')


class MoveRankSerializer(serializers.Serializer):
    """
    Move a best practice into the tree of best practices.
    """
    source = serializers.CharField(write_only=True)

    def create(self, validated_data):
        raise NotImplementedError('This serializer is read-only')

    def update(self, instance, validated_data):
        raise NotImplementedError('This serializer is read-only')


class PageElementSerializer(BasePageElementSerializer):

    consumption = ConsumptionSerializer(required=False)
    is_empty = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()

    class Meta:
        model = PageElement
        fields = ('slug', 'path', 'title', 'tag',
            'rank', 'is_empty', 'consumption')

    @staticmethod
    def get_rank(obj):
        return obj.rank if hasattr(obj, 'rank') else None

    @staticmethod
    def get_is_empty(obj):
        return not obj.text


class ScoreWeightSerializer(serializers.Serializer):

    weight = serializers.DecimalField(decimal_places=2, max_digits=3,
        required=True)

    class Meta:
        fields = ('weight',)

    def create(self, validated_data):
        raise NotImplementedError('done is APIView')

    def update(self, instance, validated_data):
        raise NotImplementedError('done is APIView')
