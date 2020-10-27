# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

"""
API URLs
"""
from rules.urldecorators import include, url
from pages.settings import PATH_RE

from ...api.campaigns import ContentElementListAPIView

urlpatterns = [
    # URLs for content editors
    url(r'^content/', include('envconnect.urls.api.editors'),
        decorators=['envconnect.decorators.requires_content_manager']),
    # URLs for authenticated readers (upvote, downvote, etc.)
    url(r'^content/', include('pages.urls.api.readers')),
    # URLs for unauthenticated readers (content tree)
    url(r'^content/(?P<path>%s)$' % PATH_RE,
        ContentElementListAPIView.as_view(), name='api_content'),
    url(r'^content/', include('pages.urls.api.noauth')),
    # URLs for assessments
    url(r'^', include('envconnect.urls.api.suppliers')),
]
