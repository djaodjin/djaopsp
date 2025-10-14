# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path, re_path

from ...views.app import ProfileAppView, GetStartedProfileView


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
    # Use a `re_path` such that clicking on subscriber in djaoapp does
    # not result in a 404.
    re_path(r'[a-zA-Z\-/]*', ProfileAppView.as_view(), name='app_profile'),
]
