# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging, os

from django.db import transaction
from django.http import Http404
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from pages.models import RelationShip
from pages.api.relationship import PageElementMoveAPIView

from ..mixins import BestPracticeMixin
from ..models import Consumption
from ..serializers import MoveRankSerializer

LOGGER = logging.getLogger(__name__)


class BestPracticeMoveAPIView(PageElementMoveAPIView):

    def perform_change(self, sources, targets, rank=None):
        moved = '/' + '/'.join([source.slug for source in sources])
        new_root = "/%s/%s" % ('/'.join([target.slug for target in targets]),
            sources[-1].slug)
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



class BestPracticeAPIView(BestPracticeMixin, RetrieveUpdateDestroyAPIView):

    serializer_class = MoveRankSerializer

    def get_object(self):
        return self.best_practice

    def get(self, request, *args, **kwargs):
        from_root, trail = self.breadcrumbs
        if len(trail) > 0:
            root, _, _ = trail[-1]
            root = self._build_tree(root, from_root)
            return Response(self.to_representation(root))
        raise Http404

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer): #pylint:disable=too-many-locals
        # XXX This code has been deprecated. Left until tests are stable.
        attach = self.kwargs.get('path')
        moved = serializer.validated_data['source']
        LOGGER.debug("move '%s' after '%s'", moved, attach)
        _, moved_path_elements = self.get_breadcrumbs(moved)
        _, attach_path_elements = self.get_breadcrumbs(attach)

        if len(moved_path_elements) == len(attach_path_elements):
            attach_root = attach_path_elements[-2][0]
            attach_below = attach_path_elements[-1][0]
            prefix_elements = attach_path_elements[:-1]
            # Implementation Note:
            # Edges are ordered loosily, that is until an edge is moved
            # to a specific position, ranks will all be zero.
            for index, edge in enumerate(RelationShip.objects.filter(
                    orig_element=attach_root).order_by('rank', 'pk')):
                if edge.dest_element.pk == attach_below.pk:
                    pos = index + 1
                    break
        elif len(moved_path_elements) > len(attach_path_elements):
            attach_root = attach_path_elements[-1][0]
            prefix_elements = attach_path_elements
            pos = 0
        else:
            attach_root = attach_path_elements[-3][0]
            attach_below = attach_path_elements[-2][0]
            prefix_elements = attach_path_elements[:-2]
            for index, edge in enumerate(RelationShip.objects.filter(
                    orig_element=attach_root).order_by('rank', 'pk')):
                if edge.dest_element.pk == attach_below.pk:
                    pos = index + 1
                    break
        with transaction.atomic():
            moved_node = moved_path_elements[-1][0]
            new_path = "/%s/%s" % ('/'.join([
                part[0].slug for part in prefix_elements]), moved_node.slug)
            common_prefix = os.path.commonprefix([moved, new_path])
            if len(common_prefix) == 0 or common_prefix == '/':
                raise ValidationError(
                    {'detail': "'%s' and '%s' do not share a root prefix." % (
                    moved, attach)})
            RelationShip.objects.filter(
                orig_element=moved_path_elements[-2][0],
                dest_element=moved_node).delete()
            RelationShip.objects.insert_node(
                attach_root, moved_node, pos=pos)
            try:
                consumption = Consumption.objects.get(path=moved)
                consumption.path = new_path
                consumption.save()
            except Consumption.DoesNotExist:
                pass
