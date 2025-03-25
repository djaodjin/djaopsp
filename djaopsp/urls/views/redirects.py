# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.

"""
Views URLs
"""
from django.urls import path
from ...views.app import GetStartedView


urlpatterns = [
    path('getstarted/<slug:campaign>/<path:path>/',
        GetStartedView.as_view(), name='getstarted_campaign_path'),
    path('getstarted/<slug:campaign>/',
        GetStartedView.as_view(), name='getstarted_campaign'),
    path('getstarted/',
        GetStartedView.as_view(), name='getstarted'),
]
