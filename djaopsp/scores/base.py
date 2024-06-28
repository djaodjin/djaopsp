# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

import datetime, logging

from django.conf import settings
from django.db.models import F
from survey.helpers import datetime_or_now
from survey.models import Answer, Choice, Sample, Unit

from ..compat import import_string, six
from ..models import ScorecardCache
from ..utils import get_score_weight


LOGGER = logging.getLogger(__name__)

SCORE_UNIT = 'points'


class ScoreCalculator(object):
    """
    Abstract base class to compute scores on individual answers
    for an assessment
    """
    intrinsic_value_headers = []

    def __init__(self):
        self.points_unit_id = Unit.objects.get(slug=SCORE_UNIT).pk
        self.yes_no_unit_id = Unit.objects.get(slug='yes-no').pk
        self.yes = Choice.objects.get(
            unit_id=self.yes_no_unit_id, text='Yes').pk

    def get_opportunity(self, campaign,
                        includes=None, excludes=None, prefix=None,
                        last_frozen_assessments=None):
        """
        Lists opportunity (intrisic and peers-based)

        *includes* is a list of `Sample`.

        *prefix* restricts computation to `Question` whose path starts
        with *prefix* and *excludes* is a set of `Account` that shouldn't
        be included in the peers-based opportunity.

        *last_frozen_assessments* is a pre-cached population of peers
        to use for peers-based opportunity.
        """
        #pylint:disable=too-many-arguments,unused-argument
        return []


    def get_scored_answers(self, campaign,
                           includes=None, excludes=None, prefix=None):
        """
        Retuns answers with score computed based on opportunity.
        """
        results = []
        queryset = Answer.objects.filter(
            unit_id=F('question__default_unit_id'),
            sample__in=includes,
            question__default_unit_id=self.yes_no_unit_id,
            question__path__startswith=prefix,
            measured=self.yes
        ).distinct().select_related('question')
        for answer in queryset:
            answer.measured = get_score_weight(
                campaign, answer.question.path, default_value=0)

            answer.numerator = answer.measured  # XXX for freeze_scores
            answer.unit_id = self.points_unit_id
            answer.answer_id = answer.pk # XXX for freeze_scores
            answer.is_planned = includes[0].extra # XXX for freeze_scores
            answer.id = answer.question_id # XXX for freeze_scores
            results += [answer]

        return results


    def get_scorecards(self, campaign, prefix, title=None, includes=None,
                       bypass_cache=False):
        """
        Returns an aggregate of answers' scores and relevant metrics
        to be cached.
        """
        #pylint:disable=too-many-arguments
        active_samples = []
        frozen_samples = []
        if bypass_cache:
            active_samples = includes
        else:
            for sample in includes:
                if sample.is_frozen:
                    frozen_samples += [sample]
                else:
                    active_samples += [sample]
        scorecard_caches = []
        for sample in frozen_samples:
            scorecard_caches += ScorecardCache.objects.filter(
                sample=sample, path__startswith=prefix)
            for scored_answer in self.get_scored_answers(campaign,
                includes=[sample], prefix=prefix):
                # created_at, measured, denominator, path
                LOGGER.debug("%s,%s,%s,%s", scored_answer.created_at.date(),
                    scored_answer.measured, scored_answer.denominator,
                    scored_answer.question.path)

        if active_samples:
            for sample in active_samples:
                scorecard_cache = ScorecardCache(
                    sample_id=sample.id, # XXX for freeze_scores
                    path=prefix, sample=sample, normalized_score=0)
                scorecard_cache.numerator = 0
                scorecard_cache.nb_answers = 0
                scorecard_cache.nb_questions = 0
                scorecard_cache.denominator = 100
                for scored_answer in self.get_scored_answers(campaign,
                                        includes=includes, prefix=prefix):
                    if scored_answer.denominator:
                        scorecard_cache.normalized_score += scored_answer.measured
                        scorecard_cache.numerator += scored_answer.measured
                        scorecard_cache.nb_answers = scorecard_cache.nb_answers + 1
                        scorecard_cache.nb_questions = scorecard_cache.nb_questions + 1
                # XXX for freeze_scores
                scorecard_cache.normalized_score = round(
                    scorecard_cache.normalized_score)
                scorecard_cache.account_id = includes[0].account_id
                scorecard_cache.slug = includes[0].slug
                scorecard_cache.created_at = includes[0].created_at
                scorecard_cache.campaign_id = includes[0].campaign_id
                scorecard_cache.updated_at = includes[0].updated_at
                scorecard_cache.is_frozen  = includes[0].is_frozen
                scorecard_cache.extra  = includes[0].extra
                scorecard_cache.segment_path = prefix
                scorecard_cache.segment_title = title
                scorecard_cache.nb_na_answers = 0
                scorecard_cache.reporting_publicly = False
                scorecard_cache.reporting_fines = False
                scorecard_cache.reporting_energy_consumption = False
                scorecard_cache.reporting_ghg_generated = False
                scorecard_cache.reporting_water_consumption = False
                scorecard_cache.reporting_waste_generated = False
                scorecard_cache.reporting_energy_target = False
                scorecard_cache.reporting_ghg_target = False
                scorecard_cache.reporting_water_target = False
                scorecard_cache.reporting_waste_target = False

                scorecard_caches += [scorecard_cache]

        return scorecard_caches


def freeze_scores(sample, excludes=None, collected_by=None, created_at=None,
                  segment_path=None, score_sample=None):
    """
    This function creates a copy of all, or a subset if *segment_path* is
    present, the user-inputted answers in *sample* and derives a score
    for each of them.

    The date at which the frozen sample is created and the user executing
    the freeze can be optionnaly specified by *created_at* and *collected_by*
    respectively.
    """
    #pylint:disable=too-many-arguments,disable=too-many-locals
    # This function must be executed in a `transaction.atomic` block.
    # XXX check sample is not already frozen???
    at_time = created_at
    created_at = datetime_or_now(created_at)
    if not segment_path:
        segment_path = '/'
    # creates a new frozen sample
    if not score_sample:
        score_sample = Sample.objects.create(
            created_at=created_at,
            updated_at=created_at,
            campaign=sample.campaign,
            account=sample.account,
            extra=sample.extra,
            is_frozen=True)
    LOGGER.info("freeze %s scores for segment %s based of sample %s"\
        " (extra=%s): frozen as %s", sample.account, segment_path, sample.slug,
        sample.extra, score_sample)
    # Copy the actual answers inputted by users
    points_unit_id = Unit.objects.get(slug=SCORE_UNIT).pk
    user_answers = []
    for answer in Answer.objects.filter(
            sample=sample,
            question__enumeratedquestions__campaign=sample.campaign,
            question__path__startswith=segment_path).exclude(
                unit_id=points_unit_id):
        answer.pk = None
        answer.created_at = created_at
        answer.sample = score_sample
        user_answers += [answer]
        LOGGER.debug("save(created_at=%s, question_id=%s, unit_id=%s,"\
            " measured=%s, denominator=%s, collected_by=%s,"\
            " sample=%s)",
            answer.created_at, answer.question_id, answer.unit_id,
            answer.measured, answer.denominator, answer.collected_by,
            answer.sample)
    Answer.objects.bulk_create(user_answers)

    # Create frozen scores for answers we can derive a score from
    # (i.e. assessment).
    calculator = get_score_calculator(segment_path)
    if calculator:
        score_answers = []
        calculator_answers = calculator.get_scored_answers(
                sample.campaign, includes=[sample], prefix=segment_path,
                excludes=excludes)
        for decorated_answer in calculator_answers:
            if (decorated_answer.answer_id and
                decorated_answer.is_planned == sample.extra):
                numerator = decorated_answer.numerator
                denominator = decorated_answer.denominator
                if numerator or denominator:
                    LOGGER.debug("create(created_at=%s, question_id=%s,"\
                        " unit_id=%s, measured=%s, denominator=%s,"\
                        " collected_by=%s, sample=%s)",
                        created_at, decorated_answer.id, points_unit_id,
                        numerator, denominator, collected_by, score_sample)
                    score_answers += [Answer(
                        created_at=created_at,
                        question_id=decorated_answer.id,
                        unit_id=points_unit_id,
                        measured=numerator,
                        denominator=denominator,
                        collected_by=collected_by,
                        sample=score_sample)]
        LOGGER.info("write %d scored answers in %s for segment '%s'",
            len(score_answers), score_sample, segment_path)
        Answer.objects.bulk_create(score_answers)

    # Update date of active sample to be later than all frozen ones.
    at_time = datetime_or_now()
    sample.created_at = at_time
    sample.updated_at = at_time
    sample.save()

    return score_sample


def get_score_calculator(segment_path):
    """
    Returns a specific calculator for scores if one exists for
    the `segment_path`, otherwise return a default calculator.
    """
    for root_path, calculator_class in six.iteritems(
            settings.SCORE_CALCULATORS):
        if segment_path.startswith(root_path):
            return import_string(calculator_class)()
    return None


def _normalize(scores, normalize_to_one=False, force_score=False):
    """
    Adds keys ``normalized_score`` and ``improvement_score``
    into the dictionnary *scores* when keys ``nb_answers``
    and ``nb_questions`` are equal and (``numerator``, ``denominator``
    ``improvement_numerator``) are present.

    The ``score_weight`` on a node really represents a percentage the node
    contributes to the parent score. This means we need to normalize the
    node score before using it.
    """
    # XXX while we figure out how to compute `normalize_to_one` correctly
    # in the context of the assessment (Python) vs. scorecard (SQL).
    numerator_key = 'numerator'
    denominator_key = 'denominator'
    nb_answers = scores.get('nb_answers', 0)
    nb_questions = scores.get('nb_questions', 0)
    if force_score or nb_answers == nb_questions:
        # If we don't have the same number of questions
        # and answers, numerator and denominator are meaningless.
        denominator = scores.get(denominator_key, 0)
        if denominator:
            scores['normalized_score'] = int(
                scores[numerator_key] * 100.0 / denominator)
            improvement_numerator = scores.get('improvement_numerator', None)
            if improvement_numerator is not None:
                scores['improvement_score'] = (
                    improvement_numerator * 100.0 / denominator)
            if normalize_to_one:
                if numerator_key in scores:
                    scores[numerator_key] = (
                        float(scores[numerator_key]) / denominator)
                improvement_numerator = scores.get(
                    'improvement_numerator', None)
                if improvement_numerator is not None:
                    scores['improvement_numerator'] = (
                        float(improvement_numerator) / denominator)
                scores[denominator_key] = 1.0
        elif nb_questions != 0:
            scores['normalized_score'] = 0
    else:
        scores.pop(numerator_key, None)
        scores.pop(denominator_key, None)


def populate_rollup(rollup_tree, normalize_to_one, force_score=False):
    """
    Recursively populate the tree *rollup_tree* with aggregated scores
    for assessment.

    A rollup_tree is recursively defined as a tuple of two dictionnaries.
    The first dictionnary stores the fields on the node while the second
    dictionnary contains the leafs keyed by path.

    Example:

        [{
            "slug": "totals",
            "title": "Total Score",
            "tag": ["scorecard"]
         },
         {
            "/boxes-and-enclosures": [{
                "path": "/boxes-and-enclosures",
                "slug": "boxes-and-enclosures",
                "title": "Boxes & enclosures",
                "tag": "{\"tags\":[\"sustainability\"]}",
                "score_weight": 1.0,
                "transparent_to_rollover": false
            },
            {
                "/boxes-and-enclosures/management-basics": [{
                    "path": "/boxes-and-enclosures/management-basics",
                    "slug": "management-basics",
                    "title": "Management",
                    "tag": "{\"tags\":[\"management\",\"scorecard\"]}",
                    "score_weight": 1.0,
                    "transparent_to_rollover": false,
                    "accounts": {
                        "6": {
                            "nb_answers": 0,
                            "nb_questions": 2,
                            "created_at": null
                        },
                        "7": {
                            "nb_answers": 2,
                            "nb_questions": 2,
                            "created_at": "2017-12-20 18:48:40.666239",
                            "numerator": 4.0,
                            "denominator": 10.5,
                            "improvement_numerator": 1.5,
                            "improvement_denominator": 4.5
                        },
                    }
                },
                {}
                ],
                "/boxes-and-enclosures/design": [{
                    "path": "/boxes-and-enclosures/design",
                    "slug": "design",
                    "title": "Design",
                    "tag": "{\"tags\":[\"scorecard\"]}",
                    "score_weight": 1.0,
                    "transparent_to_rollover": false,
                    "accounts": {
                        "6": {
                            "nb_answers": 0,
                            "nb_questions": 2,
                            "created_at": null
                        },
                        "7": {
                            "nb_answers": 0,
                            "nb_questions": 2,
                            "created_at": null,
                            "improvement_numerator": 0.0,
                            "improvement_denominator": 0.0
                        },
                    }
                },
                {}
                ],
                "/boxes-and-enclosures/production": [{
                    "path": "/boxes-and-enclosures/production",
                    "slug": "production",
                    "title": "Production",
                    "tag": "{\"tags\":[\"scorecard\"]}",
                    "score_weight": 1.0,
                    "transparent_to_rollover": false
                },
                {
                    "/boxes-and-enclosures/production/energy-efficiency": [{
              "path": "/boxes-and-enclosures/production/energy-efficiency",
                        "slug": "energy-efficiency",
                        "title": "Energy Efficiency",
                        "tag": "{\"tags\":[\"pagebreak\",\"scorecard\"]}",
                        "score_weight": 1.0,
                        "transparent_to_rollover": false,
                        "accounts": {
                            "6": {
                                "nb_answers": 1,
                                "nb_questions": 4,
                                "created_at": "2016-05-01 00:36:19.448000"
                            },
                            "7": {
                                "nb_answers": 0,
                                "nb_questions": 4,
                                "created_at": null,
                                "improvement_numerator": 0.0,
                                "improvement_denominator": 0.0
                            },
                        }
                    },
                    {}
                    ]
                }
            }]
         }]
    """
    #pylint:disable=too-many-locals
    values = rollup_tree[0]
    slug = values.get('slug', None)
    total_score_weight = 0
    if len(rollup_tree[1]) > 1:
        for node in six.itervalues(rollup_tree[1]):
            score_weight = node[0].get('score_weight', 1.0)
            total_score_weight += score_weight
        normalize_children = (
            (1.0 - 0.01) < total_score_weight < (1.0 + 0.01))
    else:
        # With only one children the weight will always be 1 yet we don't
        # want to normalize here.
        normalize_children = False

    if not 'accounts' in values:
        values['accounts'] = {}
    accounts = values['accounts']
    for node in six.itervalues(rollup_tree[1]):
        populate_rollup(                                       # recursive call
            node, normalize_children, force_score=force_score)
        score_weight = node[0].get('score_weight', 1.0)
        for account_id, scores in six.iteritems(node[0].get('accounts', {})):
            if not account_id in accounts:
                accounts[account_id] = {}
            agg_scores = accounts[account_id]
            if 'sample_id' in scores:
                agg_scores['sample_id'] = scores['sample_id']
            if 'created_at' in scores:
                if not ('created_at' in agg_scores and isinstance(
                        agg_scores['created_at'], datetime.datetime)):
                    agg_scores['created_at'] = scores['created_at']
                elif (isinstance(
                        agg_scores['created_at'], datetime.datetime) and
                      isinstance(scores['created_at'], datetime.datetime)):
                    agg_scores['created_at'] = max(
                        agg_scores['created_at'], scores['created_at'])
            nb_questions = scores.get('nb_questions')
            if nb_questions is not None:
                agg_scores['nb_questions'] = (
                    agg_scores.get('nb_questions', 0) + nb_questions)
            nb_answers = scores.get('nb_answers')
            if slug != 'totals' or nb_answers:
                # Aggregation of total scores is different. We only want to
                # count scores for assessment that matter for an organization's
                # segment.
                for key in ('nb_answers',
                            'nb_na_answers', 'nb_planned_improvements'):
                    value = scores.get(key)
                    if value is not None:
                        agg_scores[key] = agg_scores.get(key, 0) + value
                for key in ['numerator', 'denominator',
                            'improvement_numerator']:
                    value = scores.get(key)
                    if value is not None:
                        agg_scores[key] = agg_scores.get(key, 0) + (
                            value * score_weight)

    for account_id, scores in six.iteritems(accounts):
        _normalize(
            scores, normalize_to_one=normalize_to_one, force_score=force_score)


def populate_scorecard_cache(sample, calculator, segment_path, segment_title):
    LOGGER.info("populate %s scorecard cache for %s based of sample %s",
        sample.account, segment_path, str(sample))
    scorecards = calculator.get_scorecards(
            sample.campaign, segment_path, title=segment_title,
            includes=[sample], bypass_cache=True)
    # XXX fixes highlights that were not set.
    for scorecard in scorecards:
        if scorecard.reporting_publicly is None:
            scorecard.reporting_publicly = False
        if scorecard.reporting_fines is None:
            scorecard.reporting_fines = False
        if scorecard.reporting_environmental_fines is None:
            scorecard.reporting_environmental_fines = False
        if scorecard.reporting_energy_consumption is None:
            scorecard.reporting_energy_consumption = False
        if scorecard.reporting_water_consumption is None:
            scorecard.reporting_water_consumption = False
        if scorecard.reporting_ghg_generated is None:
            scorecard.reporting_ghg_generated = False
        if scorecard.reporting_waste_generated is None:
            scorecard.reporting_waste_generated = False
        if scorecard.reporting_energy_target is None:
            scorecard.reporting_energy_target = False
        if scorecard.reporting_water_target is None:
            scorecard.reporting_water_target = False
        if scorecard.reporting_ghg_target is None:
            scorecard.reporting_ghg_target = False
        if scorecard.reporting_waste_target is None:
            scorecard.reporting_waste_target = False
        if scorecard.nb_planned_improvements is None:
            scorecard.nb_planned_improvements = 0
        if scorecard.nb_na_answers is None:
            scorecard.nb_na_answers = 0
        if scorecard.normalized_score is None:
            scorecard.normalized_score = 0

    ScorecardCache.objects.bulk_create(scorecards)
