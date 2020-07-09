# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

"""
API URLs
"""
from rules.urldecorators import include, url


urlpatterns = [
    # URLs for content editors
    url(r'^content/editables/', include('envconnect.urls.api.editors'),
        decorators=['envconnect.decorators.requires_content_manager']),
    # URLs for authenticated readers (upvote, downvote, etc.)
    url(r'^content/', include('answers.urls.api')),
    # URLs for unauthenticated readers (content tree)
    url(r'^content/', include('pages.urls.api.readers')),
    # URLs for assessments
    url(r'^', include('envconnect.urls.api.suppliers')),
]
