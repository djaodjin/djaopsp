# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from deployutils.apps.django import mixins as deployutils_mixins
from django.conf import settings
from django.db.models import Q
from pages.models import PageElement, build_content_tree, flatten_content_tree
from pages.helpers import ContentCut
from survey.mixins import SampleMixin
from survey.models import Campaign, Sample
from survey.utils import get_account_model, get_question_model

from .utils import get_account_model


class VisibilityMixin(deployutils_mixins.AccessiblesMixin):

    @property
    def visibility(self):
        if not hasattr(self, '_visibility'):
            if self.manages(settings.APP_NAME):
                self._visibility = None
            else:
                self._visibility = set(['public']) | self.accessible_plans
        return self._visibility

    @property
    def owners(self):
        if not hasattr(self, '_owners'):
            if self.manages(settings.APP_NAME):
                self._owners = None
            else:
                self._owners = self.accessible_profiles
        return self._owners


class AccountMixin(deployutils_mixins.AccountMixin):

    account_queryset = get_account_model().objects.all()
    account_lookup_field = 'slug'
    account_url_kwarg = 'profile'

    @property
    def campaign_candidates(self):
        """
        Returns a list of campaigns that can an account
        can answer against.
        """
        if not hasattr(self, '_campaign_candidates'):
            filtered_in = None
            for visible in (set(['public']) | self.accessible_plans):
                visibility_q = Q(extra__contains=visible)
                if filtered_in:
                    filtered_in |= visibility_q
                else:
                    filtered_in = visibility_q
                if self.accessible_profiles:
                    accounts_q = Q(account__slug__in=self.accessible_profiles)
                    if filtered_in:
                        filtered_in |= accounts_q
                    else:
                        filtered_in = accounts_q
            self._campaign_candidates = (Campaign.objects.filter(filtered_in)
                if filtered_in else Campaign.objects.all())
        return self._campaign_candidates


class ReportMixin(AccountMixin, SampleMixin):
    """
    Loads assessment and improvement for a profile
    """
    @property
    def segments_candidates(self):
        """
        Returns a list of top-level segments that can an account
        can answer against.
        """
        if not hasattr(self, '_segments_candidates'):
            self._segments_candidates = []
            for segment in get_segments_available(
                    self.sample.campaign, visibility=self.visibility,
                    owners=self.accessible_profiles):
                print("XXX segment=%s" % str(segment))
                searchable = segment.get('extra', {}).get('searchable', False)
                pagebreak = segment.get('extra', {}).get('pagebreak', False)
                if pagebreak and not searchable:
                    continue
                self._segments_candidates += [segment]
        return self._segments_candidates

    def get_context_data(self, **kwargs):
        context = super(ReportMixin, self).get_context_data(**kwargs)
        context.update({'sample': self.sample})
        return context



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
