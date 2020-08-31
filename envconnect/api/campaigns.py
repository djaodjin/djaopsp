# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

import json, logging

from django.db.models import Q
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter

from pages.models import PageElement

from ..compat import six
from ..mixins import BreadcrumbMixin, ContentCut
from ..models import Consumption
from ..serializers import NoModelSerializer

LOGGER = logging.getLogger(__name__)


class CampaignSerializer(NoModelSerializer):

    path = serializers.CharField()
    title = serializers.CharField()
    indent = serializers.IntegerField()
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    text = serializers.CharField(required=False)
    environmental_value = serializers.IntegerField(required=False)
    business_value = serializers.IntegerField(required=False)
    profitability = serializers.IntegerField(required=False)
    implementation_ease = serializers.IntegerField(required=False)
    avg_value = serializers.IntegerField(required=False)


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
        """
        Returns a list of heading and best practices
        """
        search_query = (self.request.query_params.get('q')
            if hasattr(self, 'request') else None)
        query_filter = Q(tag__contains='industry')
        if search_query:
            query_filter = query_filter & Q(tag__contains=search_query)
        trail = self.get_full_element_path(self.kwargs.get('path'))
        full_path = '/%s' % '/'.join([element.slug for element in trail])
        if trail:
            prefix = '/%s' % '/'.join([element.slug for element in trail[:-1]])
            roots = [trail[-1]]
        else:
            prefix = ''
            roots = PageElement.objects.get_roots().filter(
                query_filter).order_by('title')

        menus = []
        cut = ContentCut(depth=2)

#        rollup_trees
        for root in roots:
            if not prefix and not cut.enter(root.tag):
                menus += [{
                    'title': root.title,
                    'path': '%s/%s' % (prefix, root.slug),
                    'indent': 0
                }]
            else:
                rollup_tree = self._build_tree(root, full_path, cut=cut)
                menus += self.flatten({prefix: rollup_tree})
        return menus

    def flatten(self, rollup_trees, depth=0):
        results = []
        for _, values in six.iteritems(rollup_trees):
            elem, nodes = values
            content = {
                'title': elem['title'],
                'path': None if nodes else elem['path'],
                'indent': depth
            }
            if 'tags' in elem and elem['tags']:
                content.update({
                    'tags': elem['tags']
                })
            if 'consumption' in elem and elem['consumption']:
                content.update({
                    'environmental_value':
                        elem['consumption'].environmental_value,
                    'business_value':
                        elem['consumption'].business_value,
                    'profitability':
                        elem['consumption'].profitability,
                    'implementation_ease':
                        elem['consumption'].implementation_ease,
                    'avg_value':
                        elem['consumption'].avg_value
                })
            results += [content]
            results += self.flatten(nodes, depth=depth + 1)
        return results

    def decorate_leafs(self, leafs):
        for path, vals in six.iteritems(leafs):
            consumption = Consumption.objects.filter(
                enumeratedquestions__campaign=self.survey, path=path).first()
            if consumption:
                vals[0]['consumption'] = consumption
            else:
                vals[0]['consumption'] = None
            extra = vals[0].get('tag', None)
            if extra:
                try:
                    extra = json.loads(extra)
                    vals[0]['tags'] = extra.get('tags', [])
                except (TypeError, ValueError):
                    pass
