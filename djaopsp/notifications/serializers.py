# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE

from rest_framework import serializers
from survey.api.serializers import (NoModelSerializer,
    InviteeSerializer as ProfileSerializer, CampaignSerializer, SampleSerializer)

from ..compat import gettext_lazy as _

class UserDetailSerializer(NoModelSerializer):

    username = serializers.CharField(
        help_text=_("Unique identifier for the user, typically used in URLs"))
    printable_name = serializers.CharField(source='get_full_name',
        help_text=_("Full name (effectively first name followed by last name)"))
    email = serializers.CharField(
        help_text=_("E-mail address for the originating user"))

    class Meta:
        fields = ('username', 'printable_name', 'email')
        read_only_fields = ('username', 'printable_name', 'email')


class NotificationSerializer(NoModelSerializer):

    broker = ProfileSerializer(required=False,
        help_text=_("Site on which the product is hosted"))
    back_url = serializers.URLField(
        help_text=_("Link back to the site"))
    originated_by = UserDetailSerializer(
        help_text=_("the user at the origin of the notification"))

    class Meta:
        fields = ('broker', 'back_url', 'originated_by')
        read_only_fields = ('broker', 'back_url', 'originated_by')


class PortfolioGrantInitiatedSerializer(NotificationSerializer):

    grantee = ProfileSerializer()
    campaign = CampaignSerializer(required=False)
    message = serializers.CharField(required=False, allow_null=True)

    class Meta:
        fields = ("invitee", "campaign", "message", "ends_at",)
        read_only_fields = ("ends_at",)


class PortfolioNotificationSerializer(NotificationSerializer):

    grantee = ProfileSerializer()
    account = ProfileSerializer()
    campaign = CampaignSerializer(required=False)
    last_completed_at = serializers.CharField(required=False)
    message = serializers.CharField(required=False, allow_null=True)

    class Meta:
        fields = ('grantee', 'account', 'campaign', 'last_completed_at',
            'message',)
        read_only_fields = ('grantee', 'account', 'campaign',
            'last_completed_at',)

class SampleFrozenNotificationSerializer(NotificationSerializer):
    # Needs to be updated depending on how we end up
    # getting the profile managers.
    account = ProfileSerializer()
    campaign = CampaignSerializer(required=False)
    last_completed_at = serializers.CharField(required=False)
    sample = SampleSerializer()

    class Meta:
        fields = ('account', 'campaign', 'last_completed_at', 'sample')

