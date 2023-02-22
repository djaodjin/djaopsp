# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path

from ...views.content import ContentDetailView, ContentIndexView


urlpatterns = [
    path('<path:path>/',
         ContentDetailView.as_view(), name='pages_element'),
    path('',
         ContentIndexView.as_view(), name='pages_index'),
]
