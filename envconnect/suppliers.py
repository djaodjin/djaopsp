# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

from deployutils.helpers import datetime_or_now
from saas.models import Subscription


def get_supplier_managers(account):
    ends_at = datetime_or_now()
    supplier_managers = [{
        'slug': supplier_manager[0], 'printable_name': supplier_manager[1]} for
            supplier_manager in Subscription.objects.filter(
                ends_at__gt=ends_at, organization=account).select_related(
                'plan__organization').values_list(
                'plan__organization__slug', 'plan__organization__full_name')]
    print("XXX suppliers for %s (%s) = %s" % (account, account.__class__, supplier_managers))
    return supplier_managers
