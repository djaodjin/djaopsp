# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from pages.api.elements import (PageElementAPIView as PageElementBaseAPIView,
    PageElementEditableListAPIView as PageElementEditableListBaseAPIView)
from survey.utils import get_question_model

from .serializers import ContentElementSerializer
from ..mixins import VisibilityMixin
from ..utils import get_practice_serializer


class PageElementAPIView(VisibilityMixin, PageElementBaseAPIView):
    """
    """
    serializer_class = ContentElementSerializer
    practice_serializer_class = get_practice_serializer()

    def get_extra_fields(self):
        if hasattr(self.practice_serializer_class.Meta, 'extra_fields'):
            return self.practice_serializer_class.Meta.extra_fields
        return []

    def attach(self, elements):
        extra_fields = self.get_extra_fields()
        values_by_path = {}
        for resp in get_question_model().objects.filter(
            path__in=[elem['path'] for elem in elements]).values(
            'path', *extra_fields):
            path = resp.pop('path')
            values_by_path.update({path: resp})
        for elem in elements:
            path = elem['path']
            values = values_by_path.get(path)
            if values:
                elem.update(values)
        return elements


class PageElementEditableListAPIView(PageElementEditableListBaseAPIView):

    account_url_kwarg = 'profile'
