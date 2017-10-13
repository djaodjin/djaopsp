# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging, re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.utils import six
from rest_framework import generics
from rest_framework.response import Response
from survey.api.matrix import MatrixDetailAPIView
from survey.models import EditableFilter
from survey.utils import get_account_model

from .benchmark import BenchmarkMixin
from ..mixins import PermissionMixin
from ..serializers import AccountSerializer


LOGGER = logging.getLogger(__name__)


class DashboardMixin(BenchmarkMixin):

    account_model = get_account_model()

    def get_requested_accounts(self):

        return (self.get_accounts() | self.account_model.objects.accessible_by(
            self.request.user).filter(
                role__request_key__isnull=False)).distinct()

    def get_accounts(self):
        return self.account_model.objects.filter(
            subscriptions__organization=self.account).distinct()


class SupplierListAPIView(DashboardMixin, generics.ListAPIView):
    """
    List of suppliers accessible by the request user
    with normalized (total) score when the supplier completed
    a self-assessment.

    GET /api/:organization/suppliers

    Example Response:

        {
          "count":1,
          "next":null
          "previous":null,
          "results":[{
             "slug":"andy-shop",
             "printable_name":"Andy's Shop",
             "created_at": "2017-01-01",
             "normalized_score":94
          }]
        }
    """

    serializer_class = AccountSerializer

    def get_queryset(self):
        results = []
        rollup_tree = self.rollup_scores()
        account_scores = rollup_tree[0]['accounts']
        for account in self.get_requested_accounts():
            try:
                score = account_scores.get(account.pk, None)
                dct = {'slug': account.slug,
                    'printable_name': account.printable_name}
                if score is not None:
                    created_at = score.get('created_at', None)
                    if created_at:
                        dct.update({'last_activity_at': created_at})
                    nb_answers = score.get('nb_answers', 0)
                    nb_questions = score.get('nb_questions', 0)
                    dct.update({
                        'nb_answers': nb_answers, 'nb_questions': nb_questions})
                    if nb_answers == nb_questions:
                        normalized_score = score.get('normalized_score', None)
                    else:
                        normalized_score = None
                    if normalized_score is not None:
                        dct.update({'normalized_score': normalized_score})
                results += [dct]
            except self.account_model.DoesNotExist:
                pass
        return results


class TotalScoreBySubsectorAPIView(DashboardMixin, MatrixDetailAPIView):
    """
    A table of scores for cohorts aganist a metric.

    Uses the total score for each organization as recorded
    by the self-assessment surveys and present aggregates
    by industry sub-sectors (Boxes & enclosures, etc.)

    **Examples**:

    .. sourcecode:: http

        GET /api/matrix/totals

        Response:

        [{
           "slug": "totals",
           "title": "Total scores by supplier industry sub-sector"
           "scores":[{
               "portfolio-a": "0.1",
               "portfolio-b": "0.5",
           }
        }
        ...
        ]
    """
    @staticmethod
    def as_metric_candidate(cohort_slug):
        look = re.match(r"(\S+)(-\d+)$", cohort_slug)
        if look:
            return look.group(1)
        return cohort_slug

    def aggregate_scores(self, metric, cohorts, cut=None, accounts=None):
        #pylint:disable=unused-argument
        if accounts is None:
            accounts = get_account_model().objects.all()
        scores = {}
        rollup_tree = self.rollup_scores()
        rollup_scores = self.get_drilldown(rollup_tree, metric.slug)
        for cohort in cohorts:
            score = 0
            if isinstance(cohort, EditableFilter):
                if metric.slug == 'totals':
                    # Hard-coded: on the totals matrix we want to use
                    # a different metric for each cohort/column shown.
                    rollup_scores = self.get_drilldown(
                        rollup_tree, self.as_metric_candidate(cohort.slug))
                includes, excludes = cohort.as_kwargs()
                nb_accounts = 0
                for account in accounts.filter(**includes).exclude(**excludes):
                    account_score = rollup_scores.get(account.pk, None)
                    if account_score is not None:
                        score += account_score.get('normalized_score', 0)
                        nb_accounts += 1
                if nb_accounts > 0:
                    score = score / nb_accounts
            else:
                account = cohort
                account_score = rollup_scores.get(account.pk, None)
                if account_score is not None:
                    score = account_score.get('normalized_score', 0)
            scores.update({str(cohort): score})
        return scores

    def get_likely_metric(self, cohort_slug):
        likely_metric = None
        look = re.match(r"(\S+)(-\d+)$", cohort_slug)
        if look:
            try:
                likely_metric = reverse('matrix_chart', args=(self.account,
                    EditableFilter.objects.get(slug=look.group(1)).slug,))
            except EditableFilter.DoesNotExist:
                pass
        if likely_metric is None and self.matrix is not None:
            likely_metric = reverse('scorecard_organization',
                args=(cohort_slug, "/sustainability-%s" % self.matrix.slug))
        if likely_metric:
            likely_metric = self.request.build_absolute_uri(likely_metric)
        return likely_metric

    def decorate_with_scores(self, rollup_tree, accounts=None):
        if accounts is None:
            accounts = dict([(account.pk, account)
                for account in self.get_accounts()])
        score = {}
        cohorts = []
        for _, values in six.iteritems(rollup_tree[1]):
            self.decorate_with_scores(values, accounts=accounts)
            for account_id, account_score in six.iteritems(
                    values[0].get('accounts', {})):
                if account_id in accounts:
                    n_score = account_score.get('normalized_score', 0)
                    if n_score > 0:
                        account = accounts.get(account_id, None)
                        score[account.slug] = n_score
                        cohorts += [{
                            'slug': account.slug,
                            'title': account.full_name,
                            'likely_metric': self.get_likely_metric(
                                account.slug)}]
        rollup_tree[0]['values'] = score
        rollup_tree[0]['cohorts'] = cohorts

    def decorate_with_cohorts(self, rollup_tree, accounts=None):
        if accounts is None:
            accounts = dict([(account.pk, account)
                for account in self.get_accounts()])
        score = {}
        cohorts = []
        for path, values in six.iteritems(rollup_tree[1]):
            self.decorate_with_scores(values, accounts=accounts)
            nb_accounts = 0
            normalized_score = 0
            for account_id, account_score in six.iteritems(
                    values[0].get('accounts', {})):
                if account_id in accounts:
                    n_score = account_score.get('normalized_score', 0)
                    if n_score > 0:
                        nb_accounts += 1
                        normalized_score += n_score
            if normalized_score > 0 and nb_accounts > 0:
                score[path] = normalized_score / nb_accounts
                cohorts += [{
                    'slug': path,
                    'title': values[0]['title'],
                    'likely_metric': self.get_likely_metric(
                        values[0]['slug'] + '-1')}]
            values[0]['tag'] = [settings.TAG_SCORECARD]
        rollup_tree[0]['values'] = score
        rollup_tree[0]['cohorts'] = cohorts

    def get(self, request, *args, **kwargs):
        #pylint:disable=unused-argument
        try:
            from_root, trail = self.breadcrumbs
        except Http404:
            from_root = ''
            trail = []
        roots = [trail[-1][0]] if len(trail) > 0 else None
        rollup_tree = self.rollup_scores(roots, from_root)
        if roots:
            for node in six.itervalues(rollup_tree[1]):
                rollup_tree = node
                break
            self.decorate_with_scores(rollup_tree)
        else:
            self.decorate_with_cohorts(rollup_tree)
        charts = self.get_charts(rollup_tree)
        charts += [rollup_tree[0]]
        for chart in charts:
            if 'accounts' in chart:
                del chart['accounts']
        return Response(charts)
