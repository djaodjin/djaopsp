# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

from pages.api.elements import PageElementAPIView
from survey.helpers import datetime_or_now

from ..compat import gettext_lazy as _
from .base import PracticesXLSXRenderer


class ContentDetailDownloadView(PageElementAPIView):
    """
    Download the practices as a spreadsheet
    """
    schema = None
    base_headers = ['']
    intrinsic_value_headers = ['Environmental', 'Ops/maintenance',
        'Financial', 'Implementation ease', 'AVERAGE VALUE']

    renderer_classes = [PracticesXLSXRenderer]

    def finalize_response(self, request, response, *args, **kwargs):
        resp = super(ContentDetailDownloadView, self).finalize_response(
            request, response, *args, **kwargs)
        filename = datetime_or_now().strftime(
            self.element.slug + '-%Y%m%d.xlsx')
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            filename)
        return resp
