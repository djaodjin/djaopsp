# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE
import logging

from django.conf import settings
from django.dispatch import receiver
from survey.signals import (portfolios_grant_initiated,
    portfolios_request_initiated, portfolio_request_accepted)

from ..compat import reverse
from ..utils import send_notification, get_latest_completed_assessment
from .serializers import (PortfolioGrantInitiatedSerializer,
    PortfolioNotificationSerializer)

LOGGER = logging.getLogger(__name__)


# We insure the method is only bounded once no matter how many times
# this module is loaded by using a dispatch_uid as advised here:
#   https://docs.djangoproject.com/en/dev/topics/signals/
@receiver(portfolios_grant_initiated,
    dispatch_uid="portfolios_grant_initiated_notice")
def portfolios_grant_initiated_notice(sender, portfolios, invitee, message,
                                      request, **kwargs):
    """
    Portfolio grant initiated

    **Tags: notification

    **Example

    .. code-block:: json

        {
          "event": "portfolios_grant_initiated",
          "back_url": "{{api_base_url}}",
        }
    """
    #pylint:disable=unused-argument
    LOGGER.debug("[signal] portfolios_grant_initiated_notice(portfolios=%s,"\
        "invitee=%s)", portfolios, invitee)
    if False:
        # XXX figure out which back_url to use, as well as structure
        # of `context`.
        for portfolio in portfolios:
            back_url = request.build_absolute_uri(
                reverse('portfolios_grant_accept',
                    args=(portfolio.grantee, portfolio.verification_key)))
            context = {
                'back_url': back_url,
                'invitee': invitee,
                'created_at': portfolio.created_at,
                'account': portfolio.account,
                'campaign': portfolio.campaign,
                'ends_at': portfolio.ends_at,
                'state': portfolio.state,
                'initiated_by': portfolio.initiated_by,
            }
            send_notification('portfolios_grant_initiated',
                context=PortfolioGrantInitiatedSerializer().to_representation(
                context))


# We insure the method is only bounded once no matter how many times
# this module is loaded by using a dispatch_uid as advised here:
#   https://docs.djangoproject.com/en/dev/topics/signals/
@receiver(portfolios_request_initiated,
    dispatch_uid="portfolios_request_initiated_notice")
def portfolios_request_initiated_notice(sender, portfolios, invitee, message,
                                        request, **kwargs):
    """
    Portfolio request initiated

    **Tags: notification

    **Example

    .. code-block:: json

        {
          "event": "portfolios_request_initiated",
          "back_url": "{{api_base_url}}",
        }
    """
    #pylint:disable=unused-argument
    portfolio = portfolios[0] # XXX first one only
    LOGGER.debug("[signal] portfolios_request_initiated_notice("\
        "portfolio=%s, invitee=%s)", portfolio, invitee)
    back_url = request.build_absolute_uri(reverse('profile_getstarted', args=(
        portfolio.account,)))

    # XXX `slug` is not passed by the proxy
    broker = request.session.get('site', {})
    context = {
        'back_url': back_url,
        'broker': {
            'slug': settings.APP_NAME,
            'full_name': broker.get('printable_name'),
            'printable_name': broker.get('printable_name'),
            'email': broker.get('email')
        },
        'account': portfolio.account,
        'campaign': portfolio.campaign,
        'grantee': portfolio.grantee,
        'originated_by': request.user,
        'message': message
    }
    send_notification('portfolios_request_initiated',
      context=PortfolioNotificationSerializer().to_representation(context))


# We insure the method is only bounded once no matter how many times
# this module is loaded by using a dispatch_uid as advised here:
#   https://docs.djangoproject.com/en/dev/topics/signals/
@receiver(portfolio_request_accepted,
    dispatch_uid="portfolio_request_accepted_notice")
def portfolio_request_accepted_notice(sender, portfolio, request, **kwargs):
    """
    Portfolio request accepted

    **Tags: notification

    **Example

    .. code-block:: json

        {
          "event": "portfolio_request_accepted",
          "back_url": "{{api_base_url}}",
        }
    """
    #pylint:disable=unused-argument
    LOGGER.debug("[signal] portfolio_request_accepted_notice(portfolio=%s)",
        portfolio)
    latest_completed_assessment = get_latest_completed_assessment(
        portfolio.account, portfolio.campaign)
    if not latest_completed_assessment:
        # We are granting access to data that does not exist (yet).
        # Let's not confuse anyone.
        return
    back_url = request.build_absolute_uri(reverse('scorecard',
        args=(portfolio.grantee, latest_completed_assessment)))
    context = {
        'back_url': back_url,
        'account': portfolio.account,
        'campaign': portfolio.campaign,
        'last_completed_at': latest_completed_assessment.created_at.date(),
        'grantee': portfolio.grantee,
        'originated_by': request.user,
    }
    send_notification('portfolio_request_accepted',
        context=PortfolioNotificationSerializer().to_representation(context))
