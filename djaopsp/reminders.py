# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

from dateutil import rrule
from django.db.models import Min
from survey.helpers import datetime_or_now
from survey.models import PortfolioDoubleOptIn

from .utils import get_account_model, send_notification


def send_reminders(organization, email=None, dry_run=False):

    requesters = get_account_model().objects.filter(
        pk__in=PortfolioDoubleOptIn.objects.pending_for(
        account=organization).filter(
        state=PortfolioDoubleOptIn.OPTIN_REQUEST_INITIATED).values_list(
        'grantee', flat=True)).distinct()

    if not requesters:
        return

    context = {
        'account': {
            'email': organization.email,
            'printable_name': organization.printable_name,
        },
        'requesters': requesters,
    }
    if email:
        context.update({'recipients': [{'email': email}]})

    deadline = PortfolioDoubleOptIn.objects.pending_for(
        account=organization).filter(
        state=PortfolioDoubleOptIn.OPTIN_REQUEST_INITIATED).aggregate(
        Min('ends_at')).get('ends_at__min')
    if deadline:
        weeks_to_deadline = rrule.rrule(
            rrule.WEEKLY, dtstart=datetime_or_now(),
            until=datetime_or_now(deadline)).count()
        context.update({
            'deadline': deadline.strftime("%b %d, %Y"),
            'deadline_year': deadline.year,
            'weeks_to_deadline': weeks_to_deadline
        })

    if not dry_run:
        send_notification('request_reminder', context=context)
