# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import decimal, json, logging, re

from django.db import transaction
from django.db.models import Max
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (get_object_or_404,
    RetrieveUpdateDestroyAPIView, UpdateAPIView)
from rest_framework.response import Response
from pages.mixins import TrailMixin
from pages.models import PageElement, RelationShip
from pages.api.relationship import (PageElementMirrorAPIView,
    PageElementMoveAPIView)
from survey.models import SurveyModel

from ..mixins import BestPracticeMixin, BreadcrumbMixin
from ..models import Consumption
from ..serializers import PageElementSerializer

LOGGER = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):

    def default(self, obj): #pylint: disable=method-hidden
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class ToggleTagContentAPIView(TrailMixin, UpdateAPIView):

    added_tag = None
    removed_tag = None

    def update(self, request, *args, **kwargs):
        trail = self.get_full_element_path(self.kwargs.get('path'))
        element = trail[-1]
        extra = {}
        try:
            extra = json.loads(element.tag)
        except (TypeError, ValueError):
            pass
        if 'tags' not in extra:
            if self.added_tag:
                extra.update({'tags': self.added_tag})
        else:
            if self.removed_tag and self.removed_tag in extra['tags']:
                extra['tags'].remove(self.removed_tag)
            if self.added_tag and not self.added_tag in extra['tags']:
                extra['tags'].append(self.added_tag)
        element.tag = json.dumps(extra, cls=DecimalEncoder)
        element.save()
        return Response(element.tag)


class EnableContentAPIView(ToggleTagContentAPIView):
    """
    Enable a top level segment.
    """
    added_tag = "enabled"
    removed_tag = "disabled"


class DisableContentAPIView(ToggleTagContentAPIView):
    """
    Disable a top level segment.
    """
    added_tag = "disabled"
    removed_tag = "enabled"


class BestPracticeMirrorAPIView(BreadcrumbMixin, PageElementMirrorAPIView):
    """
    This API end-point mirrors content element under another node.

    A a result, we return the content tree that was updated
    instead of the `Column` instance because the user interface will
    want a chance to refresh the display accordingly.
    """

    report_title = 'Best Practices Report'

    @property
    def survey(self):
        if not hasattr(self, '_survey'):
            self._survey = get_object_or_404(
                SurveyModel.objects.all(), title=self.report_title)
        return self._survey

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        targets = self.get_full_element_path(self.kwargs.get('path', None))
        sources = self.get_full_element_path(serializer.validated_data.get(
            'source'))
        self.valid_against_loop(sources, targets)
        node = self.perform_change(sources, targets,
            rank=serializer.validated_data.get('rank', None))
        prefix = self.kwargs.get('path', None)
        root = self._build_tree(node, prefix + '/' + node.slug)
        headers = self.get_success_headers(root)
        return Response(root, status=status.HTTP_201_CREATED, headers=headers)

    def mirror_leaf(self, leaf, prefix="", new_prefix=""):
        last_rank = self.survey.questions.aggregate(
            Max('rank')).get('rank__max', 0)
        rank = 0 if last_rank is None else last_rank + 1
        for consumption in Consumption.objects.filter(
                path__startswith=prefix):
            new_path = None
            look = re.match(r"^%s/(.*)$" % prefix, consumption.path)
            if look:
                new_path = new_prefix + "/" + look.group(1)
            elif consumption.path == prefix:
                new_path = new_prefix
            if new_path:
                Consumption.objects.get_or_create(path=new_path,
                    defaults={
                        'environmental_value': consumption.environmental_value,
                        'business_value': consumption.business_value,
                        'implementation_ease': consumption.implementation_ease,
                        'profitability': consumption.profitability,
                        'avg_energy_saving': consumption.avg_energy_saving,
                        'avg_fuel_saving': consumption.avg_fuel_saving,
                        'capital_cost_low': consumption.capital_cost_low,
                        'capital_cost_high': consumption.capital_cost_high,
                        'capital_cost': consumption.capital_cost,
                        'payback_period': consumption.payback_period,
                        'survey': self.survey,
                        'rank': rank
                    })
            rank = rank + 1
        return leaf


class BestPracticeMoveAPIView(PageElementMoveAPIView):

    def post(self, request, *args, **kwargs):#pylint: disable=unused-argument
        LOGGER.debug("move %s under %s", request.data, kwargs.get('path'))
        return super(BestPracticeMoveAPIView, self).post(
            request, *args, **kwargs)

    def perform_change(self, sources, targets, rank=None):
        moved = "/" + "/".join([source.slug for source in sources])
        attach = "/" + "/".join([target.slug for target in targets])
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


# XXX should not derive from BestPracticeMixin but PageElement instead?
class BestPracticeAPIView(BestPracticeMixin, RetrieveUpdateDestroyAPIView):
    """
    This API end-point manages a content element referenced by a *path*
    from the root of the content hierarchy.

    ``GET`` returns the content tree rooted at the content element referenced
    by *path*. It includes the title, text and, if applicable, the metrics
    associated to the content elements in the tree.

    **Example request**:

    .. sourcecode:: http

        GET /api/content/detail/boxes-enclosures/energy-efficiency/

    **Example response**:

    .. sourcecode:: http

        [
          {
            "slug": "energy-efficiency",
            "path": "/boxes-enclosures/energy-efficiency",
            "title": "Energy Efficiency",
            "tag": "system",
            "rank": null,
            "is_empty": true,
            "consumption": null
          },
          [
            [
              {
                "slug": "air-flow",
                "path": "/boxes-enclosures/energy-efficiency/air-flow",
                "title": "Adjust air/fuel ratio",
                "tag": "",
                "rank": 0,
                "is_empty": false,
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
              },
              []
            ]
          ]
        ]

    ``PUT`` updates the title, text and, if applicable, the metrics associated
    associated to the content element referenced by *path*.

    **Example request**:

    .. sourcecode:: http

        PUT /api/content/detail/boxes-enclosures/energy-efficiency/air-flow/

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

    **Example response**:

    .. sourcecode:: http

    XXX

   ``DELETE`` removes content element referenced by path from the content
    hierarchy.

    **Example request**:

    .. sourcecode:: http

        DELETE /api/content/detail/boxes-enclosures/energy-efficiency/air-flow/

    """
    queryset = PageElement.objects.all()
    serializer_class = PageElementSerializer

    def get_object(self):
        return self.best_practice

    def get(self, request, *args, **kwargs):
        from_root, trail = self.breadcrumbs
        if len(trail) > 0:
            root = self._build_tree(trail[-1][0], from_root)
            return Response(root)
        raise Http404

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

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

    def perform_destroy(self, instance): #pylint:disable=unused-argument
        trail = self.get_full_element_path(self.kwargs.get('path'))
        from_root = "/" + "/".join([element.slug for element in trail])
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
            cmpt_serializer = serializer.get('consumption', None)
            if cmpt_serializer:
                # Force "Gold" value to be outside the linear scale.
                for field_name in Consumption.VALUE_SUMMARY_FIELDS:
                    if (field_name in cmpt_serializer.validated_data and
                        cmpt_serializer.validated_data[field_name] == 4):
                        cmpt_serializer.validated_data[field_name] = 6
                cmpt_serializer.save()
