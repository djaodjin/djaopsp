# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.
"""
This file contains helper functions that are used accross the project
but do not fit nicely into the API/Views class hierarchy.
Furthermore this functions rely on the models to be loaded. For pure
helper functions that do not rely on the order Django loads the modules,
see the file helpers.py in the same directory.
"""

from pages.helpers import ContentCut
from pages.models import PageElement, build_content_tree, flatten_content_tree
from survey.models import Sample
from survey.utils import get_question_model

from .models import Account


def get_account_model():
    return Account


def get_latest_active_assessments(account, campaign=None):
    kwargs = {}
    if campaign:
        kwargs.update({'campaign': campaign})
    if isinstance(account, get_account_model()):
        kwargs.update({'account': account})
    else:
        kwargs.update({'account__slug': str(account)})
    return Sample.objects.filter(
        is_frozen=False, **kwargs).order_by('-created_at').select_related(
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


def get_segments_available(campaign, visibility=None, owners=None):
    """
    All segments that are candidates based on a campaign.
    """
    DB_PATH_SEP = '/'
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
