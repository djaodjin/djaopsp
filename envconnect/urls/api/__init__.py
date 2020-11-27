# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

"""
API URLs
"""
from rules.urldecorators import include, url
from pages.settings import PATH_RE

from ...api.campaigns import (ContentDetailAPIView, ContentSearchAPIView,
  ContentListAPIView)

urlpatterns = [
    # URLs for content editors
    url(r'^content/', include('envconnect.urls.api.editors'),
        decorators=['envconnect.decorators.requires_content_manager']),
    # URLs for authenticated readers (upvote, downvote, etc.)
    url(r'^content/', include('pages.urls.api.readers')),
    # URLs for unauthenticated readers (override 'pages.urls.api.noauth')
    url(r'^content/search',
        ContentSearchAPIView.as_view(), name='api_page_element_search'),
    url(r'content/detail/(?P<path>%s)$' % PATH_RE,
        ContentDetailAPIView.as_view(), name='pages_api_pageelement'),
    url(r'^content/(?P<path>%s)$' % PATH_RE,
        ContentListAPIView.as_view(), name='api_content'),

    # URLs for assessments
    url(r'^', include('envconnect.urls.api.suppliers')),
]
