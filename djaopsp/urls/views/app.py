# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path

from ...views.app import AppView, GetStartedProfileView


urlpatterns = [
    path('getstarted/<slug:campaign>/<path:path>/',
        GetStartedProfileView.as_view(),
        name='profile_getstarted_campaign_path'),
    path('getstarted/<slug:campaign>/',
        GetStartedProfileView.as_view(),
        name='profile_getstarted_campaign'),
    path('getstarted/',
        GetStartedProfileView.as_view(),
        name='profile_getstarted'),
    path('', AppView.as_view(), name='app'),
]
