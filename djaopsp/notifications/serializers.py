# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE

from rest_framework import serializers
from survey.api.serializers import (NoModelSerializer,
    InviteeSerializer as ProfileSerializer)
from survey.models import Campaign

from ..compat import gettext_lazy as _

class UserDetailSerializer(NoModelSerializer):

    username = serializers.CharField(
        help_text=_("Unique identifier for the user, typically used in URLs"))
    printable_name = serializers.CharField(source='get_full_name',
        help_text=_("Full name (effectively first name followed by last name)"))

    class Meta:
        fields = ('username', 'printable_name')
        read_only_fields = ('username', 'printable_name')


class NotificationSerializer(NoModelSerializer):

    broker = ProfileSerializer(required=False,
        help_text=_("Site on which the product is hosted"))
    back_url = serializers.URLField(
        help_text=_("Link back to the site"))

    class Meta:
        fields = ('broker', 'back_url',)
        read_only_fields = ('broker', 'back_url',)


class PortfolioGrantInitiatedSerializer(NotificationSerializer):

    invitee = ProfileSerializer()
    campaign = serializers.SlugRelatedField(required=False,
        queryset=Campaign.objects.all(), slug_field='slug')
    message = serializers.CharField(required=False, allow_null=True)

    class Meta:
        fields = ("invitee", "campaign", "message", "ends_at",)
        read_only_fields = ("ends_at",)


class PortfolioNotificationSerializer(NotificationSerializer):

    grantee = ProfileSerializer()
    account = ProfileSerializer()
    campaign = serializers.SlugRelatedField(required=False,
        queryset=Campaign.objects.all(), slug_field='slug')
    message = serializers.CharField(required=False, allow_null=True)
    originated_by = UserDetailSerializer(
        help_text=_("the user at the origin of the notification"))

    class Meta:
        fields = ("grantee", "account", "campaign", "message", "originated_by",)
        read_only_fields = ("grantee", "account", "campaign", "originated_by",)