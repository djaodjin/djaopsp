# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

"""
Decorators to check content management permissions.
"""
from __future__ import unicode_literals

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import available_attrs
from pages.models import PageElement


def requires_content_manager(function=None):
    """
    Decorator for views that checks that the authenticated ``request.user``
    is a manager of the account the content belongs to.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if request.method.lower() in ['post', 'put', 'patch', 'delete']:
                path = kwargs.get('path', kwargs.get('slug', None))
                if path:
                    slug = path.split('/')[-1]
                    page_element = get_object_or_404(PageElement, slug=slug)
                    account_slug = str(page_element.account)
                    found = False
                    for organization in request.session.get(
                            'roles', {}).get('manager', []):
                        if account_slug == organization['slug']:
                            found = True
                            break
                    if not found:
                        raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view

    if function:
        return decorator(function)
    return decorator
