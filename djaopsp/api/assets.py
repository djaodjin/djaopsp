# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

import logging

from django.http import Http404
from django.db.models import Q
from pages.api.assets import AssetAPIView as AssetBaseAPIView
from survey.models import Portfolio
from survey.queries import datetime_or_now

from ..mixins import VisibilityMixin

LOGGER = logging.getLogger(__name__)


class AssetAPIView(VisibilityMixin, AssetBaseAPIView):

    def get(self, request, *args, **kwargs):
        """
        Expiring link to download asset file

        **Examples

        .. code-block:: http

            GET /api/supplier-1/assets/supporting-evidence.pdf HTTP/1.1

        responds

        .. code-block:: json

            {
              "location": "https://example-bucket.s3.amazon.com\
/supporting-evidence.pdf",
              "updated_at": "2016-10-26T00:00:00.00000+00:00"
            }
        """
        at_time = datetime_or_now()
        if not (self.is_auditor or
            self.account.slug in self.accessible_profiles or
            Portfolio.objects.filter(
                Q(account=self.account) &
                Q(grantee__slug__in=self.accessible_profiles)).exists()):
            raise Http404()

        return super(AssetAPIView, self).get(request, *args, **kwargs)
