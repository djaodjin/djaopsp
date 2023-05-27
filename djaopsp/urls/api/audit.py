# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

"""
API URLs for portfolios engagement & analytics dashboards
"""
from django.urls import path

from ...api.audits import VerifierNotesAPIView, VerifierNotesIndexAPIView

urlpatterns = [
    path('sample/<slug:sample>/notes/<path:path>',
        VerifierNotesAPIView.as_view(), name='api_verifier_notes'),
    path('sample/<slug:sample>/notes',
        VerifierNotesIndexAPIView.as_view(),
        name='api_verifier_notes_index'),
]
