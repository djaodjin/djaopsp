# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

import json

from deployutils.helpers import datetime_or_now
from saas.models import Subscription


def is_testing(account):
    """
    Returns `True` if `account` is a test account.
    """
    try:
        extra = json.loads(account.extra)
    except (IndexError, TypeError, ValueError) as err:
        extra = {}
    return bool(extra.get('testing'))


def get_supplier_managers(account, ends_at=None):
    ends_at = datetime_or_now(ends_at)
    queryset = Subscription.objects.filter(
        ends_at__gt=ends_at, organization=account)
    if is_testing(account):
        queryset = queryset.filter(
            plan__organization__extra__contains='testing')
    else:
        queryset = queryset.exclude(
            plan__organization__extra__contains='testing')
    queryset = queryset.select_related(
        'plan__organization').values_list(
        'plan__organization__slug', 'plan__organization__full_name')
    supplier_managers = [{
        'slug': supplier_manager[0], 'printable_name': supplier_manager[1]} for
            supplier_manager in queryset]
    return supplier_managers
