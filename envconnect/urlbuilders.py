# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from django.conf import settings
from rules.urldecorators import url

if settings.DEBUG:
    # In debug mode we add a path_prefix such that we can test
    # the webapp through the session proxy.
    APP_PREFIX = '%s/' % settings.APP_NAME
else:
    APP_PREFIX = ''

def url_prefixed(regex, view, name=None, decorators=None):
    """
    Returns a urlpattern prefixed with the APP_NAME in debug mode.
    """
    return url(r'^%(app_prefix)s%(regex)s' % {
        'app_prefix': APP_PREFIX, 'regex': regex}, view, name=name,
        decorators=decorators)


# XXX ``views.AccountRedirectView`` will attempt to create a new Organization
# if we don't test for an authenticated User first.
def url_authenticated(regex, view, name=None):
    """
    Returns a urlpattern accessible to an authenticated user.
    """
    return url_prefixed(regex, view, name=name,
        decorators=['django.contrib.auth.decorators.login_required'])


def url_content_manager(regex, view, name=None):
    """
    Builds URLs for a direct decorator.
    """
    return url_prefixed(regex, view, name=name,
        decorators=['envconnect.decorators.requires_content_manager'])


def url_direct(regex, view, name=None):
    """
    Builds URLs for a direct decorator.
    """
    return url_prefixed(regex, view, name=name,
        decorators=['django.contrib.auth.decorators.login_required'])
