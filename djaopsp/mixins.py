# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from deployutils.apps.django import mixins as deployutils_mixins
from pages.models import PageElement, build_content_tree
from survey.mixins import SampleMixin
from survey.models import Campaign, Sample
from survey.utils import get_account_model, get_question_model

from .helpers import ContentCut, flatten
from .utils import get_account_model


class AccountMixin(deployutils_mixins.AccountMixin):

#    account_queryset = get_account_model().objects.all()
    account_lookup_field = 'slug'
    account_url_kwarg = 'profile'


class ReportMixin(AccountMixin, SampleMixin):
    """
    Loads assessment and improvement for a profile
    """


def get_latest_assessment_sample(account, campaign=None):
    kwargs = {}
    if campaign:
        kwargs.update({'campaign': campaign})
    if isinstance(account, get_account_model()):
        kwargs.update({'account': account})
    else:
        kwargs.update({'account__slug': str(account)})
    return Sample.objects.filter(
        is_frozen=False, extra__isnull=True,
        **kwargs).order_by('-created_at').select_related(
            'campaign', 'account').first()


def get_segments_available(campaign):
    """
    All segments that are candidates based on a campaign.
    """
    candidates = set([])
    for path in get_question_model().objects.filter(
        enumeratedquestions__campaign=campaign).values_list(
        'path', flat=True):
        candidates |= set([path.strip('/').split('/')[0]])
    if candidates:
        roots = PageElement.objects.get_roots().filter(
            slug__in=candidates).order_by('title')
        content_tree = build_content_tree(roots=roots, prefix='/',
            cut=ContentCut())
        return flatten(content_tree)
    return []


def get_segments_in_sample(sample):
    """
    All segments that havwe answers based on a sample's campaign.
    """
    candidates = get_segments_available(sample.campaign)
    return candidates


def get_campaigns_available(account):
    """
    All campaigns available to a profile.
    """
    return Campaign.objects.all()
