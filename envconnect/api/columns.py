# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from rest_framework import generics

from ..models import ColumnHeader
from ..serializers import ColumnHeaderSerializer


class ColumnAPIView(generics.RetrieveUpdateAPIView):

    lookup_field = 'path'
    queryset = ColumnHeader.objects.all()
    serializer_class = ColumnHeaderSerializer

    def get_object(self):
        path = self.kwargs.get('path')
        slug = self.request.data.get('slug')
        try:
            obj = self.get_queryset().get(path=path, slug=slug)
        except ColumnHeader.DoesNotExist:
            obj = ColumnHeader(path=path, slug=slug)
        return obj
