# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

from rest_framework.views import exception_handler


def drf_exception_handler(exc, context):
    """
    Handler to capture input parameters when a 500 exception occurs.
    """
    # XXX This is not ideal as it doesn't show the actual text - still better
    #     than nothing.
    request = context.get('request', None)
    if request and request.method not in ['GET', 'HEAD', 'OPTIONS']:
        #pylint:disable=protected-access
        if not request._request.POST:
            request._request.POST = request.data
    response = exception_handler(exc, context)
    return response
