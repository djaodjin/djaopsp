# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from django.db import transaction
from django.db.models import F
from rest_framework import generics
from rest_framework.response import Response

from ..mixins import BreadcrumbMixin
from ..models import ColumnHeader, Consumption
from ..serializers import ColumnHeaderSerializer


class ColumnAPIView(BreadcrumbMixin, generics.RetrieveUpdateAPIView):
    """
    This API end-point toggles columns / `Consumption` fields to be visible
    or hidden. The visible/hidden status of a column will have an effect
    of how average values are computed.
    A a result, on `update` we return the content tree that was updated
    instead of the `Column` instance because the user interface will
    want a chance to refresh the display accordingly.
    """

    lookup_field = 'path'
    serializer_class = ColumnHeaderSerializer

    def get_queryset(self):
        return ColumnHeader.objects.filter(path=self.kwargs.get('path'))

    def get_object(self):
        path = self.kwargs.get('path')
        slug = self.request.data.get('slug')
        try:
            obj = self.get_queryset().get(slug=slug)
        except ColumnHeader.DoesNotExist:
            obj = ColumnHeader(path=path, slug=slug)
        return obj

    def perform_update(self, serializer):
        path = self.kwargs.get('path')
        with transaction.atomic():
            serializer.save()
            visible_cols = Consumption.VALUE_SUMMARY_FIELDS - set([
                col.slug for col in self.get_queryset().filter(hidden=True)])
            nb_visible_cols = len(visible_cols)
            if nb_visible_cols > 0:
                query_params = None
                for col in visible_cols:
                    if query_params is None:
                        query_params = F(col)
                    else:
                        query_params += F(col)
                # Round to nearst:
                query_params = (
                    query_params + nb_visible_cols // 2) / nb_visible_cols
                Consumption.objects.filter(
                    path__startswith=path).update(avg_value=query_params)

    def update(self, request, *args, **kwargs):#pylint:disable=unused-argument
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # `update` will force recomputation of `avg_value`. We return
        # the content tree that was updated for the user interface to
        # refresh the display accordingly.
        from_root, trail = self.breadcrumbs
        if len(trail) > 0:
            root = self._build_tree(trail[-1][0], from_root)
            return Response(root)
        return Response(serializer.data)
