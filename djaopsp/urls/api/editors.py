# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

"""
API URLs
"""
from django.urls import path, include

from ...api.content import PageElementEditableListAPIView
from ...api.campaigns import (CampaignEditableSegmentsAPIView,
    CampaignEditableContentAPIView, CampaignEditableQuestionAPIView,
    CampaignUploadAPIView)


urlpatterns = [
    path('content',
        PageElementEditableListAPIView.as_view(),
        name="pages_api_editables_index"),
    path('campaigns/<slug:campaign>/upload',
        CampaignUploadAPIView.as_view(),
         name='api_campaign_upload'),
    path('campaigns/<slug:campaign>/segments',
        CampaignEditableSegmentsAPIView.as_view(),
         name='api_campaign_editable_segments'),
    path('campaigns/<slug:campaign>/<path:path>',
        CampaignEditableQuestionAPIView.as_view(),
        name='api_campaign_editable_question'),
    path('campaigns/<slug:campaign>',
        CampaignEditableContentAPIView.as_view(),
        name='survey_api_campaign'),
    path('', include('survey.urls.api.campaigns')),
    path('', include('pages.urls.api.editables'))
]
