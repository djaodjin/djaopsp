# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path, re_path
from pages.views.sequences import CertificateDownloadView

from ...views.content import (ContentDetailView, ContentIndexView,
     SequenceProgressView, SequencePageElementView)


urlpatterns = [
    path('sequences/<slug:sequence>/',
         SequenceProgressView.as_view(), name='sequence_progress_view'),
    re_path(r'sequences/(?P<sequence>[^/]+)/(?P<rank>-?\d+)/',
          SequencePageElementView.as_view(),
          name='sequence_page_element_view'),
    path('sequences/<slug:sequence>/certificate/',
         CertificateDownloadView.as_view(),
         name='certificate_download'),
    path('<path:path>/',
         ContentDetailView.as_view(), name='pages_element'),
    path('',
         ContentIndexView.as_view(), name='pages_index'),
]
