# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

# pylint:disable=too-many-lines

from __future__ import absolute_import
from __future__ import unicode_literals

import json, logging, re
from collections import OrderedDict, namedtuple

from dateutil.relativedelta import relativedelta
from deployutils.crypt import JSONEncoder
from deployutils.helpers import datetime_or_now
from django.conf import settings
from django.db import connection
from django.db.models import Q, Count, Max
from django.utils import six
from django.utils.dateparse import parse_datetime
from django.utils.timezone import utc
from pages.mixins import TrailMixin
from pages.models import PageElement
from rest_framework import generics
from rest_framework.response import Response as HttpResponse
from survey.models import  Answer, Choice, Metric, Sample, Unit

from .best_practices import ToggleTagContentAPIView
from ..compat import reverse
from ..helpers import (get_segments_from_samples, as_measured_value,
    get_testing_accounts)
from ..mixins import ReportMixin, TransparentCut, ContentCut
from ..models import (_show_query_and_result, get_score_weight,
    get_scored_answers, get_frozen_scored_answers, get_historical_scores,
    Consumption)
from ..serializers import (BenchmarkSerializer, MetricsSerializer,
    ScoreWeightSerializer, PracticeBenchmarkSerializer, ConsumptionSerializer)
from ..scores import (populate_account, populate_account_na_answers,
    populate_account_planned_improvements, populate_rollup)

LOGGER = logging.getLogger(__name__)


class AssessmentAnswer(object):

    def __init__(self, **kwargs):
        for key, val in six.iteritems(kwargs):
            setattr(self, key, val)

    def __getattr__(self, name):
        return getattr(self.consumption, name)


class PracticeBenchmarkMixin(ReportMixin):
    # Implementation Note: uses BestPracticeMixin in order to display
    # bestpractice info through links in assess and improve pages.

    def _framework_results(self, consumptions):
        if self.campaign.slug == 'framework':
            ends_at = self.sample.created_at + relativedelta(months=1)
            last_frozen_assessments = \
                Consumption.objects.get_latest_assessment_by_accounts(
                    self.campaign, before=ends_at,
                    excludes=get_testing_accounts())
            results = Answer.objects.filter(
                metric_id=self.default_metric_id,
                sample_id__in=last_frozen_assessments
            ).values('question__path', 'measured').annotate(Count('sample_id'))
            totals = {}
            for row in Answer.objects.filter(
                    metric_id=self.default_metric_id,
                    sample_id__in=last_frozen_assessments
                    ).values('question__path').annotate(Count('sample_id')):
                totals[row['question__path']] = row['sample_id__count']
            choices = {}
            for choice in Choice.objects.filter(
                    unit__metric=self.default_metric_id):
                choices[choice.pk] = choice.text

            for row in results:
                path = row['question__path']
                measured = row['measured']
                count = row['sample_id__count']
                consumption = consumptions.get(path, None)
                if consumption:
                    if not isinstance(consumption.rate, dict):
                        if not isinstance(consumption, AssessmentAnswer):
                            consumptions[path] = AssessmentAnswer(
                                consumption=consumption, rate={})
                            consumption = consumptions[path]
                        else:
                            consumption.rate = {}
                    total = totals.get(path, None)
                    consumption.rate[choices[measured]] = \
                        int(count * 100 // total)

    def decorate_leafs(self, leafs):
        """
        Adds consumptions, implementation rate, number of respondents,
        assessment and improvement answers and opportunity score.

        For each answer the improvement opportunity in the total score is
        case NO / NEEDS_SIGNIFICANT_IMPROVEMENT
          numerator = (3-A) * opportunity + 3 * avg_value / nb_respondents
          denominator = 3 * avg_value / nb_respondents
        case YES / NEEDS_MODERATE_IMPROVEMENT
          numerator = (3-A) * opportunity
          denominator = 0
        """
        #pylint:disable=too-many-locals,too-many-statements
        consumptions = {}
        consumptions_planned = {}
        # The call to `get_expected_opportunities` within `get_scored_answers`
        # will insure all questions for the assessment are picked up, either
        # they have an answer or not.
        # This is done by listing all question in `get_opportunities_sql`
        # and filtering them out through the `survey_enumeratedquestions`
        # table in `get_expected_opportunities`.
        scored_answers = get_scored_answers(
            Consumption.objects.get_active_by_accounts(
                self.campaign, excludes=self._get_filter_out_testing()),
            self.default_metric_id,
            includes=self.get_included_samples())

        # We are running the query a second time because we did not populate
        # all Consumption fields through the aggregate.
        with connection.cursor() as cursor:
            cursor.execute(scored_answers, params=None)
            col_headers = cursor.description
            consumption_tuple = namedtuple(
                'ConsumptionTuple', [col[0] for col in col_headers])
            for consumption in cursor.fetchall():
                consumption = consumption_tuple(*consumption)
                if consumption.is_planned:
                    if consumption.answer_id:
                        if self.campaign.slug == 'framework':
                            consumptions_planned.update({
                                consumption.path: consumption.implemented})
                        else:
                            # This is part of the plan, we mark it for
                            # the planning page but otherwise don't use values
                            # stored here.
                            consumptions_planned.update({
                                consumption.path: True})
                else:
                    consumptions[consumption.path] = consumption

        # Get reported measures / comments
        for datapoint in Answer.objects.filter(sample=self.sample).exclude(
                    metric__in=Metric.objects.filter(
                    slug__in=Consumption.NOT_MEASUREMENTS_METRICS)
                ).select_related('question').order_by('-metric_id'):
            consumption = consumptions[datapoint.question.path]
            if not hasattr(consumption, 'measures'):
                consumptions[datapoint.question.path] = AssessmentAnswer(
                    consumption=consumption, measures=[])
                consumption = consumptions[datapoint.question.path]
            unit = (datapoint.unit if datapoint.unit else datapoint.metric.unit)
            measured = as_measured_value(datapoint)
            measure = {
                'metric': datapoint.metric,
                'unit': unit,
                'measured': measured,
                'created_at': datapoint.created_at,
#XXX                'collected_by': datapoint.collected_by,
            }
            if datapoint.metric.slug == 'target-baseline':
                measure['text'] = "baseline %s" % str(measured)
            elif datapoint.metric.slug == 'target-by':
                measure['text'] = "by %s" % str(measured)
            elif unit.system in [Unit.SYSTEM_STANDARD, Unit.SYSTEM_IMPERIAL]:
                measure['text'] = "%s %s" % (measured, unit.title)
            consumption.measures += [measure]

        # Find all framework samples / answers for a time period
        self._framework_results(consumptions)

        # Populate leafs and cut nodes with data.
        for path, vals in six.iteritems(leafs):
            # First, let's split the text fields in multiple rows
            # so we can populate the choices.
            if 'text' in vals[0]:
                vals[0]['text'] = vals[0]['text'].splitlines()
            consumption = consumptions.get(path, None)
            if consumption:
                if (path.startswith('/euissca-rfx') and #XXX /rfx hack
                    not consumption.answer_id):
                    answer = Answer.objects.filter(sample=self.sample,
                        metric_id=self.default_metric_id,
                        question__path__endswith=path.split('/')[-1]).first()
                    if answer:
                        answer.pk = None
                        answer.question = Consumption.objects.get(path=path)
                        answer.save()
                        if not hasattr(consumption, 'measures'):
                            consumption = AssessmentAnswer(
                                consumption=consumption, measures=[])
                        consumption.answer_id = answer.pk
                        consumption.implemented = as_measured_value(answer)
                avg_value = consumption.avg_value
                opportunity = consumption.opportunity
                nb_respondents = consumption.nb_respondents
                if nb_respondents > 0:
                    added = 3 * avg_value / float(nb_respondents)
                else:
                    added = 0
                if 'accounts' not in vals[0]:
                    vals[0]['accounts'] = {}
                if self.account.pk not in vals[0]['accounts']:
                    vals[0]['accounts'][self.account.pk] = {}
                populate_account(vals[0]['accounts'], consumption)
                scores = vals[0]['accounts'][self.account.pk]
                if (consumption.implemented ==
                    Consumption.ASSESSMENT_ANSWERS[Consumption.YES]) or (
                    consumption.implemented ==
                Consumption.ASSESSMENT_ANSWERS[Consumption.NOT_APPLICABLE]):
                    scores.update({
                        'opportunity_numerator': 0,
                        'opportunity_denominator': 0
                    })
                elif (consumption.implemented ==
                      Consumption.ASSESSMENT_ANSWERS[
                          Consumption.NEEDS_SIGNIFICANT_IMPROVEMENT]):
                    scores.update({
                        'opportunity_numerator': opportunity,
                        'opportunity_denominator': 0
                    })
                elif (consumption.implemented ==
                      Consumption.ASSESSMENT_ANSWERS[
                          Consumption.NEEDS_MODERATE_IMPROVEMENT]):
                    scores.update({
                        'opportunity_numerator': 2 * opportunity + added,
                        'opportunity_denominator': added
                    })
                else:
                    # No and not yet answered.
                    scores.update({
                        'opportunity_numerator': 3 * opportunity + added,
                        'opportunity_denominator': added
                    })
                vals[0]['consumption'] \
                    = ConsumptionSerializer(context={
                        'campaign': self.campaign,
                        'planned': consumptions_planned.get(path, None)
                    }).to_representation(consumption)
            else:
                # Cut node: loads icon url.
                vals[0]['consumption'] = None
                text = PageElement.objects.filter(
                    slug=vals[0]['slug']).values('text').first()
                if text and text['text']:
                    vals[0].update(text)


class BenchmarkMixin(ReportMixin):

    @property
    def start_at(self):
        if not hasattr(self, '_start_at'):
            self._start_at = self.request.GET.get('start_at', None)
            if self._start_at:
                try:
                    self._start_at = datetime_or_now(self._start_at.strip('"'))
                except ValueError:
                    self._start_at = None
        return self._start_at

    def get_highlighted_practices(self):
        from_root, trail = self.breadcrumbs
        url_prefix = trail[-1][1] if trail else ""

        flt = Q(path__startswith=from_root,
            answer__sample=self.assessment_sample,
            answer__metric_id=self.default_metric_id,
            answer__measured=Consumption.NOT_APPLICABLE)
        if self.improvement_sample:
            flt = flt | Q(path__startswith=from_root,
                answer__sample=self.improvement_sample,
                answer__metric_id=self.default_metric_id,
                answer__measured=Consumption.NEEDS_SIGNIFICANT_IMPROVEMENT)
        highlighted_practices = Consumption.objects.filter(flt).values(
            'path', 'answer__sample_id', 'answer__measured')

        depth = len(from_root.split('/')) + 1
        root = (OrderedDict({}), OrderedDict({}))
        assessment_sample_pk = (
            self.assessment_sample.id if self.assessment_sample else 0)
        improvement_sample_pk = (
            self.improvement_sample.id if self.improvement_sample else 0)
        for practice in highlighted_practices:
            node = self._insert_path(root, practice['path'], depth=depth)
            if (practice['answer__sample_id'] == assessment_sample_pk and
                practice['answer__measured'] == Consumption.NOT_APPLICABLE):
                node[0].update({'not_applicable': True})
            if practice['answer__sample_id'] == improvement_sample_pk:
                node[0].update({'planned': True})

        # Populate environmental metrics answers
        root = self._get_measured_metrics_context(root, from_root)
        root = self._natural_order(root)
        return self.flatten_answers(root, url_prefix)

    def get_context_data(self, **kwargs):
        context = super(BenchmarkMixin, self).get_context_data(**kwargs)
        context.update({
            'highlighted_practices': self.get_highlighted_practices(),
        })
        return context

    def get_drilldown(self, rollup_tree, prefix):
        accounts = None
        node = rollup_tree[1].get(prefix, None)
        if node:
            accounts = rollup_tree[0].get('accounts', OrderedDict({}))
        elif prefix == 'totals' or rollup_tree[0].get('slug', '') == prefix:
            accounts = rollup_tree[0].get('accounts', OrderedDict({}))
        else:
            for node in six.itervalues(rollup_tree[1]):
                accounts = self.get_drilldown(node, prefix)
                if accounts is not None:
                    break
        # Filter out accounts whose score cannot be computed.
        if accounts is not None:
            all_accounts = accounts
            accounts = OrderedDict({})
            for account_id, account_metrics in six.iteritems(all_accounts):
                normalized_score = account_metrics.get('normalized_score', None)
                if normalized_score is not None:
                    accounts[account_id] = account_metrics

        return accounts

    def get_charts(self, rollup_tree, excludes=None):
        charts = []
        icon_tag = rollup_tree[0].get('tag', "")
        if icon_tag and settings.TAG_SCORECARD in icon_tag:
            if not (excludes and rollup_tree[0].get('slug', "") in excludes):
                charts += [rollup_tree[0]]
        for _, icon_tuple in six.iteritems(rollup_tree[1]):
            sub_charts = self.get_charts(icon_tuple, excludes=excludes)
            charts += sub_charts
        return charts


    def create_distributions(self, rollup_tree, view_account=None):
        #pylint:disable=too-many-statements
        """
        Create a tree with distributions of scores from a rollup tree.
        """
        #pylint:disable=too-many-locals
        denominator = None
        highest_normalized_score = 0
        sum_normalized_scores = 0
        nb_normalized_scores = 0
        nb_respondents = 0
        nb_implemeted_respondents = 0
        distribution = None
        for account_id_str, account_metrics in six.iteritems(rollup_tree[0].get(
                'accounts', OrderedDict({}))):
            if account_id_str is None: # XXX why is that?
                continue
            account_id = int(account_id_str)
            is_view_account = (view_account and account_id == view_account)

            if is_view_account:
                rollup_tree[0].update(account_metrics)

            if account_metrics.get('nb_answers', 0):
                nb_respondents += 1

            normalized_score = account_metrics.get('normalized_score', None)
            if normalized_score is None:
                continue

            nb_normalized_scores += 1
            numerator = account_metrics.get('numerator')
            denominator = account_metrics.get('denominator')
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

        for node_metrics in six.itervalues(rollup_tree[1]):
            self.create_distributions(node_metrics, view_account=view_account)

        if distribution is not None:
            if nb_respondents > 0:
                avg_normalized_score = int(
                    sum_normalized_scores / nb_normalized_scores)
                rate = int(100.0
                    * nb_implemeted_respondents / nb_normalized_scores)
            else:
                avg_normalized_score = 0
                rate = 0
            rollup_tree[0].update({
                'nb_respondents': nb_respondents,
                'rate': rate,
                'opportunity': denominator,
                'highest_normalized_score': highest_normalized_score,
                'avg_normalized_score': avg_normalized_score,
                'distribution': distribution
            })
        if 'accounts' in rollup_tree[0]:
            del rollup_tree[0]['accounts']

    # BenchmarkMixin.flatten_distributions
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
        for key, chart in six.iteritems(distribution_tree[1]):
            if key.startswith(prefix) or prefix.startswith(key):
                leaf_charts, leaf_complete = self.flatten_distributions(
                    chart, prefix=prefix)
                charts += leaf_charts
                complete &= leaf_complete
                charts += [chart[0]]
                if 'distribution' in chart[0]:
                    normalized_score = chart[0].get('normalized_score', None)
                    complete &= (normalized_score is not None)
        return charts, complete

    @staticmethod
    def get_distributions(numerators, denominators, view_sample=None):
        distribution = {
            'x' : ["0-25%", "25-50%", "50-75%", "75-100%"],
            'y' : [0 for _ in range(4)],
            'normalized_score': 0,  # instead of 'ukn.' to avoid js error.
            'organization_rate': ""
        }
        for sample, numerator in six.iteritems(numerators):
            denominator = denominators.get(sample, 0)
            if denominator != 0:
                normalized_score = int(numerator * 100 / denominator)
            else:
                normalized_score = 0
            if sample == view_sample:
                distribution['normalized_score'] = normalized_score
            if normalized_score < 25:
                distribution['y'][0] += 1
                if sample == view_sample:
                    distribution['organization_rate'] = distribution['x'][0]
            elif normalized_score < 50:
                distribution['y'][1] += 1
                if sample == view_sample:
                    distribution['organization_rate'] = distribution['x'][1]
            elif normalized_score < 75:
                distribution['y'][2] += 1
                if sample == view_sample:
                    distribution['organization_rate'] = distribution['x'][2]
            else:
                assert normalized_score <= 100
                distribution['y'][3] += 1
                if sample == view_sample:
                    distribution['organization_rate'] = distribution['x'][3]
        return distribution

    def _get_scored_answers(self, population, metric_id,
                            includes=None, prefix=None):
        if self.is_frozen:
            return get_frozen_scored_answers(population,
                datetime_or_now(self.ends_at), prefix=prefix)
        return get_scored_answers(population, metric_id,
            includes=includes, prefix=prefix)

    @staticmethod
    def _get_na_answers(population, metric_id, includes=None, prefix=None):
        return None

    @staticmethod
    def _get_planned_improvements(population, metric_id,
                                  includes=None, prefix=None):
        return None

    @property
    def requested_accounts_pk(self):
        return []

    @property
    def requested_accounts_pk_as_sql(self):
        if not hasattr(self, '_requested_accounts_pk_as_sql'):
            self._requested_accounts_pk_as_sql = "(%s)" % ','.join(
                [str(pk) for pk in self.requested_accounts_pk])
        return self._requested_accounts_pk_as_sql

    def rollup_scores(self, roots=None, root_prefix=None, force_score=False):
        """
        Returns a tree populated with scores per accounts.

        `force_score` makes sure that we compute an aggregated score when
        a question was added after the sample was frozen.
        """
        #pylint:disable=too-many-locals,too-many-statements
        self._start_time()
        self._report_queries("at rollup_scores entry point")
        rollup_tree = None
        rollups = self._cut_tree(self.build_content_tree(
            roots, prefix=root_prefix, cut=TransparentCut()),
            cut=TransparentCut())

        # Moves up all industry segments which are under a category
        # (ex: /facilities/janitorial-services).
        # If we donot do that, then assessment score will be incomplete
        # in the dashboard, as the aggregator will wait for other sub-segments
        # in the top level category.
        removes = []
        ups = OrderedDict({})
        for root_path, root in six.iteritems(rollups):
            if not 'pagebreak' in root[0].get('tag', ""):
                removes += [root_path]
                ups.update(root[1])
        for root_path in removes:
            del rollups[root_path]
        rollups.update(ups)

        rollup_tree = (OrderedDict({}), rollups)
        if 'title' not in rollup_tree[0]:
            rollup_tree[0].update({
                'slug': "totals",
                'title': "Total Score",
                'tag': [settings.TAG_SCORECARD]})
        self._report_queries("rollup_tree generated")

        leafs = self.get_leafs(rollup_tree=rollup_tree)
        self._report_queries("leafs loaded")

        # `population` is the most recent (not-frozen) assessment
        # indexed by account.
        population = list(Consumption.objects.get_active_by_accounts(
            self.campaign, excludes=self._get_filter_out_testing()))

        # All latest samples per account
        includes = list(Consumption.objects.get_latest_samples_by_accounts(
            before=self.ends_at))

        for prefix, values_tuple in six.iteritems(leafs):
            metric_id = self.default_metric_id

            # 1. Populate scores
            self.populate_leaf(values_tuple[0],
                # `DashboardMixin` overrides _get_scored_answers to get
                # the frozen scores. `population`, `metric_id`, `includes`
                # and `questions` are not used in
                # DashboardMixin._get_scored_answers
                # calls get_frozen_scored_answers in dashboard which uses
                # metric_id=2
                self._get_scored_answers(population, metric_id,
                    includes=includes, prefix=prefix), force_score=force_score)

            # 2. Populate N/A answers
            self.populate_leaf(values_tuple[0],
                self._get_na_answers(population, metric_id,
                    includes=includes, prefix=prefix),
                    populate_account=populate_account_na_answers)

            # 3. Populate planned improvements
            self.populate_leaf(values_tuple[0],
                self._get_planned_improvements(population, metric_id,
                    includes=includes, prefix=prefix),
                    populate_account=populate_account_planned_improvements)

        self._report_queries("leafs populated")

        populate_rollup(rollup_tree, True, force_score=force_score)

        # All latest per-segment samples per account. Some segment do not
        # result in a score, and some assessment might not be complete yet.
        # In both cases, `populate_rollup` will not had a chance to insert
        # these samples.
        includes_per_ids = {sample.pk: sample for sample in includes}
        for path, node in six.iteritems(rollup_tree[1]):
            for record in Consumption.objects.filter(
                    path__startswith=path,
                    answer__sample__in=includes).values(
                    'answer__sample_id').annotate(
                    last_activity_at=Max('answer__created_at')):
                sample_id = record['answer__sample_id']
                last_activity_at = record['last_activity_at']
                sample = includes_per_ids[sample_id]
                if 'accounts' not in node[0]:
                    node[0]['accounts'] = {}
                scores = node[0]['accounts']
                if sample.account_id not in scores:
                    scores[sample.account_id] = {}
                score = scores[sample.account_id]
                if 'created_at' not in score:
                    # If we already have an aggregated result, we keep it.
                    score.update({
                        'sample': str(sample),
                        'created_at': max(last_activity_at, sample.created_at)
                    })
        self._report_queries("rollup_tree populated")

        # Adds if the supplier is reporting publicly or not.
        if self.requested_accounts_pk:
            # at least one public report.
            latest_assessments = \
                Consumption.objects.get_latest_samples_by_prefix(
                    before=self.ends_at, prefix="/")

            reporting_publicly = True
            reporting_fines = True
            reporting_data = False
            reporting_targets = False
            reporting_employee_count = False
            reporting_revenue_generated = False

            if reporting_publicly:
                reporting_publicly_sql = """
        WITH samples AS (
        %(latest_assessments)s
        )
        SELECT DISTINCT samples.account_id
        FROM survey_answer
        INNER JOIN survey_question
          ON survey_answer.question_id = survey_question.id
        INNER JOIN samples
          ON survey_answer.sample_id = samples.id
        WHERE samples.account_id IN %(accounts)s AND
          survey_answer.measured = %(yes)s AND
          (survey_question.path LIKE '%%report-extern%%' OR
           survey_question.path LIKE '%%publicly-reported%%')
        """ % {
            'latest_assessments': latest_assessments,
            'yes': Consumption.YES,
            'accounts': self.requested_accounts_pk_as_sql
        }
                _show_query_and_result(reporting_publicly_sql)
                with connection.cursor() as cursor:
                    cursor.execute(reporting_publicly_sql, params=None)
                    reporting_publicly = [row[0] for row in cursor]

                # XXX We add `reporting_publicly` no matter whichever segment
                # the boolean comes from.
                for segment in six.itervalues(rollup_tree[1]):
                    for account_pk, account in six.iteritems(
                            segment[0].get('accounts')):
                        if int(account_pk) in reporting_publicly:
                            account.update({'reporting_publicly': True})
                self._report_queries("reporting publicly completed")

            if reporting_fines:
                reporting_fines_sql = """
        WITH samples AS (
        %(latest_assessments)s
        )
        SELECT DISTINCT samples.account_id
        FROM survey_answer
        INNER JOIN survey_question
          ON survey_answer.question_id = survey_question.id
        INNER JOIN samples
          ON survey_answer.sample_id = samples.id
        WHERE samples.account_id IN %(accounts)s AND
          survey_answer.measured = %(yes)s AND
          (survey_question.path LIKE '%%/environmental-fines')
        """ % {
            'latest_assessments': latest_assessments,
            'yes': "(SELECT id FROM survey_choice"\
" WHERE unit_id=(SELECT id FROM survey_unit WHERE slug='yes-no')"\
" AND text = 'Yes')",
            'accounts': self.requested_accounts_pk_as_sql
        }
                _show_query_and_result(reporting_fines_sql)
                with connection.cursor() as cursor:
                    cursor.execute(reporting_fines_sql, params=None)
                    reporting_fines = [row[0] for row in cursor]

                # XXX We add `reporting_fines` no matter whichever segment
                # the boolean comes from.
                for segment in six.itervalues(rollup_tree[1]):
                    for account_pk, account in six.iteritems(
                            segment[0].get('accounts')):
                        if int(account_pk) in reporting_fines:
                            account.update({'reporting_fines': True})
                self._report_queries("reporting fines completed")

            if reporting_data:
                reporting_data_sql = """
        WITH samples AS (
        %(latest_assessments)s
        )
        SELECT samples.account_id,
          survey_answer.measured,
          survey_answer.unit_id,
          survey_metric.slug,
          survey_question.path
        FROM survey_answer
        INNER JOIN survey_question
          ON survey_answer.question_id = survey_question.id
        INNER JOIN samples
          ON survey_answer.sample_id = samples.id
        INNER JOIN survey_metric
          ON survey_answer.metric_id = survey_metric.id
        WHERE samples.account_id IN %(accounts)s AND
          (survey_metric.slug = 'energy-consumed' OR
           survey_metric.slug = 'ghg-emissions-generated' OR
           survey_metric.slug = 'water-consumed' OR
           survey_metric.slug = 'waste-generated') AND
          (survey_question.path LIKE '%%/energy-consumed' OR
           survey_question.path LIKE '%%/ghg-emissions-total-scope-%%-emissions' OR
           survey_question.path LIKE '%%/ghg-emissions-breakdown-of-scope-3-emissions%%' OR
           survey_question.path LIKE '%%/water-total-water-discharged' OR
           survey_question.path LIKE '%%/water-total-water-recycled-and-reused' OR
           survey_question.path LIKE '%%/water-total-water-withdrawn' OR
           survey_question.path LIKE '%%/waste-total-hazardous-waste' OR
           survey_question.path LIKE '%%/waste-total-non-hazardous-waste' OR
           survey_question.path LIKE '%%/waste-total-waste-recycled')
        """ % {
            'latest_assessments': latest_assessments,
            'yes': Consumption.YES,
            'accounts': self.requested_accounts_pk_as_sql
        }
                _show_query_and_result(reporting_data_sql)
                reported = {}
                with connection.cursor() as cursor:
                    cursor.execute(reporting_data_sql, params=None)
                    for row in cursor:
                        account_pk = int(row[0])
                        measured = row[1]
                        unit_id = row[2]
                        metric = row[3]
                        question = row[4]
                        if account_pk not in reported:
                            reported[account_pk] = {}
                        if question.endswith('/energy-consumed'):
                            question = 'Energy'
                        elif re.match(r'/ghg-emissions-', question):
                            question = 'GHG Emissions'
                        elif re.match(r'/water-', question):
                            question = 'Water'
                        elif re.match(r'/waste-', question):
                            question = 'Waste'
                        if not question in reported[account_pk]:
                            reported[account_pk][question] = {}
                        if unit_id:
                            measured = as_measured_value(
                                None, Unit.objects.get(pk=unit_id),
                                measured=measured)
                        reported[account_pk][question][metric] = measured

                # XXX We add `employee_count` no matter whichever segment
                # the metric comes from.
                for segment in six.itervalues(rollup_tree[1]):
                    for account_pk, account in six.iteritems(
                            segment[0].get('accounts')):
                        account_pk = int(account_pk)
                        if account_pk in reported:
                            texts = []
                            for question, values in six.iteritems(
                                    reported[account_pk]):
                                planned = "%s" % str(question)
                                texts += [planned]
                            account.update({'reported': texts})
                self._report_queries("reporting Energy, GHG, Water"\
                    " and Waste measurements completed")

            if reporting_targets:
                reporting_targets_sql = """
        WITH samples AS (
        %(latest_assessments)s
        )
        SELECT samples.account_id,
          survey_answer.measured,
          survey_answer.unit_id,
          survey_metric.slug,
          survey_question.path
        FROM survey_answer
        INNER JOIN survey_question
          ON survey_answer.question_id = survey_question.id
        INNER JOIN samples
          ON survey_answer.sample_id = samples.id
        INNER JOIN survey_metric
          ON survey_answer.metric_id = survey_metric.id
        WHERE samples.account_id IN %(accounts)s AND
          (survey_metric.slug = 'target-reduced' OR
           survey_metric.slug = 'target-by' OR
           survey_metric.slug = 'target-baseline') AND
          (survey_question.path LIKE '%%/energy-target' OR
           survey_question.path LIKE '%%/ghg-emissions-scope-1-emissions-target' OR
           survey_question.path LIKE '%%/water-withdrawn-target' OR
           survey_question.path LIKE '%%/hazardous-waste-target')
        """ % {
            'latest_assessments': latest_assessments,
            'yes': Consumption.YES,
            'accounts': self.requested_accounts_pk_as_sql
        }
                _show_query_and_result(reporting_targets_sql)
                targets = {}
                with connection.cursor() as cursor:
                    cursor.execute(reporting_targets_sql, params=None)
                    for row in cursor:
                        account_pk = int(row[0])
                        measured = row[1]
                        unit_id = row[2]
                        metric = row[3]
                        question = row[4]
                        if account_pk not in targets:
                            targets[account_pk] = {}
                        if question.endswith('/energy-target'):
                            question = 'Energy'
                        elif question.endswith(
                                '/ghg-emissions-scope-1-emissions-target'):
                            question = 'GHG Emissions'
                        elif question.endswith('/water-withdrawn-target'):
                            question = 'Water'
                        elif question.endswith('/hazardous-waste-target'):
                            question = 'Waste'
                        if not question in targets[account_pk]:
                            targets[account_pk][question] = {}
                        if unit_id:
                            measured = as_measured_value(
                                None, Unit.objects.get(pk=unit_id),
                                measured=measured)
                        targets[account_pk][question][metric] = measured

                # XXX We add `employee_count` no matter whichever segment
                # the metric comes from.
                for segment in six.itervalues(rollup_tree[1]):
                    for account_pk, account in six.iteritems(
                            segment[0].get('accounts')):
                        account_pk = int(account_pk)
                        if account_pk in targets:
                            texts = []
                            for question, values in six.iteritems(
                                    targets[account_pk]):
                                planned = "%s: %s by %s on baseline of %s" % (
                                    question, targets[account_pk][question].get(
                                        'target-reduced'),
                                    targets[account_pk][question].get(
                                        'target-by'),
                                    targets[account_pk][question].get(
                                        'target-baseline'))
                                texts += [planned]
                            account.update({'targets': texts})
                self._report_queries("reporting Energy, GHG, Water"\
                    " and Waste targets completed")

            if reporting_employee_count:
                employee_count_sql = """
            WITH samples AS (
            %(latest_assessments)s
            )
            SELECT DISTINCT samples.account_id, survey_answer.measured
            FROM survey_answer
            INNER JOIN samples
              ON survey_answer.sample_id = samples.id
            WHERE samples.account_id IN %(accounts)s AND
              survey_answer.metric_id = (
                  SELECT id FROM survey_metric WHERE slug='%(metric)s');
            """ % {
                'latest_assessments': latest_assessments,
                'metric': 'employee-counted',
                'accounts': self.requested_accounts_pk_as_sql
            }
                _show_query_and_result(employee_count_sql)
                with connection.cursor() as cursor:
                    cursor.execute(employee_count_sql, params=None)
                    employee_counts = dict(cursor)

                # XXX We add `employee_count` no matter whichever segment
                # the metric comes from.
                for segment in six.itervalues(rollup_tree[1]):
                    for account_pk, account in six.iteritems(
                            segment[0].get('accounts')):
                        if int(account_pk) in employee_counts:
                            account.update({
                                'employee_count':
                                    employee_counts[int(account_pk)]
                            })
                self._report_queries("reporting employee count completed")

            if reporting_revenue_generated:
                revenue_generated_sql = """
            WITH samples AS (
            %(latest_assessments)s
            )
            SELECT DISTINCT samples.account_id,
              survey_answer.measured,
              survey_answer.unit_id, survey_unit.system
            FROM survey_answer
            INNER JOIN samples
              ON survey_answer.sample_id = samples.id
            INNER JOIN survey_unit
              ON survey_answer.unit_id = survey_unit.id
            WHERE samples.account_id IN %(accounts)s AND
              survey_answer.metric_id = (
                  SELECT id FROM survey_metric WHERE slug='%(metric)s');
            """ % {
                'latest_assessments': latest_assessments,
                'metric': 'revenue-generated',
                'accounts': self.requested_accounts_pk_as_sql
            }
                _show_query_and_result(revenue_generated_sql)
                revenue_generateds = {}
                with connection.cursor() as cursor:
                    cursor.execute(revenue_generated_sql, params=None)
                    for row in cursor:
                        account_id = int(row[0])
                        measured = row[1]
                        unit_id = row[2]
                        unit_system = row[3]
                        if unit_system not in Unit.NUMERICAL_SYSTEMS:
                            try:
                                choice = Choice.objects.get(
                                    id=measured, unit_id=unit_id)
                                measured = choice.text
                            except Choice.DoesNotExist:
                                pass
                        revenue_generateds[account_id] = measured

                # XXX We add `revenue_generated` no matter whichever segment
                # the metric comes from.
                for segment in six.itervalues(rollup_tree[1]):
                    for account_pk, account in six.iteritems(
                            segment[0].get('accounts')):
                        if int(account_pk) in revenue_generateds:
                            account.update({
                              'revenue_generated':
                                revenue_generateds[int(account_pk)]
                            })
                self._report_queries("reporting revenue completed")

        return rollup_tree


    def get_rollup_at_path_prefix(self, root_prefix, rollup_tree=None):
        """
        Traverse the `rollup_tree` to find and return the node
        matching `root_prefix`.
        """
        if rollup_tree is None:
            rollup_tree = self.rollup_scores()
        if root_prefix in rollup_tree[1]:
            return rollup_tree[1][root_prefix]
        parts = root_prefix.split('/')
        while parts:
            parts.pop()
            from_root = '/'.join(parts)
            if from_root in rollup_tree[1]:
                return self.get_rollup_at_path_prefix(
                    root_prefix, rollup_tree[1][from_root])
        raise KeyError(root_prefix)


class ScorecardQuerySetMixin(BenchmarkMixin):
    """
    Queryset used to create a scorecard
    """
    def get_queryset(self):
        #pylint:disable=too-many-locals
        from_root, trail = self.breadcrumbs
        roots = [trail[-1][0]] if trail else None
        rollup_tree = self.rollup_scores(roots, from_root)
        # XXX `nb_questions` will not be computed correctly if some sections
        #     have not been answered, and as a result `populate_leaf` wasn't
        #     called for that particular section.

        self.create_distributions(rollup_tree,
            view_account=(self.assessment_sample.account.pk
                if self.assessment_sample else None))
        self.decorate_with_breadcrumbs(rollup_tree)
        charts, complete = self.flatten_distributions(rollup_tree,
            prefix=from_root)

        # Done in BenchmarkView through `_build_tree` > `decorate_leafs`.
        # This code is here otherwise the printable scorecard doesn't show
        # icons.
        for chart in charts:
            text = PageElement.objects.filter(
                slug=chart['slug']).values('text').first()
            if text and text['text']:
                chart.update({'icon': text['text']})

        total_score = None
        parts = from_root.split('/')
        if parts:
            slug = parts[-1]
        # When we remove the following 4 lines ...
            for chart in charts:
                if chart['slug'] == slug:
                    total_score = chart.copy()
                    break
        if not total_score:
            total_score = rollup_tree[0]
        if not total_score:
            total_score = OrderedDict({"nb_respondents": "-"})
        total_score.update({"slug": "totals", "title": "Total Score"})
        # ... and the following 2 lines together, pylint does not blow up...
        if not complete and 'normalized_score' in total_score:
            del total_score['normalized_score']
        charts += [total_score]
        return charts


class BenchmarkAPIView(ScorecardQuerySetMixin, generics.GenericAPIView):
    """
    Retrieves a scorecard

    Returns list of *organization*'s scores for all relevant section
    of the best practices based on *path*.

    **Tags**: benchmark

    **Examples

    .. code-block:: http

        GET /api/supplier-1/benchmark/boxes-and-enclosures/energy-efficiency/\
 HTTP/1.1

    responds

    .. code-block:: json

        [{
            "slug":"totals",
            "title":"Total Score",
            "nb_answers": 4,
            "nb_questions": 4,
            "nb_respondents": 2,
            "numerator": 12.0,
            "improvement_numerator": 8.0,
            "denominator": 26.0,
            "normalized_score": 46,
            "improvement_score": 30,
            "score_weight": 1.0,
            "highest_normalized_score": 88,
            "avg_normalized_score": 67,
            "created_at":"2017-08-02T20:18:19.089",
            "distribution": {
                "y": [0, 1, 0, 1],
                "x": ["0-25%", "25-50%", "50-75%", "75-100%"],
                "organization_rate":"25-50%"
            }
         },
         {
            "slug":"energy-efficiency-management-basics",
            "title":"Management",
            "text":"/media/envconnect/management-basics.png",
            "tag":"management",
            "score_weight":1.0
         },
         {
            "slug":"process-heating",
            "title":"Process heating",
            "text":"/media/envconnect/process-heating.png",
            "nb_questions": 4,
            "nb_answers": 4,
            "nb_respondents": 2,
            "numerator": 12.0,
            "improvement_numerator": 8.0,
            "denominator": 26.0,
            "normalized_score": 46,
            "improvement_score": 12,
            "highest_normalized_score": 88,
            "avg_normalized_score": 67,
            "created_at": "2017-08-02T20:18:19.089",
            "distribution": {
                "y": [0, 1, 0, 1],
                "x": [ "0-25%", "25-50%", "50-75%", "75-100%"],
                "organization_rate": "25-50%"
            },
            "score_weight": 1.0
         }]
    """
    http_method_names = ['get']
    serializer_class = BenchmarkSerializer

    def get(self, request, *args, **kwargs): #pylint:disable=unused-argument
        return HttpResponse(self.get_queryset())


class EnableScorecardAPIView(ToggleTagContentAPIView):
    """
    Enable scorecard

    XXX same description/behavior as /api/content/score but writing
    to a bolean value. returns tags.

    **Tags**: benchmark

    **Examples**

    .. code-block:: http

         PUT /api/content/scorecard/enable/water-use/ HTTP/1.1

    responds

    .. code-block:: json

        {
            "tags": "scorecard"
        }
    """
    added_tag = 'scorecard'


class DisableScorecardAPIView(ToggleTagContentAPIView):
    """
    Disable scorecard

    **Tags**: benchmark

    **Examples**

    .. code-block:: http

         PUT /api/content/scorecard/disable/water-use/  HTTP/1.1

    responds

    .. code-block:: json

        {
            "tags": "scorecard"
        }
    """
    removed_tag = 'scorecard'


class ScoreWeightAPIView(TrailMixin, generics.RetrieveUpdateAPIView):
    """
    Retrieve score

    XXX score weight is embed in the PageElement tag. Do we really care
    about the path or just the PageElement.slug? Since we do not have
    aliasing at the node level (only leaf best practices), that seems
    `path` is only used for API consistency.

    **Tags**: benchmark

    **Examples**

    .. code-block:: http

         GET /api/content/editables/score/water-use/ HTTP/1.1

    responds

    .. code-block:: json

        {
            "weight": 2.0
        }
    """
    lookup_field = 'path'
    serializer_class = ScoreWeightSerializer

    def retrieve(self, request, *args, **kwargs):
        trail = self.get_full_element_path(self.path)
        return HttpResponse(self.serializer_class().to_representation({
            'weight': get_score_weight(trail[-1].tag)}))

    def update(self, request, *args, **kwargs):#pylint:disable=unused-argument
        partial = kwargs.pop('partial', False)
        serializer = self.serializer_class(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return HttpResponse(serializer.data)

    def perform_update(self, serializer):
        trail = self.get_full_element_path(self.path)
        element = trail[-1]
        extra = {}
        try:
            extra = json.loads(element.tag)
        except (TypeError, ValueError):
            pass
        extra.update(serializer.validated_data)
        element.tag = json.dumps(extra, cls=JSONEncoder)
        element.save()


def _populate_account_historical(accounts, agg_score,
                         agg_key='account_id', force_score=False):
    populate_account(
        accounts, agg_score, agg_key=agg_key, force_score=force_score)
    created_at = agg_score.last_activity_at
    if created_at:
        if isinstance(created_at, six.string_types):
            created_at = parse_datetime(created_at)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=utc)
    account_id = (created_at if agg_key == 'last_activity_at'
        else getattr(agg_score, agg_key))
    accounts[account_id].update({'sample': agg_score.sample_id})


# XXX ReportMixin because we use populate_leaf
class HistoricalScoreAPIView(ReportMixin, generics.GenericAPIView):
    """
    Retrieves historical scorecards

    Returns list of historical *organization*'s scores for all top level
    icons based on *path*. The output format is compatible
    with `HistoricalScoreChart` (see draw-chart.js).

    **Tags**: benchmark

    **Examples

    .. code-block:: http

        GET /api/supplier-1/benchmark/historical/metal/boxes-and-enclosures\
 HTTP/1.1

    responds

    .. code-block:: json

        {
            "latest": {
                "assessment": "abc123",
                "segments": [
                    [
                     "/construction/",
                     "Construction"
                    ]
                ]
            },
            "results": [
            {
                "key": "May 2018",
                "created_at": "2018-05-28T17:39:59.368272Z",
                "values": [
                    ["Construction", 80, "/app/supplier-1/assess/"\
"ce6dc2c4cf6b40dbacef91fa3e934eed/sample/boxes-and-enclosures/"]
                ]
            },
            {
                "key": "Dec 2017",
                "created_at": "2017-12-28T17:39:59.368272Z",
                "values": [
                    ["Construction", 80, "/app/supplier-1/assess/"\
"ce6dc2c4cf6b40dbacef91fa3e934eed/sample/boxes-and-enclosures/"]
                ]
            }
            ]
        }
    """
    serializer_class = MetricsSerializer
    force_score = True

    # HistoricalScoreAPIView.flatten_distributions
    def flatten_distributions(self, rollup_tree, accounts, prefix=None):
        """
        A rollup_tree is keyed best practices and we need a structure
        keyed on historical samples here.
        """
        if prefix is None:
            prefix = "/"
        if not prefix.startswith("/"):
            prefix = '/%s' % prefix

        is_pagebreak = ContentCut.TAG_PAGEBREAK in rollup_tree[0].get('tag', "")
        if not is_pagebreak:
            for path, node in six.iteritems(rollup_tree[1]):
                self.flatten_distributions(node, accounts, prefix=prefix)
            return

        node_path = rollup_tree[0].get('path', '')
        node_key = rollup_tree[0].get('title', node_path)
        for account_key, account in six.iteritems(rollup_tree[0].get(
                'accounts', OrderedDict({}))):
            if account_key not in accounts:
                accounts[account_key] = OrderedDict({})
            by_industry = {
                'normalized_score': account.get('normalized_score', 0)
            }
            if 'sample' in account:
                # XXX builds URL to segments.
                last_part = node_path.split('/')[-1]
                by_industry.update({
                    'url': self.request.build_absolute_uri(
                        reverse('assess_organization',
                            args=(self.account.slug, account['sample'],
                                  '/%s' % last_part)))
                })
            accounts[account_key].update({node_key: by_industry})

    def get(self, request, *args, **kwargs):
        #pylint:disable=unused-argument,too-many-locals
        self._start_time()
        from_root, trail = self.breadcrumbs
        roots = [trail[-1][0]] if trail else None
        # At this point rollups is a dictionary
        #     {prefix: (node(Dict), children(Dict))}
        # and we want to a rooted tree (node(Dict), children(Dict)).
        by_created_at = OrderedDict({})
        includes = Sample.objects.filter(
            account=self.account, extra__isnull=True, is_frozen=True)
        if includes:
            self._report_queries("at rollup_scores entry point")
            rollups = self._cut_tree(self.build_content_tree(
                roots, prefix=from_root, cut=TransparentCut()),
                cut=TransparentCut())
            for rollup_tree in six.itervalues(rollups):
                self._report_queries("rollup_tree generated")
                leafs = self.get_leafs(rollup_tree=rollup_tree)
                self._report_queries("leafs loaded")
                for prefix, values_tuple in six.iteritems(leafs):
                    self.populate_leaf(values_tuple[0],
                        get_historical_scores(
                            includes=includes,
                            prefix=prefix),
                        populate_account=_populate_account_historical,
                        agg_key='last_activity_at',
                        force_score=self.force_score)
                                          # Relies on `get_historical_scores()`
                                          # to use `Sample.created_at`
                self._report_queries("leafs populated")

                populate_rollup(rollup_tree, True, force_score=self.force_score)
                self._report_queries("rollup_tree populated")

                # We populated the historical scores per section.
                # Now we need to transpose them by sample_id.
                accounts = OrderedDict({})
                self.flatten_distributions(
                    rollup_tree, accounts, prefix=from_root)
                for account_key in accounts:
                    account = accounts[account_key]
                    values = []
                    for segment_title, scores in six.iteritems(account):
                        if account_key not in by_created_at:
                            by_created_at[account_key] = []
                        by_created_at[account_key] += [(segment_title,
                            scores['normalized_score'], scores['url'])]

        results = []
        for created_at, values in six.iteritems(by_created_at):
            results += [{
                "key": created_at.strftime("%b %Y"),
                "values": values,
                "created_at": created_at
            }]
        results.sort(key=lambda sample: sample['created_at'], reverse=True)
        resp_data = {"results": results}
        if self.assessment_sample:
            active_assessment = get_segments_from_samples(
                [self.assessment_sample.id])[self.assessment_sample.id]
            segments = [segment[0] for segment in active_assessment]
            updates = []
            for segment in segments:
                updates += [{
                    "slug": str(self.assessment_sample),
                    "account": str(self.account),
                    "created_at": self.assessment_sample.created_at,
                    "campaign": {
                        "slug": str(self.assessment_sample.campaign),
                        "title": segment['title'],
                        "path": segment['path']
                    },
                    "is_frozen": self.assessment_sample.is_frozen
                }]
            resp_data.update({"updates": updates})
        return HttpResponse(resp_data)


class PracticeBenchmarkAPIView(PracticeBenchmarkMixin, generics.ListAPIView):
    """
    Lists of practices with implementation rate and opportunity score.

    **Tags**: survey

    **Examples

    .. code-block:: http

        GET /api/supplier-1/benchmark/f1e2e916eb494b90f9ff0a36982342/\
details/boxes-and-enclosures HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 3,
          "next": null,
          "previous": null,
          "results": [
            {
              "path": null,
              "title": "Boxes & enclosures",
              "indent": 0
            },
            {
              "path": null,
              "title": "Governance & management",
              "indent": 1
            },
            {
              "path": "/metal/boxes-and-enclosures/governance-management/"\
"assessment/the-assessment-process-is-rigorous",
              "title": "The assessment process is rigorous and thorough*",
              "indent": 2,
              "nb_respondents": 15,
              "rate": 50,
              "opportunity": 4.5
            }
          ]
        }
    """
    serializer_class = PracticeBenchmarkSerializer

    def get_queryset(self):
        """
        Returns a list of heading and best practices
        """
        search_query = self.request.query_params.get('q')
        query_filter = Q(tag__contains='industry')
        if search_query:
            query_filter = query_filter & Q(tag__contains=search_query)
        trail = self.get_full_element_path(self.path)
        full_path = '/%s' % '/'.join([element.slug for element in trail])
        if trail:
            prefix = '/%s' % '/'.join([element.slug for element in trail[:-1]])
            roots = [trail[-1]]
        else:
            prefix = ''
            roots = PageElement.objects.get_roots().filter(
                query_filter).order_by('title')

        menus = []
        cut = ContentCut(depth=2)

#        rollup_trees
        for root in roots:
            if not prefix and not cut.enter(root.tag):
                menus += [{
                    'title': root.title,
                    'path': '%s/%s' % (prefix, root.slug),
                    'indent': 0
                }]
            else:
                rollup_tree = self._build_tree(root, full_path, cut=cut)
                menus += self.flatten({prefix: rollup_tree})
        return menus

    def flatten(self, rollup_trees, depth=0):
        results = []
        for _, values in six.iteritems(rollup_trees):
            elem, nodes = values
            content = {
                'title': elem['title'],
                'path': None if nodes else elem['path'],
                'indent': depth
            }
            if 'consumption' in elem and elem['consumption']:
                content.update({
                    'nb_respondents':
                        elem['consumption'].get('nb_respondents', 0),
                    'rate':
                        elem['consumption'].get('rate', 0),
                    'opportunity':
                        elem['consumption'].get('opportunity', 0),
                })
            results += [content]
            results += self.flatten(nodes, depth=depth + 1)
        return results
