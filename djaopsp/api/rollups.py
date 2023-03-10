# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
import logging
from collections import OrderedDict

from pages.models import PageElement
from survey.mixins import DateRangeContextMixin, TimersMixin
from survey.models import Sample
from survey.utils import get_account_model, is_sqlite3

from ..compat import six
from ..queries import get_completed_assessments_at_by
from ..mixins import CampaignMixin
from ..models import ScorecardCache
from ..scores import get_score_calculator
from ..utils import TransparentCut, get_scores_tree, segments_as_sql
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
    def requested_accounts_pk_as_sql(self):
        """
        Returns the set of accounts under consideration as a string
        that can be used in SQL statements.

        The property is overriden in portfolio dashboards and overral
        benchmarking (samples.py).
        """
        if not hasattr(self, '_requested_accounts_pk_as_sql'):
            self._requested_accounts_pk_as_sql = ""
        return self._requested_accounts_pk_as_sql

    @property
    def expired_at(self):
        return self.start_at

    @property
    def search_param(self):
        if not hasattr(self, '_search_param'):
            self._search_param = self.request.GET.get('q', None)
        return self._search_param

    @property
    def sort_ordering(self):
        if not hasattr(self, '_sort_ordering'):
            sort_field = self.valid_sort_fields.get(
                self.request.GET.get('o', None))
            sort_dir = self.valid_sort_dir.get(
                self.request.GET.get('ot', 'desc'))
            if sort_field:
                self._sort_ordering = [(sort_field, sort_dir)]
            else:
                # defaults to alphabetical order for suppliers
                self._sort_ordering = [('printable_name', 'asc')]
        return self._sort_ordering

    def _get_frozen_query(self, segments):
        frozen_assessments_query = None
        frozen_improvements_query = None

        for segment in segments:
            prefix = segment['path']
            segment_query = get_completed_assessments_at_by(
                self.campaign, ends_at=self.ends_at,
                prefix=prefix, title=segment['title']).query.sql
            if not frozen_assessments_query:
                frozen_assessments_query = segment_query
            else:
                frozen_assessments_query = "(%s) UNION (%s)" % (
                    frozen_assessments_query, segment_query)
            segment_query = get_completed_assessments_at_by(
                self.campaign, ends_at=self.ends_at,
                prefix=prefix, title=segment['title'],
                extra='is_planned').query.sql
            if not frozen_improvements_query:
                frozen_improvements_query = segment_query
            else:
                frozen_improvements_query = "(%s) UNION (%s)" % (
                    frozen_improvements_query, segment_query)

        if self.expired_at:
            reporting_clause = \
"""  CASE WHEN _frozen_assessments.created_at < '%(expired_at)s'
       THEN %(reporting_expired)d
       ELSE %(reporting_completed)d END""" % {
             'expired_at': self.expired_at.isoformat(),
             'reporting_completed': ReportingSerializer.REPORTING_PLANNING_PHASE,
             'reporting_expired': ReportingSerializer.REPORTING_ABANDONED
            }
        else:
            reporting_clause = "%d" % ReportingSerializer.REPORTING_PLANNING_PHASE
        frozen_assessments_query = """SELECT
  _frozen_assessments.id AS id,
  _frozen_assessments.slug AS slug,
  _frozen_assessments.created_at AS created_at,
  _frozen_assessments.campaign_id AS campaign_id,
  _frozen_assessments.account_id AS account_id,
  _frozen_assessments.updated_at AS updated_at,
  _frozen_assessments.is_frozen AS is_frozen,
  _frozen_assessments.extra AS extra,
  _frozen_assessments.segment_path AS segment_path,
  _frozen_assessments.segment_title AS segment_title,
  %(reporting_clause)s AS reporting_status
FROM (%(query)s) AS _frozen_assessments""" % {
    'query': frozen_assessments_query.replace('%', '%%'),
    'reporting_clause': reporting_clause}

        frozen_improvements_query = """SELECT
  _frozen_improvements.id AS id,
  _frozen_improvements.slug AS slug,
  _frozen_improvements.created_at AS created_at,
  _frozen_improvements.campaign_id AS campaign_id,
  _frozen_improvements.account_id AS account_id,
  _frozen_improvements.updated_at AS updated_at,
  _frozen_improvements.is_frozen AS is_frozen,
  _frozen_improvements.extra AS extra,
  _frozen_improvements.segment_path AS segment_path,
  _frozen_improvements.segment_title AS segment_title
FROM (%(query)s) AS _frozen_improvements""" % {
    'query': frozen_improvements_query.replace('%', '%%')}

        if self.expired_at:
            reporting_clause = \
"""  CASE WHEN frozen_assessments.created_at < '%(expired_at)s'
       THEN %(reporting_expired)d
       ELSE %(reporting_completed)d END""" % {
               'expired_at': self.expired_at.isoformat(),
               'reporting_completed': ReportingSerializer.REPORTING_COMPLETED,
               'reporting_expired': ReportingSerializer.REPORTING_EXPIRED
       }
        else:
            reporting_clause = "%d" % ReportingSerializer.REPORTING_COMPLETED
        frozen_query = """
WITH frozen_assessments AS (%(frozen_assessments_query)s),
frozen_improvements AS (%(frozen_improvements_query)s)
SELECT
  frozen_assessments.id AS id,
  frozen_assessments.slug AS slug,
  frozen_assessments.created_at AS created_at,
  frozen_assessments.campaign_id AS campaign_id,
  frozen_assessments.account_id AS account_id,
  frozen_assessments.updated_at AS updated_at,
  frozen_assessments.is_frozen AS is_frozen,
  frozen_assessments.extra AS extra,
  frozen_assessments.segment_path AS segment_path,
  frozen_assessments.segment_title AS segment_title,
  0 AS nb_na_answers,
  0 AS reporting_publicly,
  0 AS reporting_fines,
  0 AS reporting_energy_consumption,
  0 AS reporting_ghg_generated,
  0 AS reporting_water_consumption,
  0 AS reporting_waste_generated,
  0 AS nb_planned_improvements,
  0 AS reporting_energy_target,
  0 AS reporting_ghg_target,
  0 AS reporting_water_target,
  0 AS reporting_waste_target,
  0 AS normalized_score,
  CASE WHEN frozen_assessments.created_at < frozen_improvements.created_at
       THEN (%(reporting_clause)s)
       ELSE frozen_assessments.reporting_status END AS reporting_status
FROM frozen_assessments
LEFT OUTER JOIN frozen_improvements
ON frozen_assessments.account_id = frozen_improvements.account_id AND
   frozen_assessments.segment_path = frozen_improvements.segment_path""" % {
       'frozen_assessments_query': frozen_assessments_query,
       'frozen_improvements_query': frozen_improvements_query,
       'reporting_clause': reporting_clause}
        # Implementation Note: frozen_improvements will always pick the latest
        # improvement plan which might not be the ones associated with
        # the latest assessment if in a subsequent year no plan is created.
        return frozen_query


    def _get_scorecard_cache_query(self, segments, ends_at=None):
        if not ends_at:
            ends_at = self.ends_at
        segments_query = segments_as_sql(segments)

        if self.expired_at:
            reporting_completed_clause = \
"""  CASE WHEN survey_sample.created_at < '%(expired_at)s'
       THEN %(reporting_expired)d
       ELSE %(reporting_completed)d END""" % {
               'expired_at': self.expired_at.isoformat(),
               'reporting_expired': ReportingSerializer.REPORTING_EXPIRED,
               'reporting_completed': ReportingSerializer.REPORTING_COMPLETED
       }
            reporting_planning_clause = \
"""  CASE WHEN survey_sample.created_at < '%(expired_at)s'
       THEN %(reporting_expired)d
       ELSE %(reporting_completed)d END""" % {
               'expired_at': self.expired_at.isoformat(),
               'reporting_expired': ReportingSerializer.REPORTING_ABANDONED,
               'reporting_completed': ReportingSerializer.REPORTING_PLANNING_PHASE
       }
        else:
            reporting_completed_clause = (
                "%d" % ReportingSerializer.REPORTING_COMPLETED)
            reporting_planning_clause = (
                "%d" % ReportingSerializer.REPORTING_PLANNING_PHASE)

        scorecard_cache_query = """WITH
segments AS (
  %(segments_query)s
),
scorecards AS (
  SELECT
    segments.path AS segment_path,
    segments.title AS segment_title,
    survey_sample.account_id AS account_id,
    MAX(survey_sample.created_at) AS created_at
  FROM %(scorecardcache_table)s
  INNER JOIN survey_sample
    ON %(scorecardcache_table)s.sample_id = survey_sample.id
  INNER JOIN segments
    ON %(scorecardcache_table)s.path = segments.path
  WHERE survey_sample.created_at < '%(ends_at)s'
  GROUP BY segments.path, segments.title, survey_sample.account_id
)
SELECT
  survey_sample.id AS id,
  survey_sample.slug AS slug,
  survey_sample.created_at AS created_at,
  survey_sample.campaign_id AS campaign_id,
  survey_sample.account_id AS account_id,
  survey_sample.updated_at AS updated_at,
  survey_sample.is_frozen AS is_frozen,
  survey_sample.extra AS extra,
  scorecards.segment_path AS segment_path,
  scorecards.segment_title AS segment_title,
  %(scorecardcache_table)s.nb_na_answers AS nb_na_answers,
  %(scorecardcache_table)s.reporting_publicly AS reporting_publicly,
  %(scorecardcache_table)s.reporting_fines AS reporting_fines,
  %(scorecardcache_table)s.reporting_energy_consumption AS reporting_energy_consumption,
  %(scorecardcache_table)s.reporting_ghg_generated AS reporting_ghg_generated,
  %(scorecardcache_table)s.reporting_water_consumption AS reporting_water_consumption,
  %(scorecardcache_table)s.reporting_waste_generated AS reporting_waste_generated,
  %(scorecardcache_table)s.reporting_energy_target AS reporting_energy_target,
  %(scorecardcache_table)s.reporting_ghg_target AS reporting_ghg_target,
  %(scorecardcache_table)s.reporting_water_target AS reporting_water_target,
  %(scorecardcache_table)s.reporting_waste_target AS reporting_waste_target,
  %(scorecardcache_table)s.nb_planned_improvements AS nb_planned_improvements,
  %(scorecardcache_table)s.normalized_score AS normalized_score,
  CASE WHEN %(scorecardcache_table)s.nb_planned_improvements > 0
       THEN (%(reporting_completed_clause)s)
       ELSE (%(reporting_planning_clause)s) END AS reporting_status
FROM %(scorecardcache_table)s
INNER JOIN scorecards
  ON %(scorecardcache_table)s.path = scorecards.segment_path
INNER JOIN survey_sample
  ON survey_sample.id = %(scorecardcache_table)s.sample_id AND
     survey_sample.account_id = scorecards.account_id AND
     survey_sample.created_at = scorecards.created_at
WHERE survey_sample.created_at < '%(ends_at)s'
""" % {
    'ends_at': ends_at.isoformat(),
    'segments_query': segments_query,
    'reporting_planning_clause': reporting_planning_clause,
    'reporting_completed_clause': reporting_completed_clause,
    #pylint:disable=protected-access
    'scorecardcache_table': ScorecardCache._meta.db_table
}
        return scorecard_cache_query

    @property
    def scores_of_interest(self):
        """
        Returns the segments/tiles we are interested in for this query.
        """
        if not hasattr(self, '_scores_of_interest'):
            self._scores_of_interest = self.segments_available
        return self._scores_of_interest

    def get_queryset(self):
        #pylint:disable=protected-access
        if not self.scores_of_interest:
            # We don't have any scorecard/chart to compute.
            return Sample.objects.none()

        # The scores_of_interest do not represent solely segments. They might
        # also represent sections within a segment (see benchmarks API).
        # None-the-less as long as all segments in a survey are scored, this
        # code will work to differentiate between using the scorecard cache
        # and just getting frozen samples.
        use_scorecard_cache = False
        for seg in self.scores_of_interest:
            prefix = seg.get('path')
            if prefix:
                score_calculator = get_score_calculator(prefix)
                if score_calculator:
                    use_scorecard_cache = True
                    break
        if use_scorecard_cache:
            frozen_query = self._get_scorecard_cache_query(
                self.scores_of_interest)
        else:
            frozen_query = self._get_frozen_query(self.scores_of_interest)

        if self.expired_at:
            reporting_clause = \
"""  CASE WHEN active_assessments.created_at < '%(expired_at)s'
       THEN %(reporting_abandoned)d
       ELSE %(reporting_inprogress)d END""" % {
               'expired_at': self.expired_at.isoformat(),
               'reporting_inprogress':
                   ReportingSerializer.REPORTING_ASSESSMENT_PHASE,
               'reporting_abandoned': ReportingSerializer.REPORTING_ABANDONED
       }
        else:
            reporting_clause = \
                "%d" % ReportingSerializer.REPORTING_ASSESSMENT_PHASE

        if self.db_path and self.db_path != self.DB_PATH_SEP:
            assessments_query = frozen_query
        else:
            assessments_query = """
WITH frozen AS (%(frozen_query)s)
SELECT
  COALESCE(frozen.id, active_assessments.id) AS id,
  COALESCE(frozen.slug, active_assessments.slug) AS slug,
  frozen.created_at AS created_at,
  COALESCE(frozen.campaign_id, active_assessments.campaign_id) AS campaign_id,
  COALESCE(frozen.account_id, active_assessments.account_id) AS account_id,
  active_assessments.updated_at AS updated_at,
  COALESCE(frozen.is_frozen, active_assessments.is_frozen) AS is_frozen,
  COALESCE(frozen.extra, active_assessments.extra) AS extra,
  frozen.segment_path AS segment_path,
  frozen.segment_title AS segment_title,
  frozen.nb_na_answers AS nb_na_answers,
  frozen.reporting_publicly AS reporting_publicly,
  frozen.reporting_fines AS reporting_fines,
  frozen.reporting_energy_consumption AS reporting_energy_consumption,
  frozen.reporting_ghg_generated AS reporting_ghg_generated,
  frozen.reporting_water_consumption AS reporting_water_consumption,
  frozen.reporting_waste_generated AS reporting_waste_generated,
  frozen.nb_planned_improvements AS nb_planned_improvements,
  frozen.reporting_energy_target AS reporting_energy_target,
  frozen.reporting_ghg_target AS reporting_ghg_target,
  frozen.reporting_water_target AS reporting_water_target,
  frozen.reporting_waste_target AS reporting_waste_target,
  frozen.normalized_score AS normalized_score,
  COALESCE(frozen.reporting_status, %(reporting_clause)s) AS reporting_status
FROM (SELECT
    survey_sample.id AS id,
    survey_sample.slug AS slug,
    survey_sample.created_at AS created_at,
    survey_sample.campaign_id AS campaign_id,
    survey_sample.account_id AS account_id,
    survey_sample.updated_at AS updated_at,
    survey_sample.is_frozen AS is_frozen,
    survey_sample.extra AS extra
    FROM survey_sample
    WHERE survey_sample.extra IS NULL AND
          NOT survey_sample.is_frozen AND
          survey_sample.campaign_id = %(campaign_id)d
) AS active_assessments
LEFT OUTER JOIN frozen
ON active_assessments.account_id = frozen.account_id AND
   active_assessments.campaign_id = frozen.campaign_id""" % {
       'frozen_query': frozen_query,
       'campaign_id': self.campaign.id,
       'reporting_clause': reporting_clause}

        accounts_clause = ""
        if self.requested_accounts_pk_as_sql:
            accounts_clause = "%(account_table)s.id IN %(account_ids)s" % {
                'account_table': self.account_model._meta.db_table,
                'account_ids': self.requested_accounts_pk_as_sql}
            if self.search_param:
                if accounts_clause:
                    accounts_clause += "AND "
                accounts_clause += (
                "%(account_table)s.full_name ILIKE '%%%%%(search_param)s%%%%'"
                    % {
                        'account_table': self.account_model._meta.db_table,
                        'search_param': self.search_param})
        if accounts_clause:
            accounts_clause = "WHERE %s" % accounts_clause
        else:
            return Sample.objects.none()

        order_clause = ""
        if self.sort_ordering:
            order_clause = "ORDER BY "
            sep = ""
            for sort_field, sort_dir in self.sort_ordering:
                order_clause += "%s%s %s" % (sep, sort_field, sort_dir)
                if sort_field in ('last_activity_at', 'last_completed_at'):
                    order_clause += " NULLS LAST"
                sep = ", "
        query = """
WITH assessments AS (%(assessments_query)s)
SELECT
  assessments.id AS id,
  assessments.slug AS slug,
  assessments.created_at AS created_at,
  assessments.campaign_id AS campaign_id,
  COALESCE(assessments.account_id, %(account_table)s.id) AS account_id,
  assessments.updated_at AS updated_at,
  assessments.is_frozen AS is_frozen,
  assessments.extra AS extra,
  assessments.segment_path AS segment_path,
  assessments.segment_title AS segment,    -- XXX should be segment_title
  assessments.nb_na_answers AS nb_na_answers,
  assessments.reporting_publicly AS reporting_publicly,
  assessments.reporting_fines AS reporting_fines,
  assessments.reporting_energy_consumption AS reporting_energy_consumption,
  assessments.reporting_ghg_generated AS reporting_ghg_generated,
  assessments.reporting_water_consumption AS reporting_water_consumption,
  assessments.reporting_waste_generated AS reporting_waste_generated,
  assessments.nb_planned_improvements AS nb_planned_improvements,
  assessments.reporting_energy_target AS reporting_energy_target,
  assessments.reporting_ghg_target AS reporting_ghg_target,
  assessments.reporting_water_target AS reporting_water_target,
  assessments.reporting_waste_target AS reporting_waste_target,
  assessments.normalized_score AS normalized_score,
  COALESCE(assessments.reporting_status, %(reporting_status)d) AS reporting_status,
  %(account_table)s.slug AS account_slug,
  %(account_table)s.full_name AS printable_name,
  %(account_table)s.email AS email,
  %(account_table)s.phone AS phone,
  assessments.created_at AS last_completed_at,
  assessments.updated_at AS last_activity_at,
  '' AS score_url                              -- updated later
FROM %(account_table)s
%(join_clause)s JOIN assessments
ON %(account_table)s.id = assessments.account_id
%(accounts_clause)s
%(order_clause)s""" % {
    'assessments_query': assessments_query,
#XXX    'join_clause': "INNER" if self.db_path else "LEFT OUTER",
    'join_clause': "LEFT OUTER",
    'account_table': self.account_model._meta.db_table,
    'reporting_status': ReportingSerializer.REPORTING_NOT_STARTED,
    'accounts_clause': accounts_clause,
    'order_clause': order_clause}

        # XXX still need to compute status and score.
        # XXX still need to add order by clause.
        return Sample.objects.raw(query)


class RollupMixin(object):

    def _insert_in_tree(self, rollup_tree, prefix, value):
        for path, node in six.iteritems(rollup_tree):
            if path == prefix:
                accounts = node[0].get('accounts', {})
                # `accounts` (`get_requested_accounts`) used
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
                    slug=prefix.split(self.DB_PATH_SEP)[-1])]
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
                    distribution = {
                        'x' : ["0-25%", "25-50%", "50-75%", "75-100%"],
                        'y' : [0 for _ in range(4)],
                        'organization_rate': ""
                    }
                if normalized_score < 25:
                    distribution['y'][0] += 1
                    if is_view_account:
                        distribution['organization_rate'] = distribution['x'][0]
                elif normalized_score < 50:
                    distribution['y'][1] += 1
                    if is_view_account:
                        distribution['organization_rate'] = distribution['x'][1]
                elif normalized_score < 75:
                    distribution['y'][2] += 1
                    if is_view_account:
                        distribution['organization_rate'] = distribution['x'][2]
                else:
                    assert normalized_score <= 100
                    distribution['y'][3] += 1
                    if is_view_account:
                        distribution['organization_rate'] = distribution['x'][3]

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
                    'distribution': distribution
                })
            elif TransparentCut.TAG_SCORECARD in node[0].get(
                    'extra', {}).get('tags', []):
                node[0].update({
                    'nb_respondents': nb_respondents,
                    'distribution': []
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
                if 'distribution' in chart[0]:
                    normalized_score = chart[0].get('normalized_score', None)
                    complete &= (normalized_score is not None)
        return charts, complete
