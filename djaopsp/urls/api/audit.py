# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

"""
API URLs for verifier notes and reports
"""
from django.urls import path

from ...api.audits import VerifierNotesIndexAPIView, VerifiedStatsAPIView

urlpatterns = [
    path('sample/<slug:sample>/notes',
        VerifierNotesIndexAPIView.as_view(),
        name='api_verifier_notes_index'),
    path('reporting/notes',
         VerifiedStatsAPIView.as_view(),
         name="api_verified_aggregate"),
]
