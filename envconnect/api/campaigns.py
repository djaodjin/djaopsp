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


(0, {'path': '/metal', 'slug': 'metal', 'title': 'Metal structures & equipment', 'tag': '{"tags":["industry","enabled","heading"]}', 'score_weight': 1.0}),


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
        cut = ContentCut(depth=2)
        menus = []
        search_query = self.request.query_params.get('q')
        query_filter = Q(tag__contains='industry')
        if search_query:
            query_filter = query_filter & Q(tag__contains=search_query)
        for root in PageElement.objects.get_roots().filter(
                query_filter).order_by('title'):
            if not cut.enter(root.tag):
                menus += [{
                    'title': root.title,
                    'path': '/%s' % root.slug,
                    'indent': 0
                }]
            else:
                rollup_trees = self._cut_tree(self.build_content_tree(
                    [root], prefix='', cut=cut), cut=cut)
                menus += self.flatten(rollup_trees)
        return menus

    def flatten(self, rollup_trees, depth=0):
        result = []
        for _, values in six.iteritems(rollup_trees):
            elem, nodes = values
            path = None if nodes else elem['path']
            result += [
                {'title': elem['title'], 'path': path, 'indent': depth}]
            result += self.flatten(nodes, depth=depth + 1)
        return result
