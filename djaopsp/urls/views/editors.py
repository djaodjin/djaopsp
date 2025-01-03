# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
Views URLs for campaign editors
"""
from django.urls import path
from survey.views.campaigns import CampaignListView

from ...downloads.campaigns import CampaignXLSXView
from ...views.content import EditablesIndexView, EditablesDetailView
from ...views.campaigns import CampaignEditView


urlpatterns = [
    # Assessment campaigns editors
    path('campaigns/<slug:campaign>/download/',
        CampaignXLSXView.as_view(), name='campaign_download'),
    path('campaigns/<slug:campaign>/',
        CampaignEditView.as_view(), name='campaign_edit'),
    path('campaigns/',
        CampaignListView.as_view(), name='survey_campaign_list'),
    path('editables/<path:path>/',
        EditablesDetailView.as_view(), name='pages_editables_element'),
    path('editables/',
        EditablesIndexView.as_view(), name='pages_editables_index'),
]
