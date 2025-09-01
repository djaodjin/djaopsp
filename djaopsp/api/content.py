# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

from pages.api.elements import (PageElementAPIView as PageElementBaseAPIView,
    PageElementEditableListAPIView as PageElementEditableListBaseAPIView)
from pages.docs import extend_schema
from survey.utils import get_question_model

from .serializers import ContentElementSerializer
from ..mixins import VisibilityMixin
from ..utils import get_practice_serializer


class PageElementAPIView(VisibilityMixin, PageElementBaseAPIView):
    """
    Lists tree of page elements matching prefix

    **Tags: content

    **Example

    .. code-block:: http

        GET /api/content/boxes-and-enclosures HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 8,
          "next": null,
          "previous": null,
          "results": [
          {
            "slug": "metal",
            "path": null,
            "title": "Metal structures & equipment",
            "indent": 0
          },
          {
            "slug": "boxes-and-enclosures",
            "path": "/metal/boxes-and-enclosures",
            "title": "Boxes & enclosures",
            "indent": 1,
            "tags": [
              "industry",
              "pagebreak",
              "public",
              "scorecard"
            ]
          }
          ]
        }
    """
    serializer_class = ContentElementSerializer
    practice_serializer_class = get_practice_serializer()
    #authentication_classes = [] # XXX permissions are handled somewhere else.

    def get_extra_fields(self):
        extra_fields_select = []
        if hasattr(self.practice_serializer_class.Meta, 'extra_fields'):
            extra_fields = self.practice_serializer_class.Meta.extra_fields
            if extra_fields:
                for field in extra_fields:
                    extra_fields_select += ['content__%s' % field]
        return extra_fields_select

    def attach(self, elements):
        extra_fields = self.get_extra_fields()
        values_by_path = {}
        queryset = get_question_model().objects.filter(
            path__in=[elem['path'] for elem in elements]).values(
            'path', 'default_unit__slug', *extra_fields)
        for resp in queryset:
            path = resp.pop('path')
            # don't ask. Django ORM is being funny as usual.
            default_unit_slug = resp.pop('default_unit__slug')
            resp.update({'default_unit': default_unit_slug})
            values_by_path.update({path: resp})
        for elem in elements:
            path = elem['path']
            values = values_by_path.get(path)
            if values:
                elem.update(values)
        return elements


class PageElementIndexAPIView(PageElementAPIView):
    """
    Lists tree of page elements

    **Tags: content

    **Example

    .. code-block:: http

        GET /api/content HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 8,
          "next": null,
          "previous": null,
          "results": [
          {
            "slug": "metal",
            "path": null,
            "title": "Metal structures & equipment",
            "indent": 0
          },
          {
            "slug": "boxes-and-enclosures",
            "path": "/metal/boxes-and-enclosures",
            "title": "Boxes & enclosures",
            "indent": 1,
            "tags": [
              "industry",
              "pagebreak",
              "public",
              "scorecard"
            ]
          }
          ]
        }
    """

    @extend_schema(operation_id='content_index')
    def get(self, request, *args, **kwargs):
        return super(PageElementIndexAPIView, self).get(
            request, *args, **kwargs)


class PageElementEditableListAPIView(PageElementEditableListBaseAPIView):
    """
    List editable page elements

    This API endpoint lists page elements that are owned and thus editable
    by an account.

    **Tags**: editors

    **Examples

    .. code-block:: http

        GET /api/editables/alliance/content HTTP/1.1

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
-process-is-rigorous",
                    "title": "The assessment process is rigorous",
                    "indent": 2,
                    "extra": {
                        "intrinsic_values": {
                            "environmental_value": 1,
                            "business_value": 1,
                            "profitability": 1,
                            "implementation_ease": 1,
                            "avg_value": 1
                        }
                    }
                },
                {
                    "path": null,
                    "title": "Production",
                    "picture": "https://assets.tspproject.org/production.png",
                    "indent": 1
                },
                {
                    "path": "/construction/production/adjust-air-fuel\
-ratio",
                    "title": "Adjust Air fuel ratio",
                    "indent": 2,
                    "extra": {
                        "intrinsic_values": {
                            "environmental_value": 2,
                            "business_value": 2,
                            "profitability": 2,
                            "implementation_ease": 2,
                            "avg_value": 2
                        }
                    }
                }
            ]
        }
    """
    account_url_kwarg = 'profile'

    @extend_schema(operation_id='editables_content_index')
    def post(self, request, *args, **kwargs):
        """
        Creates a page element

        **Tags: editors

        **Example

        .. code-block:: http

            POST /api/editables/alliance/content HTTP/1.1

        .. code-block:: json

            {
                "title": "Boxes enclosures"
            }

        responds

        .. code-block:: json

            {
                "slug": "boxes-enclosures",
                "title": "Boxes enclosures"
            }

        """
        #pylint:disable=useless-super-delegation
        return super(PageElementEditableListAPIView, self).create(
            request, *args, **kwargs)
