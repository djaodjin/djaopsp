# Copyright (c) 2026, DjaoDjin inc.
# see LICENSE.

from dateutil import rrule
from django.db.models import Min
from survey.helpers import datetime_or_now
from survey.models import PortfolioDoubleOptIn

from .utils import get_account_model, send_notification


def send_reminders(organization, email=None, campaign=None, dry_run=False):

    optins = PortfolioDoubleOptIn.objects.pending_for(
        account=organization, campaign=campaign).filter(
        state=PortfolioDoubleOptIn.OPTIN_REQUEST_INITIATED).select_related(
        'campaign', 'grantee')

    if not optins:
        return

    context = {
        'account': {
            'slug': organization.slug,
            'email': organization.email,
            'printable_name': organization.printable_name,
        },
    }
    if email:
        context.update({'recipients': [{'email': email}]})

    requesters_by_campaign = {}
    for optin in optins:
        requesters = requesters_by_campaign.get(optin.campaign)
        if not requesters:
            requesters = []
            requesters_by_campaign.update({optin.campaign: requesters})
        requesters += [optin.grantee]

    for campaign, requesters in requesters_by_campaign.items():
        context.update({
            'campaign': campaign,
            'requesters': requesters
        })
        deadline = PortfolioDoubleOptIn.objects.pending_for(
            account=organization, campaign=campaign).filter(
            state=PortfolioDoubleOptIn.OPTIN_REQUEST_INITIATED).aggregate(
            Min('ends_at')).get('ends_at__min')
        if deadline:
            context.update({
                'deadline': deadline.strftime("%b %d, %Y"),
                'deadline_year': deadline.year,
            })

        if not dry_run:
            send_notification('request_reminder', context=context)
