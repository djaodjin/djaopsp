# Copyright (c) 2026, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path
from pages.views.sequences import CertificateDownloadView

from ...views.content import (ContentDetailView, ContentIndexView,
    SequenceProgressView, SequencePageElementView)
from ...downloads.content import ContentDetailDownloadView


urlpatterns = [
    path('sequences/<slug:sequence>/',
         SequenceProgressView.as_view(), name='sequence_progress_view'),
    path(r'sequences/<slug:sequence>/<int:rank>/',
          SequencePageElementView.as_view(),
          name='sequence_page_element_view'),
    path('sequences/<slug:sequence>/certificate/',
         CertificateDownloadView.as_view(),
         name='certificate_download'),
    path('download/<path:path>/',
         ContentDetailDownloadView.as_view(), name='pages_element_download'),
    path('<path:path>/',
         ContentDetailView.as_view(), name='pages_element'),
    path('',
         ContentIndexView.as_view(), name='pages_index'),
]
