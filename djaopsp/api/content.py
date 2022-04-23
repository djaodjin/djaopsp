# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from pages.api.elements import (PageElementAPIView as PageElementBaseAPIView,
PageElementEditableListAPIView as PageElementEditableListBaseAPIView)

from ..mixins import VisibilityMixin


class PageElementAPIView(VisibilityMixin,
                         PageElementBaseAPIView):
    """
    """


class PageElementEditableListAPIView(PageElementEditableListBaseAPIView):

    account_url_kwarg = 'profile'
