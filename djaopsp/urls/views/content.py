# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path, re_path
from ...views.content import (ContentDetailView, ContentIndexView, 
     SequenceProgressView, SequencePageElementView)


urlpatterns = [
    path('sequences/<slug:sequence>/', 
         SequenceProgressView.as_view(), name='sequence_progress_view'),
    re_path(r'sequences/(?P<sequence>[^/]+)/(?P<rank>-?\d+)/',
          SequencePageElementView.as_view(),
          name='sequence_page_element_view'),
    path('<path:path>/',
         ContentDetailView.as_view(), name='pages_element'),
    path('',
         ContentIndexView.as_view(), name='pages_index'),
]
