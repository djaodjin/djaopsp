# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from django.conf.urls import url, include
from pages.settings import PATH_RE, SLUG_RE

from ...api.benchmark import (DisableScorecardAPIView, EnableScorecardAPIView,
    ScoreWeightAPIView)
from ...api.best_practices import (BestPracticeAPIView,
    BestPracticeMirrorAPIView, BestPracticeMoveAPIView,
    EnableContentAPIView, DisableContentAPIView)
from ...api.columns import ColumnAPIView
from ...api.consumption import (ConsumptionListAPIView,
    ConsumptionEditableDetailAPIView)


urlpatterns = [
# XXX move into editables/score/
#    url(r'^editables/enable/(?P<path>%s)$' % PATH_RE,
#      EnableContentAPIView.as_view(), name="api_enable"),
#    url(r'^editables/disable/(?P<path>%s)$' % PATH_RE,
#      DisableContentAPIView.as_view(), name="api_disable"),
#    url(r'^editables/scorecard/enable/(?P<path>%s)$' % PATH_RE,
#      EnableScorecardAPIView.as_view(), name="api_scorecard_enable"),
#    url(r'^editables/scorecard/disable/(?P<path>%s)$' % PATH_RE,
#      DisableScorecardAPIView.as_view(), name="api_scorecard_disable"),
    url(r'^editables/(?P<organization>%s)/score/(?P<path>%s)$' % (
        SLUG_RE, PATH_RE),
        ScoreWeightAPIView.as_view(), name="api_score"),

    url(r'^editables/column/(?P<path>%s)$' % PATH_RE,
        ColumnAPIView.as_view(), name="api_column"),
    url(r'^editables/(?P<organization>%s)/values$' % SLUG_RE,
        ConsumptionListAPIView.as_view(), name="api_consumption_base"),
    url(r'^editables/(?P<organization>%s)/values/(?P<path>%s)$' % (
        SLUG_RE, PATH_RE),
      ConsumptionEditableDetailAPIView.as_view(), name="api_consumption"),

    url(r'^editables/(?P<organization>%s)/(?P<path>%s)$' % (SLUG_RE, PATH_RE),
        BestPracticeAPIView.as_view(), name='pages_api_edit_element'),

    url(r'^editables/(?P<organization>%s)/attach/(?P<path>%s)$' % (
        SLUG_RE, PATH_RE),
      BestPracticeMoveAPIView.as_view(), name='api_move_node'),
    url(r'^editables/(?P<organization>%s)/mirror/(?P<path>%s)$' % (
        SLUG_RE, PATH_RE),
      BestPracticeMirrorAPIView.as_view(), name='api_mirror_node'),
    url(r'^editables/(?P<organization>%s)/',
        include('pages.urls.api.editables')),
]
