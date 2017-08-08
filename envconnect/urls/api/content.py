# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from django.conf import settings
from django.conf.urls import url

from ...api.benchmark import ScoreWeightAPIView
from ...api.best_practices import (BestPracticeAPIView,
    BestPracticeAliasAPIView, BestPracticeMoveAPIView)
from ...api.columns import ColumnAPIView
from ...api.consumption import ConsumptionListAPIView, ConsumptionDetailAPIView


urlpatterns = [
    url(r'score(?P<path>%s)/?' % settings.PATH_RE,
      ScoreWeightAPIView.as_view(), name="api_score"),
    url(r'score/?',
      ScoreWeightAPIView.as_view(), name="api_score_base"),
    url(r'consumption(?P<path>%s)/' % settings.PATH_RE,
      ConsumptionDetailAPIView.as_view(), name="api_consumption"),
    url(r'consumption/?',
      ConsumptionListAPIView.as_view(), name="api_consumption_base"),
    url(r'^alias(?P<path>%s)/$' % settings.PATH_RE,
      BestPracticeAliasAPIView.as_view(), name='api_alias_detail'),
    url(r'^attach(?P<path>%s)' % settings.PATH_RE,
      BestPracticeMoveAPIView.as_view(), name='api_move_detail'),
    url(r'detail(?P<path>%s)' % settings.PATH_RE,
      BestPracticeAPIView.as_view(), name="api_detail"),
    url(r'column(?P<path>%s)/?' % settings.PATH_RE,
      ColumnAPIView.as_view(), name="api_column"),
    url(r'column/?',
      ColumnAPIView.as_view(), name="api_column_base"),
]
