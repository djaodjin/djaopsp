# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from deployutils.apps.django import mixins as deployutils_mixins
from deployutils.helpers import update_context_urls
from django.conf import settings
from django.db.models import Q
from survey.mixins import SampleMixin
from survey.models import Campaign
from survey.utils import get_account_model

from .compat import reverse
from .utils import (get_account_model, get_segments_available,
    get_segments_candidates)


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


class ReportMixin(VisibilityMixin, AccountMixin, SampleMixin):
    """
    Loads assessment and improvement for a profile
    """
    @property
    def segments_available(self):
        if not hasattr(self, '_segments_available'):
            candidates = get_segments_available(
                self.sample, segments_candidates=self.segments_candidates)
            if self.db_path and self.db_path != self.DB_PATH_SEP:
                self._segments_available = []
                for seg in candidates:
                    path = seg.get('path')
                    if path and path.startswith(self.db_path):
                        self._segments_available += [seg]
            else:
                self._segments_available = candidates
        return self._segments_available

    @property
    def segments_candidates(self):
        """
        Returns a list of top-level segments that can an account
        can answer against.
        """
        if not hasattr(self, '_segments_candidates'):
            self._segments_candidates = self.get_segments_candidates(
                searchable_only=True)
        return self._segments_candidates

    def get_segments_candidates(self, searchable_only=False):
        results = []
        for seg in get_segments_candidates(self.sample.campaign,
                visibility=self.visibility, owners=self.owners):
            searchable = (not searchable_only or
                seg.get('extra', {}).get('searchable', False))
            pagebreak = seg.get('extra', {}).get('pagebreak', False)
            if pagebreak and not searchable:
                continue
            results += [seg]
        return results

    def get_context_data(self, **kwargs):
        context = super(ReportMixin, self).get_context_data(**kwargs)
        context.update({
            'sample': self.sample,
            'segments_available': self.segments_available,
        })
        path = self.path.lstrip(self.URL_PATH_SEP)
        if path:
            assess_url = reverse('assess_practices',
                args=(self.account, self.sample, path))
        else:
            assess_url = reverse('scorecard',
                args=(self.account, self.sample,))
        update_context_urls(context, {
            'assess': assess_url,
            'complete': reverse('scorecard',
                args=(self.account, self.sample,)),
            'share': reverse('share', args=(self.account, self.sample,)),
        })
        return context
