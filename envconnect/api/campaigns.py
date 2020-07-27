# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

import logging

from django.db.models import Q
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter

from pages.models import PageElement

from ..compat import six
from ..mixins import BreadcrumbMixin, ContentCut
from ..serializers import NoModelSerializer


LOGGER = logging.getLogger(__name__)


class CampaignSerializer(NoModelSerializer):

    path = serializers.CharField()
    title = serializers.CharField()
    indent = serializers.IntegerField()


class CampaignListAPIView(BreadcrumbMixin, ListAPIView):
    """
    Lists of campaigns available

    **Tags**: survey

    **Examples

    .. code-block:: http

        GET /api/content/campaigns/?q=public \
          HTTP/1.1

    .. code-block:: json

        {}

    responds

    .. code-block:: json

        {}
    """
    serializer_class = CampaignSerializer
    filter_backends = (SearchFilter,)

    def get_queryset(self):
        return self.get_segments(
            search_query=self.request.query_params.get('q'))
