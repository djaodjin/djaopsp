# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import re

from django.core.urlresolvers import reverse
from survey.api.matrix import MatrixDetailAPIView
from survey.models import EditableFilter
from survey.utils import get_account_model

from .benchmark import BenchmarkMixin


class TotalScoreBySubsectorAPIView(BenchmarkMixin, MatrixDetailAPIView):
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

    def aggregate_scores(self, metric, cohorts, cut=None):
        #pylint:disable=unused-argument
        scores = {}
        rollup_tree = self.rollup_scores()
        rollup_scores = self.get_drilldown(rollup_tree, metric.slug)
        for cohort in cohorts:
            score = 0
            if isinstance(cohort, EditableFilter):
                includes, excludes = cohort.as_kwargs()
                accounts = get_account_model().objects.filter(
                    **includes).exclude(**excludes)
                nb_accounts = 0
                for account in accounts:
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
        look = re.match(r"(\S+)(-\d+)", cohort_slug)
        if look:
            try:
                likely_metric = reverse('matrix_chart', args=(self.account,
                    EditableFilter.objects.get(slug=look.group(1)).slug,))
            except EditableFilter.DoesNotExist:
                pass
        if likely_metric is None and self.matrix is not None:
            likely_metric = reverse('scorecard_organization',
                args=(cohort_slug, "/%s" % self.matrix.slug))
        if likely_metric:
            likely_metric = self.request.build_absolute_uri(likely_metric)
        return likely_metric
