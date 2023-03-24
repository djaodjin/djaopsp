# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
import json

from deployutils.apps.django import mixins as deployutils_mixins
from deployutils.helpers import update_context_urls
from django.conf import settings
from django.db.models import Q, F
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from pages.mixins import TrailMixin
from pages.models import PageElement
from survey.settings import URL_PATH_SEP, DB_PATH_SEP
from survey.mixins import CampaignMixin as CampaignMixinBase, SampleMixin
from survey.models import Answer, Campaign, Sample
from survey.utils import get_question_model

from .compat import reverse
from .utils import (get_account_model, get_segments_available,
    get_segments_candidates)


class VisibilityMixin(deployutils_mixins.AccessiblesMixin):

    @property
    def manages_broker(self):
        if True:
            # XXX Temporary override while `site.slug` is being introduced.
            return self.accessible_profiles & settings.UNLOCK_BROKERS
        broker = self.request.session.get('site', {}).get('slug')
        return broker and broker in self.accessible_profiles

    @property
    def visibility(self):
        if not hasattr(self, '_visibility'):
            if self.manages_broker:
                self._visibility = None
            else:
                self._visibility = set(['public']) | self.accessible_plans
        return self._visibility

    @property
    def owners(self):
        if not hasattr(self, '_owners'):
            if self.manages_broker:
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
            #pylint:disable=superfluous-parens
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
            campaign = self.kwargs.get('campaign')
            if campaign:
                self._campaign_candidates = self._campaign_candidates.filter(
                    slug=campaign)
            else:
                # We don't have a campaign slug, so let's restrict further
                # to campaigns that are searchable.
                self._campaign_candidates = self._campaign_candidates.filter(
                    extra__contains='searchable')

        return self._campaign_candidates


class CampaignMixin(CampaignMixinBase):

    @property
    def segments_available(self):
        if not hasattr(self, '_segments_available'):
            candidates = get_segments_candidates(self.campaign)
            if self.db_path and self.db_path != DB_PATH_SEP:
                self._segments_available = []
                for seg in candidates:
                    path = seg.get('path')
                    if path and path.startswith(self.db_path):
                        self._segments_available += [seg]
            else:
                self._segments_available = candidates
        return self._segments_available

    @property
    def sections_available(self):
        """
        Returns a subset of questions in a segment an account
        can answer against.
        """
        if not hasattr(self, '_sections_available'):
            self._sections_available = self.segments_available
        return self._sections_available


class ReportMixin(VisibilityMixin, AccountMixin, SampleMixin, TrailMixin):
    """
    Loads assessment and improvement for a profile
    """
    @property
    def db_path(self):
        # We use the tree of `pages.PageElement` to infer the missing elements
        # from the db_path used to retrieve `survey.Question`.
        return self.full_path

    @property
    def improvement_sample(self):
        """
        Matching improvement sample for the assessment.
        """
        if not hasattr(self, '_improvement_sample'):
            self._improvement_sample = None
            assessment_sample = self.sample
            account = assessment_sample.account
            campaign = assessment_sample.campaign
            sample_kwarg = self.kwargs.get('sample', None)
            if sample_kwarg:
                try:
                    queryset = Sample.objects.filter(
                        Q(account=account) |
                        (Q(account__portfolios__grantee=self.account) &
                         Q(account__portfolios__ends_at__gte=F('created_at'))),
                        slug=sample_kwarg,
                        extra__contains='is_planned').select_related(
                            'campaign', 'account')
                    self._improvement_sample = queryset.distinct().get()
                except Sample.DoesNotExist:
                    # The sample slug might be matching an improvement sample.
                    next_assessment = Sample.objects.filter(
                        campaign=campaign,
                        account=account,
                        created_at__gt=assessment_sample.created_at,
                        is_frozen=assessment_sample.is_frozen).exclude(
                        extra__contains='is_planned').order_by(
                        'created_at').first()
                    # first improvement sample after assessment but no later
                    # than next assessment.
                    kwargs = {}
                    if next_assessment:
                        kwargs = {
                            'created_at__lt': next_assessment.created_at
                        }
                    self._improvement_sample = Sample.objects.filter(
                        campaign=campaign,
                        account=account,
                        extra__contains='is_planned',
                        is_frozen=assessment_sample.is_frozen,
                        created_at__gte=assessment_sample.created_at,
                        **kwargs).order_by('created_at').first()
            if not self._improvement_sample and not assessment_sample.is_frozen:
                #pylint:disable=unused-variable
                self._improvement_sample, unused_created = \
                    Sample.objects.get_or_create(
                        account=account, campaign=campaign, is_frozen=False,
                        extra='is_planned')
        return self._improvement_sample

    @property
    def segments_available(self):
        if not hasattr(self, '_segments_available'):
            self._segments_available = get_segments_available(self.sample)
        return self._segments_available

    @property
    def sections_available(self):
        """
        Returns a subset of questions in a segment an account
        can answer against.
        """
        if not hasattr(self, '_sections_available'):
            self._sections_available = self.segments_available
        return self._sections_available

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
            extra = seg.get('extra')
            if not extra:
                extra = {}
            searchable = (not searchable_only or extra.get('searchable', False))
            pagebreak = extra.get('pagebreak', False)
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
        if len(self.segments_available) == 1:
            path_parts = self.path.lstrip(URL_PATH_SEP).split(URL_PATH_SEP)
            seg_parts = self.segments_available[0].get('path').lstrip(
                DB_PATH_SEP).split(DB_PATH_SEP)
            visible_parts = []
            for seg_part in seg_parts:
                if seg_part in path_parts:
                    visible_parts += [seg_part]
            path = URL_PATH_SEP.join(visible_parts)
        else:
            path = self.path.lstrip(URL_PATH_SEP)
        # These URLs can't be accessed by profiles the sample was shared
        # with. They must use ``sample.account``.
        if path:
            assess_url = reverse('assess_practices',
                args=(self.sample.account, self.sample, path))
            improve_url = reverse('improve_practices',
                args=(self.sample.account, self.sample, path))
        else:
            assess_url = reverse('assess_redirect',
                args=(self.sample.account, self.sample,))
            improve_url = reverse('improve_redirect',
                args=(self.sample.account, self.sample,))
        update_context_urls(context, {
            'assess': assess_url,
            'improve': improve_url,
            'complete': reverse('scorecard',
                args=(self.sample.account, self.sample,)),
            'share': reverse('share', args=(self.sample.account, self.sample,)),
        })
        return context


class SectionReportMixin(ReportMixin):
    # We want `campaign` from ReportMixin and `segments_available`
    # from `CampaignContentMixin` so it is safer to redefine them here.
    @property
    def campaign(self):
        if not hasattr(self, '_campaign'):
            self._campaign = self.sample.campaign
        return self._campaign

    @property
    def segments_available(self):
        """
        When a {path} is specified, it will returns the segment identified
        by that {path} regardless of the number of answers already present
        for it. When no {path} is specified, it is empty of the root of the
        content tree, the segments which have at least one answer are returned.
        """
        #pylint:disable=too-many-nested-blocks
        if not hasattr(self, '_segments_available'):
            # We get all segments that have at least one answer, regardless
            # of their visibility or ownership status.
            if self.db_path and self.db_path != DB_PATH_SEP:
                candidates = self.get_segments_candidates()
                self._segments_available = []
                for seg in candidates:
                    path = seg.get('path')
                    is_pagebreak = seg.get('extra', {}).get('pagebreak')
                    if (path and is_pagebreak and
                        self.db_path.startswith(path)):
                        self._segments_available += [seg]
            else:
                self._segments_available = get_segments_available(self.sample)
        return self._segments_available


    @property
    def sections_available(self):
        #pylint:disable=too-many-nested-blocks
        if not hasattr(self, '_sections_available'):
            # We get all segments that have at least one answer, regardless
            # of their visibility or ownership status.
            self._sections_available = self.segments_available
            if self.db_path and self.db_path != DB_PATH_SEP:
                candidates = self._sections_available
                self._sections_available = []
                for seg in candidates:
                    path = seg.get('path')
                    if path and path.startswith(self.db_path):
                        self._sections_available += [seg]
                if not self._sections_available:
                    # Either the segment does not have an answer yet,
                    # or we are dealing with a section of a segment
                    # displayed on its own page.
                    visibility = [] # XXX We do not use `self.visibility`
                                    #     because "sustainability" is not
                                    #     currently set as "public". (v1 to v2)
                    owners = self.owners
                    slug = self.db_path.split(DB_PATH_SEP)[-1]
                    try:
                        queryset = PageElement.objects.filter(slug=slug)
                        element = queryset.get()
                        if not (owners and element.account in owners):
                            filtered_in = None
                            if visibility:
                                for visible in visibility:
                                    visibility_q = Q(extra__contains=visible)
                                    if filtered_in:
                                        filtered_in |= visibility_q
                                    else:
                                        filtered_in = visibility_q
                            if filtered_in:
                                queryset = queryset.filter(filtered_in)
                            element = queryset.get()
                    except PageElement.DoesNotExist:
                        raise Http404(_("Cannot find page '%(slug)s' "\
                            "with visibility %(visibility)s and "\
                            "ownership %(owners)s") % {
                            'slug': slug,
                            'visibility': visibility,
                            'owners': owners
                        })
                    try:
                        element.extra = json.loads(element.extra)
                    except (TypeError, ValueError):
                        pass
                    self._sections_available = [{
                        'indent': 0,
                        'path': self.db_path,
                        'slug': element.slug,
                        'title': element.title,
                        'extra': element.extra,
                    }]
        return self._sections_available

    @property
    def nb_answers(self):
        if not hasattr(self, '_nb_answers'):
            self._nb_answers = 0
            for seg in self.segments_available:
                path = seg.get('path')
                if not path:
                    continue
                queryset = Answer.objects.filter(
                    Q(unit_id=F('question__default_unit_id')) |
        Q(unit_id=F('question__default_unit__source_equivalences__target_id')),
                    sample=self.sample,
                    question__path__startswith=path)
                self._nb_answers += queryset.count()
        return self._nb_answers

    @property
    def nb_questions(self):
        if not hasattr(self, '_nb_questions'):
            self._nb_questions = 0
            if self.sample.is_frozen:
                for seg in self.segments_available:
                    path = seg.get('path')
                    if not path:
                        continue
                    queryset = get_question_model().objects.filter(
                        path__startswith=path,
                        answer__sample=self.sample
                    ).distinct()
                    self._nb_questions += queryset.count()
            else:
                for seg in self.segments_available:
                    path = seg.get('path')
                    if not path:
                        continue
                    queryset = get_question_model().objects.filter(
                        path__startswith=path,
                        enumeratedquestions__campaign=self.sample.campaign
                    ).distinct()
                    self._nb_questions += queryset.count()
        return self._nb_questions

    @property
    def nb_required_answers(self):
        if not hasattr(self, '_nb_required_answers'):
            self._nb_required_answers = 0
            if not self.sample.is_frozen:
                # completed assessments cannot use `EnumeratedQuestions`.
                for seg in self.segments_available:
                    path = seg.get('path')
                    if not path:
                        continue
                    queryset = Answer.objects.filter(
                    Q(unit_id=F('question__default_unit_id')) |
        Q(unit_id=F('question__default_unit__source_equivalences__target_id')),
                    sample=self.sample,
                    question__enumeratedquestions__required=True,
                    question__path__startswith=path,
        question__enumeratedquestions__campaign=self.sample.campaign)
                    self._nb_required_answers += queryset.count()
        return self._nb_required_answers

    @property
    def nb_required_questions(self):
        if not hasattr(self, '_nb_required_questions'):
            self._nb_required_questions = 0
            if not self.sample.is_frozen:
                # completed assessments cannot use `EnumeratedQuestions`.
                for seg in self.segments_available:
                    path = seg.get('path')
                    if not path:
                        continue
                    queryset = get_question_model().objects.filter(
                        path__startswith=path,
                        enumeratedquestions__campaign=self.sample.campaign,
                        enumeratedquestions__required=True
                    ).distinct()
                    self._nb_required_questions += queryset.count()
        return self._nb_required_questions
