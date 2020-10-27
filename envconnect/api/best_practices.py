# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

import json, logging, re

from deployutils.crypt import JSONEncoder
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from pages.mixins import TrailMixin
from pages.models import PageElement, RelationShip
from pages.api.relationship import (PageElementMirrorAPIView,
    PageElementMoveAPIView)
from pages.api.edition import PageElementEditableDetail
from survey.models import EnumeratedQuestions

from ..mixins import BestPracticeMixin, BreadcrumbMixin
from ..models import Consumption
from ..serializers import NoModelSerializer, PageElementSerializer

LOGGER = logging.getLogger(__name__)


class ExtraSerializer(NoModelSerializer):

    tags = serializers.CharField(
        help_text=_("extra/tag field from a PageElement"))


class ToggleTagContentAPIView(TrailMixin, UpdateAPIView):

    serializer_class = ExtraSerializer
    added_tag = None
    removed_tag = None

    def update(self, request, *args, **kwargs):
        trail = self.get_full_element_path(self.path)
        element = trail[-1]
        extra = {}
        try:
            extra = json.loads(element.tag)
        except (TypeError, ValueError):
            pass
        if 'tags' not in extra:
            if self.added_tag:
                extra.update({'tags': [self.added_tag]})
        else:
            if self.removed_tag and self.removed_tag in extra['tags']:
                extra['tags'].remove(self.removed_tag)
            if self.added_tag and not self.added_tag in extra['tags']:
                extra['tags'].append(self.added_tag)
        element.tag = json.dumps(extra, cls=JSONEncoder)
        element.save()
        return Response(element.tag)


class EnableContentAPIView(ToggleTagContentAPIView):
    """
    Enable a top level segment

    **Examples

    .. code-block:: http

       /api/content/editables/enable/boxes-enclosures/ HTTP/1.1

    responds

    .. code-block:: json

      {}

    """
    added_tag = "enabled"
    removed_tag = "disabled"


class DisableContentAPIView(ToggleTagContentAPIView):
    """
    Disable a top level segment

    **Examples

    .. code-block:: http

       /api/content/editables/disable/boxes-enclosures/ HTTP/1.1

    responds

    .. code-block:: json

      {}

    """
    added_tag = "disabled"
    removed_tag = "enabled"


class BestPracticeMirrorAPIView(BreadcrumbMixin, PageElementMirrorAPIView):
    """
    Mirror a content tree

    This API end-point mirrors content element under another node.

    A a result, we return the content tree that was updated
    instead of the `Column` instance because the user interface will
    want a chance to refresh the display accordingly.

    **Tags**: editors

    **Examples

    .. code-block:: http

       POST /api/content/editables/mirror/boxes-enclosures/\
energy-efficiency HTTP/1.1

    .. code-block:: json

        {
          "source": "getting-started"
        }

    responds

    .. code-block:: json

        {}

    """

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        targets = self.get_full_element_path(self.path)
        sources = self.get_full_element_path(serializer.validated_data.get(
            'source'))
        self.valid_against_loop(sources, targets)
        node = self.perform_change(sources, targets,
            rank=serializer.validated_data.get('rank', None))
        prefix = self.path
        root = self._build_tree(node, prefix + '/' + node.slug)
        headers = self.get_success_headers(root)
        return Response(root, status=status.HTTP_201_CREATED, headers=headers)

    def mirror_leaf(self, leaf, prefix="", new_prefix=""):
        rank = self.get_next_rank()
        for consumption in Consumption.objects.filter(
                path__startswith=prefix):
            new_path = None
            look = re.match(r"^%s/(.*)$" % prefix, consumption.path)
            if look:
                new_path = new_prefix + "/" + look.group(1)
            elif consumption.path == prefix:
                new_path = new_prefix
            if new_path:
                new_consumption, created = Consumption.objects.get_or_create(
                    path=new_path,
                    defaults={
                        'environmental_value': consumption.environmental_value,
                        'business_value': consumption.business_value,
                        'implementation_ease': consumption.implementation_ease,
                        'profitability': consumption.profitability,
                        'avg_energy_saving': consumption.avg_energy_saving,
                        'avg_fuel_saving': consumption.avg_fuel_saving,
                    })
                if created:
                    EnumeratedQuestions.objects.get_or_create(
                        campaign=self.survey, question=new_consumption,
                        rank=rank)
            rank = rank + 1
        return leaf


class BestPracticeMoveAPIView(PageElementMoveAPIView):
    """
    Moves a content tree

    Moves a PageElement from one attachement to another.

    **Tags**: editors

    **Examples

    .. code-block:: http

        POST /api/content/editables/envconnect/attach/boxes-enclosures HTTP/1.1

    .. code-block:: json

        {
          "source": "getting-started"
        }

    responds

    .. code-block:: json

        {}

   """

    def post(self, request, *args, **kwargs):#pylint: disable=unused-argument
        LOGGER.debug("move %s under %s", request.data, self.path)
        return super(BestPracticeMoveAPIView, self).post(
            request, *args, **kwargs)

    def perform_change(self, sources, targets, rank=None):
        moved = '/%s' % "/".join([source.slug for source in sources])
        attach = '/%s' % "/".join([target.slug for target in targets])
        if Consumption.objects.filter(path=attach).exists():
            raise ValidationError({'detail': "Cannot move '%s' under '%s'"
            % (sources[-1].title, targets[-1].title)})
        new_root = "%s/%s" % (attach, sources[-1].slug)
        with transaction.atomic():
            super(BestPracticeMoveAPIView, self).perform_change(
                sources, targets, rank=rank)
            for consumption in Consumption.objects.filter(
                    path__startswith=moved):
                new_path = new_root + consumption.path[len(moved):]
                LOGGER.debug("renames Consumption '%s' to '%s'",
                    consumption.path, new_path)
                consumption.path = new_path
                consumption.save()


class BestPracticeAPIView(BestPracticeMixin, PageElementEditableDetail):
    """
    Retrieves editable details on a practice

    This API returns the text of a single content node identified
    in the content tree by `path`.

    **Tags**: editors

    **Examples

    .. code-block:: http

        GET /api/content/editables/detail/boxes-enclosures/\
energy-efficiency/air-flow HTTP/1.1

    responds

    .. code-block:: json

        {
            "slug": "air-flow",
            "path": "/boxes-enclosures/energy-efficiency/air-flow",
            "title": "Adjust air/fuel ratio",
            "text": "Adjust air/fuel ratio",
            "picture": null,
            "environmental_value": 1,
            "business_value": 1,
            "profitability": 3,
            "implementation_ease": 1,
            "avg_value": 2
        }
    """
    queryset = PageElement.objects.all()
    serializer_class = PageElementSerializer

    def get_object(self):
        trail = self.get_full_element_path(self.path)
        return trail[-1]

    def get(self, request, *args, **kwargs):
        from_root, trail = self.breadcrumbs
        if trail:
            root = self._build_tree(trail[-1][0], from_root)
            return Response(root)
        raise Http404

    def post(self, request, *args, **kwargs):
        """
        Creates a practice

        Updates the title, text and, if applicable, the metrics associated
        associated to the content element referenced by *path*.

        **Tags**: editors

        **Examples

        .. code-block:: http

            POST /api/content/editables/detail/boxes-enclosures/\
energy-efficiency HTTP/1.1

        .. code-block:: json

            {
              "title": "Adjust air/fuel ratio",
            }

        responds:

        .. code-block:: json

            {
              "title": "Adjust air/fuel ratio",
              "tag": "",
              "consumption": {
                "path": "/boxes-enclosures/energy-efficiency/air-flow",
                "text": "Adjust air/fuel ratio",
                "avg_energy_saving": "* * * *",
                "avg_fuel_saving": "-",
                "capital_cost": "$$",
                "payback_period": "0-1.8 (0.3)",
                "environmental_value": 1,
                "business_value": 1,
                "profitability": 3,
                "implementation_ease": 1,
                "avg_value": 2,
                "rank": 3,
                "nb_respondents": 0,
                "rate": 0,
                "opportunity": 0,
                "implemented": "",
                "planned": false
               }
            }

        """
        return super(BestPracticeAPIView, self).create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Updates a practice

        Updates the title, text and, if applicable, the metrics associated
        associated to the content element referenced by *path*.

        **Tags**: editors

        **Examples

        .. code-block:: http

            PUT /api/content/editables/detail/boxes-enclosures/\
energy-efficiency/air-flow/ HTTP/1.1

        .. code-block:: json

            {
              "title": "Adjust air/fuel ratio",
            }

        responds:

        .. code-block:: json

            {
              "title": "Adjust air/fuel ratio",
              "tag": "",
              "consumption": {
                "path": "/boxes-enclosures/energy-efficiency/air-flow",
                "text": "Adjust air/fuel ratio",
                "avg_energy_saving": "* * * *",
                "avg_fuel_saving": "-",
                "capital_cost": "$$",
                "payback_period": "0-1.8 (0.3)",
                "environmental_value": 1,
                "business_value": 1,
                "profitability": 3,
                "implementation_ease": 1,
                "avg_value": 2,
                "rank": 3,
                "nb_respondents": 0,
                "rate": 0,
                "opportunity": 0,
                "implemented": "",
                "planned": false
               }
            }

        """
        #pylint:disable=useless-super-delegation
        return super(BestPracticeAPIView, self).put(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Removes a content tree

        removes content element referenced by path from the content
        hierarchy.

        **Tags**: editors

        **Examples

        .. code-block:: http

            DELETE /api/content/editables/detail/boxes-enclosures/\
energy-efficiency/air-flow/ HTTP/1.1
        """
        #pylint:disable=useless-super-delegation
        return super(BestPracticeAPIView, self).delete(request, *args, **kwargs)


    def _destroy_trees(self, roots):
        if not roots:
            return
        edges = RelationShip.objects.filter(orig_element__in=roots)
        nodes = PageElement.objects.filter(
            pk__in=[edge.dest_element_id for edge in edges])
        edges.delete()
        aliases = RelationShip.objects.filter(dest_element__in=nodes)
        self._destroy_trees(
            nodes.exclude(pk__in=[edge.dest_element_id for edge in aliases]))
        if hasattr(roots, 'delete'):
            roots.delete()
        else:
            PageElement.objects.filter(
                pk__in=[root.pk for root in roots]).delete()

    def perform_create(self, serializer):
        with transaction.atomic():
            element = serializer.save(account=self.account)
            parent = self.element
            rank = RelationShip.objects.filter(
                orig_element=parent).aggregate(Max('rank')).get(
                'rank__max', None)
            rank = 0 if rank is None else rank + 1
            RelationShip.objects.create(
                orig_element=parent, dest_element=element, rank=rank)

    def perform_destroy(self, instance): #pylint:disable=unused-argument
        trail = self.get_full_element_path(self.path)
        from_root = '/%s' % "/".join([element.slug for element in trail])
        if len(trail) > 1:
            with transaction.atomic():
                subtree_root = trail[-1]
                edge = RelationShip.objects.get(
                    orig_element=trail[-2], dest_element=subtree_root)
                edge.delete()
                aliases = RelationShip.objects.filter(dest_element=subtree_root)
                if not aliases.exists():
                    self._destroy_trees([subtree_root])
                Consumption.objects.filter(path__startswith=from_root).delete()

    def perform_update(self, serializer): #pylint:disable=too-many-locals
        with transaction.atomic():
            super(BestPracticeAPIView, self).perform_update(serializer)
            cmpt_serializer = serializer.validated_data.get('consumption', None)
            if cmpt_serializer:
                # Force "Gold" value to be outside the linear scale.
                for field_name in Consumption.VALUE_SUMMARY_FIELDS:
                    if (field_name in cmpt_serializer.validated_data and
                        cmpt_serializer.validated_data[field_name] == 4):
                        cmpt_serializer.validated_data[field_name] = 6
                cmpt_serializer.save()
