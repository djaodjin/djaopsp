# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
API URLs
"""
from django.urls import path, include
from ...api.samples import SampleAnswersAPIView

urlpatterns = [
    path('editables/<slug:profile>/', include('djaopsp.urls.api.editors')),
    path('content/editables/<slug:profile>/',
         include('pages.urls.api.editables')),
    path('content/', include('pages.urls.api.readers')),
    path('', include('survey.urls.api.noauth')),
#    path('<slug:profile>/sample/<slug:sample>)/answers/<path:path>',
#       SampleAnswersAPIView.as_view(), name='survey_api_sample_answers_path'),
    path('<slug:profile>/sample/<slug:sample>)/answers/',
       SampleAnswersAPIView.as_view(), name='survey_api_sample_answers'),
    path('<slug:profile>/', include('survey.urls.api.campaigns')),
    path('<slug:profile>/', include('survey.urls.api.sample')),

]
