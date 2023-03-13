# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
"""
This file contains helper functions that are used accross the project
but do not fit nicely into the API/Views class hierarchy.
Furthermore this functions rely on the models to be loaded. For pure
helper functions that do not rely on the order Django loads the modules,
see the file helpers.py in the same directory.
"""
import json, logging, smtplib
from collections import OrderedDict
from importlib import import_module

from deployutils.crypt import JSONEncoder
from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import F
from django.utils import translation
from extended_templates.backends import get_email_backend
from pages.helpers import ContentCut
from pages.models import PageElement, build_content_tree, flatten_content_tree
from survey.models import (Answer, Campaign, Choice, PortfolioDoubleOptIn,
    Sample, Unit)
from survey.helpers import get_extra
from survey.utils import get_question_model, is_sqlite3

from .compat import import_string, six, gettext_lazy as _

DB_PATH_SEP = '/'
LOGGER = logging.getLogger(__name__)
SEND_EMAIL = True


class TransparentCut(object):

    TAG_SCORECARD = 'scorecard'

    def __init__(self, depth=1):
        self.depth = depth

    def enter(self, tag):
        #pylint:disable=unused-argument
        self.depth = self.depth + 1
        return True

    def leave(self, attrs, subtrees):
        self.depth = self.depth - 1
        # `transparent_to_rollover` is meant to speed up computations
        # when the resulting calculations won't matter to the display.
        # We used to compute decide `transparent_to_rollover` before
        # the recursive call (see commit c421ca5) but it would not
        # catch the elements tagged deep in the tree with no chained
        # presentation.
        try:
            tags = attrs.get('extra', {}).get('tags', [])
        except AttributeError:
            tags = []
        attrs['transparent_to_rollover'] = not (
            tags and self.TAG_SCORECARD in tags)
        for subtree in six.itervalues(subtrees):
            try:
                tags = attrs.get('extra', {}).get('tags', [])
            except AttributeError:
                tags = []
            if tags and self.TAG_SCORECARD in tags:
                attrs['transparent_to_rollover'] = False
                break
            if not subtree[0].get('transparent_to_rollover', True):
                attrs['transparent_to_rollover'] = False
                break
        return not attrs['transparent_to_rollover']


def get_account_model():
    """
    Returns the ``Account`` model that is active in this project.
    """
    try:
        return django_apps.get_model(settings.ACCOUNT_MODEL)
    except ValueError:
        raise ImproperlyConfigured(
            "ACCOUNT_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured("ACCOUNT_MODEL refers to model '%s'"\
" that has not been installed" % settings.ACCOUNT_MODEL)


def _notified_recipients(notification_slug, context):
    """
    Returns the organization email or the managers email if the organization
    does not have an e-mail set.
    """
    recipients = []
    bcc = []
    reply_to = None
    originated_by = context.get('originated_by')
    if not originated_by:
        originated_by = {}

    if notification_slug in (
            'portfolios_request_initiated',):
        user_email = context.get('account', {}).get('email', "")
        if user_email:
            recipients = [user_email]
    elif notification_slug in (
            'portfolios_grant_initiated',
            'portfolio_request_accepted',):
        user_email = context.get('grantee', {}).get('email', "")
        if user_email:
            recipients = [user_email]

    return recipients, bcc, reply_to


def send_notification(event_name, context=None):
    """
    Sends a notification e-mail using the current site connection,
    defaulting to sending an e-mail to broker profile managers
    if there is any problem with the connection settings.
    """
    if context is None:
        context = {}
    if settings.SEND_NOTIFICATION_CALLABLE:
        try:
            import_string(settings.SEND_NOTIFICATION_CALLABLE)(
                event_name, context=context)
            return
        except ImportError:
            pass

    # Default behavior: send an e-mail.
    #pylint:disable=too-many-arguments
    context.update({"event": event_name})
    template = 'notification/%s.eml' % event_name

    recipients, bcc, reply_to = _notified_recipients(
        event_name, context)
    LOGGER.debug("send_notification("\
        "recipients=%s, reply_to=%s, bcc=%s, event=%s)",
        recipients, reply_to, bcc,
        json.dumps(context, indent=2, cls=JSONEncoder))
    lang_code = settings.LANGUAGE_CODE
    if SEND_EMAIL:
        try:
            with translation.override(lang_code):
                get_email_backend().send(
                    recipients=recipients,
                    reply_to=reply_to,
                    bcc=bcc,
                    template=template,
                    context=context)
        except smtplib.SMTPException as err:
            LOGGER.warning("[signal] problem sending email: %s", err)
            context.update({'errors': [_("There was an error sending"\
    " the following email to %(recipients)s. This is most likely due to"\
    " a misconfiguration of the e-mail notifications whitelabel settings"\
    " for your site.") % {'recipients': recipients}]})
            #pylint:disable=unused-variable
            notified_on_errors = [adm[1] for adm in settings.ADMINS]
            if notified_on_errors:
                get_email_backend().send(
                    recipients=notified_on_errors,
                    template=template,
                    context=context)
        except Exception as err:
            # Something went horribly wrong, like the email password was not
            # decrypted correctly. We want to notifiy the operations team
            # but the end user shouldn't see a 500 error as a result
            # of notifications sent in the HTTP request pipeline.
            LOGGER.exception(err)


def get_practice_serializer():
    """
    Returns the ``PracticeSerializer`` model that is active
    in this project.
    """
    path = settings.PRACTICE_SERIALIZER
    dot_pos = path.rfind('.')
    module, attr = path[:dot_pos], path[dot_pos + 1:]
    try:
        mod = import_module(module)
    except (ImportError, ValueError) as err:
        raise ImproperlyConfigured(
         "Error importing class '%s' defined by PRACTICE_SERIALIZER (%s)"
            % (path, err))
    try:
        cls = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s"'\
' check the value of PRACTICE_SERIALIZER' % (module, attr))
    return cls


def get_alliances(account):
    """
    Returns alliances the account queryset are part of.
    """
    if (hasattr(settings, 'ALLIANCES_CALLABLE') and
        settings.ALLIANCES_CALLABLE):
        return import_string(settings.ALLIANCES_CALLABLE)(account)
    return []


def get_reporting_accounts(account, campaign=None, start_at=None, ends_at=None):
    """
    All accounts which have elected to share their scorecard
    with ``account``.
    """
    queryset = None
    if (hasattr(settings, 'REPORTING_ACCOUNTS_CALLABLE') and
        settings.REPORTING_ACCOUNTS_CALLABLE):
        queryset = import_string(settings.REPORTING_ACCOUNTS_CALLABLE)(
            account, campaign=campaign, start_at=start_at, ends_at=ends_at)

    if queryset is None:
        filter_params = {}
        if start_at:
            filter_params.update({
                'portfolio_double_optin_accounts__created_at__gte': start_at})
        if campaign:
            filter_params.update({'portfolios__campaign': campaign})
        queryset = get_account_model().objects.filter(
            portfolios__grantee=account,
            **filter_params).distinct()

    return queryset


def get_requested_accounts(account, campaign=None, start_at=None, ends_at=None):
    """
    All accounts which ``account`` has requested a scorecard from.
    """
    queryset = None
    if (hasattr(settings, 'REQUESTED_ACCOUNTS_CALLABLE') and
        settings.REQUESTED_ACCOUNTS_CALLABLE):
            queryset = import_string(settings.REQUESTED_ACCOUNTS_CALLABLE)(
            account, campaign=campaign, start_at=start_at, ends_at=ends_at)

    if queryset is None:
        filter_params = {}
        if start_at:
            filter_params.update({
                'portfolio_double_optin_accounts__created_at__gte': start_at})
        if ends_at:
            filter_params.update({
                'portfolio_double_optin_accounts__created_at__lt': ends_at})
        if campaign:
            filter_params.update({
                'portfolio_double_optin_accounts__campaign': campaign})
        queryset = get_account_model().objects.filter(
            portfolio_double_optin_accounts__grantee=account,
            portfolio_double_optin_accounts__state__in=(
                PortfolioDoubleOptIn.OPTIN_REQUEST_INITIATED,
                PortfolioDoubleOptIn.OPTIN_REQUEST_ACCEPTED,
                PortfolioDoubleOptIn.OPTIN_REQUEST_DENIED,
                PortfolioDoubleOptIn.OPTIN_REQUEST_EXPIRED),
                **filter_params).annotate(
                requested_at=F('portfolio_double_optin_accounts__created_at'),
                grant_key=F('portfolio_double_optin_accounts__state')
        ).distinct()

    return queryset


def get_highlights(sample):
    highlights = get_extra(sample.campaign, 'highlights', [])
    for highlight in highlights:
        reporting = False
        filter_q = None
        for include in highlight.get('includes'):
            if filter_q:
                filter_q |= models.Q(
                    path__endswith=DB_PATH_SEP + include)
            else:
                filter_q = models.Q(
                    path__endswith=DB_PATH_SEP + include)
        includes = get_question_model().objects.filter(
            filter_q).select_related('default_unit')
        if includes:
            default_unit = includes[0].default_unit
            if default_unit.system == Unit.SYSTEM_ENUMERATED:
                positive = Choice.objects.filter(unit=default_unit).order_by(
                        'rank').first()
                reporting = Answer.objects.filter(
                    question__in=includes,
                    sample=sample, unit__system=Unit.SYSTEM_ENUMERATED,
                    measured=positive.pk).exists()
            elif default_unit.system == Unit.SYSTEM_DATETIME:
                reporting = Choice.objects.filter(pk__in=Answer.objects.filter(
                    question__in=includes, sample=sample,
                    unit=default_unit).values_list('measured',
                    flat=True)).exclude(text='no-target').exists()#XXX
            else:
                reporting = Answer.objects.filter(
                    question__in=includes, sample=sample).exists()
        highlight.update({'reporting': reporting})
    return highlights


def get_latest_active_assessments(account, campaign=None):
    kwargs = {}
    if campaign:
        if isinstance(account, Campaign):
            kwargs.update({'campaign': campaign})
        else:
            kwargs.update({'campaign__slug': campaign})
    if isinstance(account, get_account_model()):
        kwargs.update({'account': account})
    else:
        kwargs.update({'account__slug': str(account)})
    return Sample.objects.filter(
        is_frozen=False, extra__isnull=True,
        **kwargs).order_by('-created_at').select_related(
            'campaign', 'account')


def get_latest_completed_assessment(account, campaign=None):
    kwargs = {}
    if campaign:
        kwargs.update({'campaign': campaign})
    if isinstance(account, get_account_model()):
        kwargs.update({'account': account})
    else:
        kwargs.update({'account__slug': str(account)})
    return Sample.objects.filter(
        is_frozen=True, extra__isnull=True,
        **kwargs).order_by('-created_at').select_related(
            'campaign', 'account').first()


def get_score_weight(campaign, path, default_value=1.0):
    return get_extra(campaign, path, default_value)


def get_leafs(rollup_tree, campaign, path=None):
    """
    Returns all leafs from a rollup tree.

    The dictionnary indexed by paths is carefully constructed such
    that values are aliases into the rollup tree (not copies). It is
    thus possible to update leafs in the roll up tree by updating values
    in the dictionnary returned by this function.
    """
    if path is None:
        path = ''
    elif not path.startswith('/'):
        path = '/%s' % path

    if not rollup_tree[1].keys():
        return {path: rollup_tree}

    # Recursively go through the children of the current node
    leafs = OrderedDict({})
    for key, level_detail in six.iteritems(rollup_tree[1]):
        leafs.update(get_leafs(level_detail, campaign, path=key))

    # The node is traversed only once and we get a chance
    # to decorate it here with information that wasn't loaded
    # while building the tree.
    # We do this after all children have been traversed so we
    # get a chance to compute a total score_weight.
    if 'text' not in rollup_tree[0]:
        element = PageElement.objects.filter(
            slug=rollup_tree[0]['slug']).values('text').first()
        if element and element['text']:
            rollup_tree[0].update(element)

    score_weight = get_score_weight(campaign, path)
    rollup_tree[0].update({'score_weight': score_weight})
    total_score_weight = 0
    for key, level_detail in six.iteritems(rollup_tree[1]):
        total_score_weight += get_score_weight(campaign, key)
    normalize_children = (
        (1.0 - 0.01) < total_score_weight < (1.0 + 0.01))
    if normalize_children:
        for key, level_detail in six.iteritems(rollup_tree[1]):
            score_weight = level_detail[0].get('score_weight')
            if score_weight:
                # In edge cases where a single leaf is under a node.
                level_detail[0].update({
                    'score_percentage': int(score_weight * 100)})

    return leafs


def _cut_tree(roots, cut=None):
    """
    Cuts subtrees out of *roots* when they match the *cut* parameter.
    *roots* has a format compatible with the data structure returned
    by `build_content_tree`.

    code::
        {
          "/boxes-and-enclosures": [
            { ... data for node ... },
            {
              "boxes-and-enclosures/management": [
              { ... data for node ... },
              {}],
              "boxes-and-enclosures/design": [
              { ... data for node ... },
              {}],
            }]
        }
    """
    for node_path, node in list(six.iteritems(roots)):
        _cut_tree(node[1], cut=cut)
        if cut and not cut.leave(node[0], node[1]):
            del roots[node_path]
    return roots


def get_scores_tree(roots=None, prefix=""):
    """
    Returns a tree specialized to compute rollup scores.

    Typically `get_leafs` and a function to populate a leaf will be called
    before an rollup is done.
    """
    content_tree = build_content_tree(roots, prefix=prefix)
    scores_tree = _cut_tree(content_tree, cut=TransparentCut())

    # Moves up all industry segments which are under a category
    # (ex: /facilities/janitorial-services).
    # If we donot do that, then assessment score will be incomplete
    # in the dashboard, as the aggregator will wait for other sub-segments
    # in the top level category.
    removes = []
    ups = OrderedDict({})
    for root_path, root in six.iteritems(scores_tree):
        try:
            is_pagebreak = root[0].get('extra', {}).get(
                ContentCut.TAG_PAGEBREAK, False)
        except AttributeError:
            is_pagebreak = False
        if not is_pagebreak:
            removes += [root_path]
            ups.update(root[1])
    for root_path in removes:
        del scores_tree[root_path]
    scores_tree.update(ups)
    return scores_tree


def segments_as_sql(segments):
    """
    Returns an SQL query from a list of segments encoded as
    {'path': ..., 'title': ...}.
    """
    segments_query = None
    for segment in segments:
        if segments_query:
            segments_query = "%(segments_query)s UNION "\
                "SELECT '%(segment_path)s'%(convert_to_text)s AS path,"\
                " '%(segment_title)s'%(convert_to_text)s AS title" % {
                    'segments_query': segments_query,
                    'segment_path': segment['path'],
                    'segment_title': segment['title'],
                    'convert_to_text': ("" if is_sqlite3() else "::text")
                }
        else:
            segments_query = \
                "SELECT '%(segment_path)s'%(convert_to_text)s AS path,"\
                " '%(segment_title)s'%(convert_to_text)s AS title" % {
                    'segment_path': segment['path'],
                    'segment_title': segment['title'],
                    'convert_to_text': ("" if is_sqlite3() else "::text")
                }
    return segments_query


def get_segments_available(sample, visibility=None, owners=None,
                           segments_candidates=None):
    """
    All segments that have at least one answer
    """
    if not segments_candidates:
        segments_candidates = get_segments_candidates(
            sample.campaign, visibility=visibility, owners=owners)
    candidates = [seg for seg in segments_candidates
        if seg.get('extra', {}).get('pagebreak', False)]
    results = []
    for seg in candidates:
        prefix = seg['path']
        is_active = get_question_model().objects.filter(
            path__startswith=prefix, answer__sample=sample).exists()
        if is_active:
            results += [seg]
    return results


def get_segments_candidates(campaign, visibility=None, owners=None):
    """
    All segments that are candidates based on a campaign.
    """
    candidates = set([])
    for path in get_question_model().objects.filter(
        enumeratedquestions__campaign=campaign).values_list(
        'path', flat=True):
        candidates |= set([path.strip(DB_PATH_SEP).split(DB_PATH_SEP)[0]])
    if candidates:
        roots = PageElement.objects.get_roots(
            visibility=visibility, accounts=owners).filter(
            slug__in=candidates).order_by('title')
        content_tree = build_content_tree(roots=roots, prefix=DB_PATH_SEP,
            cut=ContentCut(), visibility=visibility, accounts=owners)
        return flatten_content_tree(content_tree)
    return []


def get_summary_performance(sample):
    if sample.campaign.slug == 'sustainability':
        return [11, 16, 7, 3]
    return []
