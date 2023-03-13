# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
API URLs
"""
from django.urls import path, include
from ...api.campaigns import (CampaignEditableSegmentsAPIView,
    CampaignEditableContentAPIView, CampaignUploadAPIView)

urlpatterns = [
    path('campaigns/<slug:campaign>/upload',
        CampaignUploadAPIView.as_view(),
         name='api_campaign_upload'),
    path('campaigns/<slug:campaign>/segments',
        CampaignEditableSegmentsAPIView.as_view(),
         name='api_campaign_editable_segments'),
    path('campaigns/<slug:campaign>',
        CampaignEditableContentAPIView.as_view(),
        name='api_campaign_editable_content'),
    path('', include('pages.urls.api.editables'))
]
