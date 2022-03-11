# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
Views URLs for campaign editors
"""
from django.urls import path
from survey.views.campaigns import CampaignListView

from ...views.campaigns import CampaignEditView, CampaignXLSXView


urlpatterns = [
    # Assessment campaigns editors
    path('campaigns/<slug:campaign>/download/',
        CampaignXLSXView.as_view(), name='campaign_download'),
    path('campaigns/<slug:campaign>/',
        CampaignEditView.as_view(), name='campaign_edit'),
    path('campaigns/',
        CampaignListView.as_view(), name='survey_campaign_list'),
]
