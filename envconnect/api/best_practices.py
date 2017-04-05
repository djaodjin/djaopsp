# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from django.db import transaction
from django.http import Http404
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from pages.models import RelationShip

from ..mixins import BestPracticeMixin
from ..models import Consumption
from ..serializers import MoveRankSerializer


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

    def perform_update(self, serializer):
        moved = self.kwargs.get('path')
        attach = serializer.validated_data['attach_below']
        _, moved_path_elements = self.get_breadcrumbs(moved)
        _, attach_path_elements = self.get_breadcrumbs(attach)

        if len(moved_path_elements) == len(attach_path_elements):
            attach_root = attach_path_elements[-2][0]
            attach_below = attach_path_elements[-1][0]
            prefix_elements = attach_path_elements[:-1]
            pos = RelationShip.objects.filter(
                orig_element=attach_root,
                dest_element=attach_below).first().rank + 1
        elif len(moved_path_elements) > len(attach_path_elements):
            attach_root = attach_path_elements[-1][0]
            prefix_elements = attach_path_elements
            pos = 0
        else:
            attach_root = attach_path_elements[-3][0]
            attach_below = attach_path_elements[-2][0]
            prefix_elements = attach_path_elements[:-2]
            pos = RelationShip.objects.filter(
                orig_element=attach_root,
                dest_element=attach_below).first().rank + 1

        with transaction.atomic():
            moved_node = moved_path_elements[-1][0]
            RelationShip.objects.filter(
                orig_element=moved_path_elements[-2][0],
                dest_element=moved_node).delete()
            RelationShip.objects.insert_node(
                attach_root, moved_node, pos=pos)
            try:
                consumption = Consumption.objects.get(path=moved)
                new_prefix = '/'.join([
                    part[0].slug for part in prefix_elements])
                consumption.path = "/%s/%s" % (new_prefix, moved_node.slug)
                consumption.save()
            except Consumption.DoesNotExist:
                pass
