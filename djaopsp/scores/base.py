# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

import datetime, logging

from django.conf import settings
from survey.models import Answer, Sample, Unit
from survey.queries import datetime_or_now

from ..compat import import_string, six


LOGGER = logging.getLogger(__name__)

SCORE_UNIT = 'points'


class ScoreCalculator(object):
    """
    Abstract base class to compute scores on individual answers
    for an assessment
    """
    intrinsic_value_headers = []

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
        #pylint:disable=unused-argument
        return []

    def get_scorecards(self, campaign, prefix, title=None, includes=None,
                       bypass_cache=False):
        #pylint:disable=unused-argument,too-many-arguments
        return []


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
    LOGGER.info("freeze %s scores for segment %s based of sample %s:"\
        " frozen as %s", sample.account, segment_path, sample.slug,
        score_sample)
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
        for decorated_answer in calculator.get_scored_answers(
                sample.campaign, includes=[sample], prefix=segment_path,
                excludes=excludes):
            if (decorated_answer.answer_id and
                decorated_answer.is_planned == sample.extra):
                numerator = decorated_answer.numerator
                denominator = decorated_answer.denominator
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
                    "transparent_to_rollover": false,
                    "text": "/envconnect/static/img/production.png"
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
