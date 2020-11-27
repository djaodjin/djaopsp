# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

import json, logging

from django.db.models import Q
from rest_framework import serializers, generics
from rest_framework.filters import SearchFilter

from pages.models import PageElement
from pages.api.edition import (PageElementDetailAPIView,
    PageElementSearchAPIView)

from ..compat import six
from ..mixins import BreadcrumbMixin, ContentCut
from ..models import Consumption
from ..serializers import NoModelSerializer

LOGGER = logging.getLogger(__name__)


class ContentElementSerializer(NoModelSerializer):

    path = serializers.CharField()
    title = serializers.CharField()
    indent = serializers.IntegerField()
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    picture = serializers.CharField(required=False)
    environmental_value = serializers.IntegerField(required=False)
    business_value = serializers.IntegerField(required=False)
    profitability = serializers.IntegerField(required=False)
    implementation_ease = serializers.IntegerField(required=False)
    avg_value = serializers.IntegerField(required=False)


class ContentDetailAPIView(PageElementDetailAPIView):

    pass


class ContentListAPIView(BreadcrumbMixin, generics.ListAPIView):
    """
    Lists a tree of page elements

    **Tags**: content

    **Examples

    .. code-block:: http

        GET /api/content/construction HTTP/1.1

    responds

    .. code-block:: json

        {
            "count": 5,
            "next": null,
            "previous": null,
            "results": [
                {
                    "path": null,
                    "title": "Construction",
                    "tags": ["public"],
                    "indent": 0
                },
                {
                    "path": null,
                    "title": "Governance & management",
                    "picture": "https://assets.tspproject.org/management.png",
                    "indent": 1
                },
                {
                    "path": "/construction/governance/the-assessment\
--process-is-rigorous",
                    "title": "The assessment process is rigorous",
                    "indent": 2,
                    "environmental_value": 1,
                    "business_value": 1,
                    "profitability": 1,
                    "implementation_ease": 1,
                    "avg_value": 1
                },
                {
                    "path": null,
                    "title": "Production",
                    "picture": "https://assets.tspproject.org/production.png",
                    "indent": 1
                },
                {
                    "path": "/construction/production/adjust-air-fuel\
--ratio",
                    "title": "Adjust Air fuel ratio",
                    "indent": 2,
                    "environmental_value": 2,
                    "business_value": 2,
                    "profitability": 2,
                    "implementation_ease": 2,
                    "avg_value": 2
                }
            ]
        }
    """
    serializer_class = ContentElementSerializer
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
        trail = self.get_full_element_path(self.path)
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
                rollup_tree = self._build_tree(root, full_path,
                    cut=cut, load_text=True)
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
            text = elem.get('text', None)
            if text and text.endswith('.png'):
                content.update({
                    'picture': text
                })
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
                enumeratedquestions__campaign=self.campaign, path=path).first()
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


class ContentSearchAPIView(PageElementSearchAPIView):

    serializer_class = ContentElementSerializer
