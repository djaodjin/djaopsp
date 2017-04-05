# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from django.conf import settings
from django.conf.urls import url

from ...api.benchmark import BenchmarkAPIView
from ...api.improvements import (ImprovementListAPIView,
    ImprovementToggleAPIView)


urlpatterns = [
    url(r'benchmark(?P<path>%s)/?' % settings.PATH_RE,
        BenchmarkAPIView.as_view(),
        name="api_benchmark"),
    url(r'improvement(?P<path>%s)/?' % settings.PATH_RE,
        ImprovementToggleAPIView.as_view(),
        name='api_improvement'),
    url(r'improvement/?', ImprovementListAPIView.as_view(),
        name='api_improvement_base'),
]
