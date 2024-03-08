# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.
import json

from dateutil.relativedelta import relativedelta
from deployutils.apps.django import mixins as deployutils_mixins
from deployutils.helpers import update_context_urls
from django.conf import settings
from django.db import transaction
from django.db.models import Q, F
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from pages.mixins import (TrailMixin,
    SequenceProgressMixin as SequenceProgressMixinBase)
from pages.models import PageElement
from survey.helpers import get_extra
from survey.mixins import (CampaignMixin as CampaignMixinBase,
    DateRangeContextMixin, SampleMixin)
from survey.models import Answer, Campaign, Sample
from survey.queries import datetime_or_now
from survey.settings import URL_PATH_SEP, DB_PATH_SEP
from survey.utils import get_question_model

from .compat import reverse
from .models import VerifiedSample, SurveyEvent
from .utils import (get_account_model, get_requested_accounts,
    get_segments_available, get_segments_candidates)


class VisibilityMixin(deployutils_mixins.AccessiblesMixin):

    @property
    def verifier_accounts(self):
        """
        Returns accounts for which the `request.user` is listed as a verifier.
        """
        if not hasattr(self, '_verifier_accounts'):
            unlocked_brokers = settings.UNLOCK_BROKERS
            broker = self.request.session.get('site', {}).get('slug')
            if broker:
                unlocked_brokers |= set([broker])
            accessibles = set([])
            self._verifier_accounts = set([])
            for org in self.get_accessible_profiles(
                    self.request, roles=['manager', settings.AUDITOR_ROLE]):
                org_slug = org['slug']
                if org_slug in unlocked_brokers:
                    accessibles |= set([org_slug])
                for subscription in org.get('subscriptions', []):
                    plan_key =  subscription.get('plan')
                    if plan_key and plan_key == 'verification-partners':
                        accessibles |= set([org_slug])
            if accessibles:
                self._verifier_accounts = list(
                    get_account_model().objects.filter(slug__in=accessibles))
        return self._verifier_accounts

    @property
    def is_auditor(self):
        return bool(self.verifier_accounts)

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
        Returns a list of campaigns that can an account can answer against.

        Implementation note: The queiry filter is using the profiles/roles
        passed through the HTTP `request`. As a result, the candidates are
        consistant when there is a direct relationship between the {account}
        specified in the URL and the authenticated user.
        Results are inconsistent for broker profile managers accessing other
        accounts.
        """
        if not hasattr(self, '_campaign_candidates'):
            filtered_in = None
            #pylint:disable=superfluous-parens
            for visible in (set(['public']) | set([plan['slug']
                    for plan in self.get_accessible_plans(
                            self.request, profile=self.kwargs.get(
                            self.account_url_kwarg))])):
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


class ReportMixin(VisibilityMixin, SampleMixin, AccountMixin, TrailMixin):
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
    def verification(self):
        if not hasattr(self, '_verification'):
            self._verification = VerifiedSample.objects.filter(
                Q(sample=self.sample) | Q(verifier_notes=self.sample)).first()
        return self._verification

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


    @property
    def verification_available(self):
        """
        Returns `True` if the response was verified and is available
        to the account making the request to see the response.
        """
        if not hasattr(self, '_verification_available'):
            self._verification_available = (
                self.account in self.verifier_accounts)
            if not self._verification_available:
                queryset = Sample.objects.filter(
                    notes__sample=self.sample,
                    notes__sample__account__portfolios__grantee=self.account,
                    notes__verified_status__gte=\
                    VerifiedSample.STATUS_REVIEW_COMPLETED)
                self._verification_available = queryset.exists()
        return self._verification_available


    def get_or_create_verification(self):
        """
        Creates a `VerifiedSample` for a verifier to store verification notes
        """
        if not self.verification:
            verifier_account = None
            if self.verifier_accounts:
                # If we don't have a verifier account, we do not create
                # any verifier notes otherwise it could lead to serious
                # data issues in the future.
                verifier_account = self.verifier_accounts[0]
                assessment_sample = self.sample
                with transaction.atomic():
                    try:
                        campaign_verified = Campaign.objects.get(
                            slug='%s-verified' % str(assessment_sample.campaign))
                        verifier_notes = Sample.objects.create(
                            account=verifier_account,
                            campaign=campaign_verified)
                        self._verification = VerifiedSample.objects.create(
                            sample=assessment_sample,
                            verifier_notes=verifier_notes)
                    except Campaign.DoesNotExist:
                        self._verification = None
        return self.verification


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
        #pylint:disable=too-many-locals
        context = super(ReportMixin, self).get_context_data(**kwargs)
        context.update({
            'sample': self.sample,
            'segments_available': self.segments_available,
            'segments_candidates': self.segments_candidates,
        })
        segments_available_set = {
            seg['slug'] for seg in self.segments_available}
        segments_candidates_set = {
            seg['slug'] for seg in self.segments_candidates}
        segments_improve_set = segments_candidates_set & segments_available_set

        path = self.path.lstrip(URL_PATH_SEP)

        # These URLs can't be accessed by profiles the sample was shared
        # with. They must use ``sample.account``.
        assess_url = None
        improve_url = None
        # Allows grantee to access assess and improve pages (read-only).
        account = self.account
        assess_url = reverse('assess_redirect',
            args=(account, self.sample,))
        improve_url = reverse('improve_redirect',
            args=(account, self.sample,))
        if path:
            # A convoluted way to get back to the industry segment `path`
            # prefix...
            seg_path = ""
            try:
                parts = iter(path.split(URL_PATH_SEP))
                elems = iter(self.get_full_element_path(path))
                elem = next(elems)
                part = next(parts)
                sep = ""
                while part and elem:
                    pagebreak = get_extra(elem, 'pagebreak', False)
                    if elem.slug == part:
                        seg_path += sep + part
                        sep = URL_PATH_SEP
                        part = next(parts)
                    elem = next(elems)
                    if pagebreak:
                        path = seg_path
                        break
            except StopIteration:
                pass
            # ... so the progresbar links are always at the industry segment
            # level.
            assess_url = reverse('assess_practices',
                args=(account, self.sample, path))
            if segments_improve_set:
                improve_url = reverse('improve_practices',
                    args=(account, self.sample, path))
        if assess_url:
            update_context_urls(context, {'assess': assess_url})
        if improve_url:
            update_context_urls(context, {'improve': improve_url})
        update_context_urls(context, {
            'complete': reverse('scorecard',
                args=(account, self.sample,)),
        })
        if self.account == self.sample.account:
            update_context_urls(context, {'share': reverse('share',
                args=(self.sample.account, self.sample,))})

        if self.is_auditor:
            verified_sample = self.get_or_create_verification()
            if verified_sample:
                if verified_sample.verified_by:
                    context.update({'verified_by': verified_sample.verified_by})
                if verified_sample.verifier_notes:
                    update_context_urls(context, {
                        'api_verification_sample': reverse('survey_api_sample',
                            args=(verified_sample.verifier_notes.account,
                            verified_sample.verifier_notes)),
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


class AccountsAggregatedQuerysetMixin(DateRangeContextMixin, AccountMixin):
    """
    A set of accounts used to select requested responses
    """
    default_unit = 'profiles'
    valid_units = ('percentage',)

    @property
    def unit(self):
        if not hasattr(self, '_unit'):
            self._unit = self.default_unit
            param_unit = self.get_query_param('unit')
            if param_unit is not None and param_unit in self.valid_units:
                self._unit = param_unit
        return self._unit

    @property
    def is_percentage(self):
        return self.unit == 'percentage'

    @property
    def accounts_ends_at(self):
        """
        End of the period when requested accounts were suppossed to respond
        """
        if not hasattr(self, '_accounts_ends_at'):
            _accounts_ends_at = get_extra(self.account, 'ends_at', None)
            at_time = datetime_or_now()
            if _accounts_ends_at:
                _accounts_ends_at = datetime_or_now(_accounts_ends_at)
                if _accounts_ends_at > at_time:
                    at_time = _accounts_ends_at
            param_ends_at = self.get_query_param('accounts_ends_at',
                self.get_query_param('ends_at'))
            if param_ends_at is not None:
                # When there are no specified `ends_at` in the query
                # string, we will be defaulting to the value stored
                # in `account.extra` or `now` whichever is grater.
                at_time = param_ends_at.strip('"')
            self._accounts_ends_at = datetime_or_now(at_time)
        return self._accounts_ends_at

    @property
    def accounts_start_at(self):
        """
        Start of the period when requested accounts were invited
        """
        if not hasattr(self, '_accounts_start_at'):
            self._accounts_start_at = get_extra(self.account, 'start_at', None)
            if self._accounts_start_at:
                self._accounts_start_at = datetime_or_now(
                    self._accounts_start_at)
            param_start_at = self.get_query_param('accounts_start_at',
                self.get_query_param('start_at'))
            if param_start_at is not None:
                param_start_at = param_start_at.strip('"')
                self._accounts_start_at = datetime_or_now(param_start_at)
            # In general `ends_at` could be `None`,
            # which would be a problem here.
            accounts_ends_at = datetime_or_now(self.accounts_ends_at)
            if (self._accounts_start_at and
                self._accounts_start_at >= accounts_ends_at):
                try:
                    # fixing period to 12 months if for any reason the start
                    # date is after the ends date.
                    self._accounts_start_at = (
                        accounts_ends_at - relativedelta(months=12))
                except ValueError:
                    # deal with a bogus ends_at date
                    self._accounts_start_at = accounts_ends_at
        return self._accounts_start_at

    @property
    def search_terms(self):
        if not hasattr(self, '_search_terms'):
            self._search_terms = self.get_query_param('q', None)
        return self._search_terms

    def get_requested_accounts(self, grantee, aggregate_set=False):
        """
        All accounts which ``grantee`` has requested a scorecard from.
        """
        if not grantee:
            grantee = self.account
        return get_requested_accounts(grantee,
            campaign=self.campaign, aggregate_set=aggregate_set,
            start_at=self.accounts_start_at, ends_at=self.accounts_ends_at,
            search_terms=self.search_terms)


class AccountsNominativeQuerysetMixin(AccountsAggregatedQuerysetMixin):
    """
    A set of accounts used to select requested responses the organization
    has direct access to
    """

    @property
    def requested_accounts(self):
        if not hasattr(self, '_requested_accounts'):
            self._requested_accounts = self.get_requested_accounts(self.account)
        return self._requested_accounts

class SequenceProgressMixin(SequenceProgressMixinBase):

    def update_element(self, obj):
        super(SequenceProgressMixin, self).update_element(obj)
        obj.is_survey_event = SurveyEvent.objects.filter(element=obj.page_element).exists()
