# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
import logging
from collections import OrderedDict

from pages.models import PageElement
from survey.mixins import DateRangeContextMixin, TimersMixin
from survey.models import Sample
from survey.queries import get_account_model, is_sqlite3
from survey.settings import DB_PATH_SEP

from ..compat import six
from ..queries import (get_completed_assessments_at_by,
    get_scored_assessments)
from ..mixins import CampaignMixin
from ..models import ScorecardCache
from ..scores import get_score_calculator
from ..utils import TransparentCut, get_scores_tree
from .serializers import ReportingSerializer

LOGGER = logging.getLogger(__name__)


class ScoresMixin(TimersMixin, DateRangeContextMixin, CampaignMixin):
    """
    The dashboard contains the columns:
      - Supplier/facility: derived from `sample.account_id`
      - Last activity: derived from `sample.created_at` as long as
      (max(survey_answer.created_at) where survey_answer.sample_id = sample.id)
      < sample.created_at
      - Status: derived from last_assessment.is_frozen,
          last_assessment.created_at, last_improvement.created_at
      - Industry segment: derived from `get_segments(sample)`
      - Score: derived from answers with metric = score.
      - # N/A: derived from count(answer) where sample = last_assessment and
          answer.measured = 'N/A'
      - Reporting publicly: derived from exists(answer) where
          sample = last_assessment and answer.measured = 'yes' and
          answer.question = 'reporting publicly'
      - Environmental files: derived from exists(answer) where
          sample = last_assessment and answer.measured = 'yes' and
          answer.question = 'environmental fines'
      - Planned actions: derived from count(answer) where
          sample = last_improvement and answer.measured = 'improve'

    If we sort by "Supplier/facility", "# N/A", "Reporting publicly",
    or "Environmental files", it is possible to do it in the assessment SQL
    query.
    If we sort by "Planned actions", it is possible to do it in the improvement
    SQL query.
    If we sort by "Industry segment", it might be possible to do it in the
    assessment SQL query provided we decorate Samples with the industry.

    XXX If we sort by "Last activity"?
    XXX If we sort by "Status"?

    XXX If we sort by "Score", we have to re-compute all scores from answers.

    The queryset can be further filtered to a range of dates between
    ``start_at`` and ``ends_at``.

    The queryset can be further filtered by passing a ``q`` parameter.
    The value in ``q`` will be matched against:

      - user.username
      - user.first_name
      - user.last_name
      - user.email

    The result queryset can be ordered by passing an ``o`` (field name)
    and ``ot`` (asc or desc) parameter.
    The fields the queryset can be ordered by are:

      - user.first_name
      - user.last_name
      - created_at
    """
    model = Sample
    account_model = get_account_model()

    search_fields = ['printable_name',
                     'email']

    valid_sort_fields = {
        'printable_name': 'printable_name',
        'last_activity_at': 'last_activity_at',
        'reporting_status': 'reporting_status',
        'last_completed_at': 'last_completed_at',
        'segment': 'segment',
        'normalized_score': 'normalized_score',
        'nb_na_answers': 'nb_na_answers',
        'reporting_publicly': 'reporting_publicly',
        'reporting_fines': 'reporting_fines',
        'nb_planned_improvements': 'nb_planned_improvements',
        'reporting_energy_consumption': 'reporting_energy_consumption',
        'reporting_ghg_generated': 'reporting_ghg_generated',
        'reporting_water_consumption': 'reporting_water_consumption',
        'reporting_waste_generated': 'reporting_waste_generated',
        'reporting_energy_target': 'reporting_energy_target',
        'reporting_ghg_target': 'reporting_ghg_target',
        'reporting_water_target': 'reporting_water_target',
        'reporting_waste_target': 'reporting_waste_target'
    }

    valid_sort_dir = {
        'asc': 'asc',
        'desc': 'desc'
    }

    sample_queryset = Sample.objects.all()

    @property
    def expired_at(self):
        return self.start_at

    @property
    def sort_ordering(self):
        if not hasattr(self, '_sort_ordering'):
            sort_field = self.valid_sort_fields.get(
                self.get_query_param('o', None))
            sort_dir = self.valid_sort_dir.get(
                self.get_query_param('ot', 'desc'))
            if sort_field:
                self._sort_ordering = [(sort_field, sort_dir)]
            else:
                # defaults to alphabetical order for suppliers
                self._sort_ordering = [('printable_name', 'asc')]
        return self._sort_ordering


    @property
    def scores_of_interest(self):
        """
        Returns the segments/tiles we are interested in for this query.
        """
        if not hasattr(self, '_scores_of_interest'):
            self._scores_of_interest = self.segments_available
        return self._scores_of_interest

    def get_queryset(self):
        return get_scored_assessments(
            self.campaign,
            accounts=self.requested_accounts,
            scores_of_interest=self.scores_of_interest,
            db_path=self.db_path,
            ends_at=self.ends_at,
            expired_at=self.expired_at,
            sort_ordering=self.sort_ordering)


class RollupMixin(object):

    def _insert_in_tree(self, rollup_tree, prefix, value):
        for path, node in six.iteritems(rollup_tree):
            if path == prefix:
                accounts = node[0].get('accounts', {})
                # `accounts` used
                # in `decorate_with_cohorts` is a dictionary indexed by id,
                # so we cannot use value.account.slug.
                account_id = value.account_id
                account = accounts.get(account_id, {})
                account.update({'normalized_score': value.normalized_score})
                if account_id not in accounts:
                    accounts.update({account_id: account})
                if 'accounts' not in node[0]:
                    node[0].update({'accounts': accounts})
                return True
            if self._insert_in_tree(node[1], prefix, value):
                return True
        return False

    def rollup_scores(self, queryset, prefix=None):
        roots = None
        if prefix:
            try:
                roots = [PageElement.objects.get(
                    slug=prefix.split(DB_PATH_SEP)[-1])]
            except PageElement.DoesNotExist:
                roots = None
        self._report_queries("[get_scores_tree] entry point")
        rollup_tree = get_scores_tree(roots, prefix=prefix)
        self._report_queries("%d score tree loaded" % len(rollup_tree))
        for score in queryset:
            self._insert_in_tree(rollup_tree, score.segment_path, score)

        self._report_queries("completed rollup_scores")
        return rollup_tree


class GraphMixin(object):

    def get_charts(self, rollup_tree, excludes=None):
        charts = []
        for values in six.itervalues(rollup_tree):
            extra = values[0].get('extra', {})
            tags = extra.get('tags', []) if extra else []
            if tags and TransparentCut.TAG_SCORECARD in tags:
                if not excludes or values[0].get('slug', "") in excludes:
                    charts += [values[0]]
            sub_charts = self.get_charts(values[1], excludes=excludes)
            charts += sub_charts
        return charts

    def create_distributions(self, rollup_tree, view_account_id=None):
        #pylint:disable=too-many-statements
        """
        Create a tree with distributions of scores from a rollup tree.
        """
        #pylint:disable=too-many-locals
        for node in six.itervalues(rollup_tree):
            denominator = None
            highest_normalized_score = 0
            sum_normalized_scores = 0
            nb_normalized_scores = 0
            nb_respondents = 0
            nb_implemeted_respondents = 0
            distribution = None
            for account_id_str, scores in six.iteritems(node[0].get(
                    'accounts', OrderedDict({}))):
                if account_id_str is None: # XXX why is that?
                    continue
                try:
                    account_id = int(account_id_str)
                    is_view_account = (view_account_id and
                        account_id == view_account_id)
                except ValueError:
                    is_view_account = False

                if is_view_account:
                    node[0].update(scores)

                if scores.get('normalized_score', 0):
                    # XXX assumes that normalized_score == 0 is an incomplete
                    # answer.
                    nb_respondents += 1

                normalized_score = scores.get('normalized_score', None)
                if normalized_score is None:
                    continue

                nb_normalized_scores += 1
                numerator = scores.get('numerator')
                denominator = scores.get('denominator')
                if numerator == denominator:
                    nb_implemeted_respondents += 1
                if normalized_score > highest_normalized_score:
                    highest_normalized_score = normalized_score
                sum_normalized_scores += normalized_score
                if distribution is None:
                    distribution = [
                        ["0-25%", 0],
                        ["25-50%", 0],
                        ["50-75%", 0],
                        ["75-100%", 0]
                    ]
                    organization_rate = ""
                if normalized_score < 25:
                    distribution[0][1] += 1
                    if is_view_account:
                        organization_rate = distribution[0][0]
                elif normalized_score < 50:
                    distribution[1][1] += 1
                    if is_view_account:
                        organization_rate = distribution[1][0]
                elif normalized_score < 75:
                    distribution[2][1] += 1
                    if is_view_account:
                        organization_rate = distribution[2][0]
                else:
                    assert normalized_score <= 100
                    distribution[3][1] += 1
                    if is_view_account:
                        organization_rate = distribution[3][0]

            self.create_distributions(node[1], view_account_id=view_account_id)

            if distribution is not None:
                if nb_respondents > 0:
                    avg_normalized_score = int(
                        sum_normalized_scores / nb_normalized_scores)
                    rate = int(100.0
                        * nb_implemeted_respondents / nb_normalized_scores)
                else:
                    avg_normalized_score = 0
                    rate = 0
                node[0].update({
                    'nb_respondents': nb_respondents,
                    'rate': rate,
                    'opportunity': denominator,
                    'highest_normalized_score': highest_normalized_score,
                    'avg_normalized_score': avg_normalized_score,
                    'organization_rate': organization_rate,
                    'benchmarks': [{
                        'slug': "all",
                        'title': "All",
                        'values': distribution
                    }]
                })
            elif TransparentCut.TAG_SCORECARD in node[0].get(
                    'extra', {}).get('tags', []):
                node[0].update({
                    'nb_respondents': nb_respondents,
                    'benchmarks': []
                })
            if 'accounts' in node[0]:
                del node[0]['accounts']

    def flatten_distributions(self, distribution_tree, prefix=None):
        """
        Flatten the tree into a list of charts.
        """
        # XXX Almost identical to get_charts. Can we abstract differences?
        if prefix is None:
            prefix = "/"
        if not prefix.startswith("/"):
            prefix = '/%s' % prefix
        charts = []
        complete = True
        for key, chart in six.iteritems(distribution_tree):
            if key.startswith(prefix) or prefix.startswith(key):
                leaf_charts, leaf_complete = self.flatten_distributions(
                    chart[1], prefix=prefix)
                charts += leaf_charts
                complete &= leaf_complete
                charts += [chart[0]]
                if 'benchmarks' in chart[0]:
                    normalized_score = chart[0].get('normalized_score', None)
                    complete &= (normalized_score is not None)
        return charts, complete
