# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from django.utils.translation import ugettext_lazy as _
from pages.serializers import NodeElementSerializer
from rest_framework import serializers
from survey.models import Unit


class NoModelSerializer(serializers.Serializer):

    def create(self, validated_data):
        raise RuntimeError('`create()` should not be called.')

    def update(self, instance, validated_data):
        raise RuntimeError('`update()` should not be called.')


class AnswerSerializer(NoModelSerializer):
    """
    Serializer of between a ``survey.Answer`` and ``pages.PageElement``
    """
    path = serializers.CharField(read_only=True, allow_null=True)
    indent = serializers.SerializerMethodField(required=False, allow_null=True)
    title = serializers.CharField(read_only=True, allow_null=True)
    picture = serializers.CharField(required=False, allow_null=True,
        help_text=_("Picture icon that can be displayed alongside the title"))
    extra = serializers.SerializerMethodField(required=False, allow_null=True,
        help_text=_("Extra meta data (can be stringify JSON)"))

    account = serializers.SlugRelatedField(slug_field='slug',
        read_only=True, required=False,
        help_text=("Account that can edit the page element"))

    unit = serializers.SlugRelatedField(required=False, allow_null=True,
        queryset=Unit.objects.all(), slug_field='slug',
        help_text=_("Unit the measured field is in"))
    measured = serializers.CharField(required=True, allow_null=True,
        allow_blank=True, help_text=_("measurement in unit"))

    created_at = serializers.DateTimeField(read_only=True,
        help_text=_("Date/time of creation (in ISO format)"))
    # We are not using a `UserSerializer` here because retrieving profile
    # information must go through the profiles API.
    collected_by = serializers.SlugRelatedField(read_only=True,
        required=False, slug_field='username',
        help_text=_("User that collected the answer"))

    class Meta(object):
        fields = ('unit', 'measured', 'created_at', 'collected_by')
        read_only_fields = ('created_at', 'collected_by')

    @staticmethod
    def get_extra(obj):
        try:
            return obj.get('extra', {})
        except AttributeError:
            pass
        try:
            return obj.extra
        except AttributeError:
            pass
        return {}

    @staticmethod
    def get_indent(obj):
        try:
            return obj.get('indent', 0)
        except AttributeError:
            pass
        try:
            return obj.indent
        except AttributeError:
            pass
        return 0


class ContentElementSerializer(NodeElementSerializer):

    url = serializers.CharField(required=False)
    nb_referencing_practices = serializers.IntegerField(required=False)
    segments = serializers.ListSerializer(child=serializers.CharField(),
        required=False)

    class Meta(NodeElementSerializer.Meta):
        model = NodeElementSerializer.Meta.model
        fields = NodeElementSerializer.Meta.fields + (
            'slug', 'url', 'nb_referencing_practices', 'segments')


class CreateParentSerializer(NoModelSerializer):

    slug = serializers.CharField(required=False)
    title = serializers.CharField(required=False)


class CreateContentElementSerializer(ContentElementSerializer):

    parents = CreateParentSerializer(many=True)

    class Meta(ContentElementSerializer.Meta):
        model = ContentElementSerializer.Meta.model
        fields = ContentElementSerializer.Meta.fields + (
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
