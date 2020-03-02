# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

"""
Compute organization assessment and improvement scores.
"""
from __future__ import unicode_literals

import datetime

from django.utils import six
from django.utils.dateparse import parse_datetime
from django.utils.timezone import utc

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


def populate_account(accounts, agg_score,
                     agg_key='account_id', force_score=False):
    """
    Populate the *accounts* dictionnary with scores in *agg_score*.

    *agg_score* is a tuple (account_id, sample_id, is_planned, numerator,
    denominator, last_activity_at, nb_answers, nb_questions)
    """
    sample_id = agg_score.sample_id
    is_completed = agg_score.is_completed # i.e. survey_sample.is_frozen
    is_planned = agg_score.is_planned
    numerator = agg_score.numerator
    denominator = agg_score.denominator
    created_at = agg_score.last_activity_at
    if created_at:
        if isinstance(created_at, six.string_types):
            created_at = parse_datetime(created_at)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=utc)
    if agg_key == 'last_activity_at':
        account_id = created_at
    else:
        account_id = getattr(agg_score, agg_key)
    nb_answers = getattr(agg_score, 'nb_answers', None)
    if nb_answers is None:
        # Putting the following statement in the default clause will lead
        # to an exception since `getattr(agg_score, 'answer_id')` will be
        # evaluated first.
        nb_answers = 0 if getattr(agg_score, 'answer_id') is None else 1
    nb_questions = getattr(agg_score, 'nb_questions', 1)
    if not account_id in accounts:
        accounts[account_id] = {}
    if is_planned:
        accounts[account_id].update({
            'improvement_numerator': numerator,
            'improvement_denominator': denominator,
            'improvement_completed': is_completed,
        })
        if not 'nb_answers' in accounts[account_id]:
            accounts[account_id].update({
                'nb_answers': nb_answers})
        if not 'nb_questions' in accounts[account_id]:
            accounts[account_id].update({
                'nb_questions': nb_questions})
        if not 'created_at' in accounts[account_id]:
            accounts[account_id].update({
                'created_at': created_at})
    else:
        accounts[account_id].update({
            'nb_answers': nb_answers,
            'nb_questions': nb_questions,
            'assessment_completed': is_completed,
            'created_at': created_at,
            'sample': sample_id
        })
        if force_score or nb_answers == nb_questions:
            # We might end-up here with an unanswered question
            # that was added after the sample was frozen.
            accounts[account_id].update({
                'numerator': numerator,
                'denominator': denominator})


def populate_account_na_answers(accounts, agg_score,
                                agg_key='account_id', force_score=False):
    """
    Adds `nb_na_answers` field in `accounts`.
    """
    account_id = getattr(agg_score, 'account_id', None)
    nb_answers = getattr(agg_score, 'nb_answers', None)
    if nb_answers is None:
        # Putting the following statement in the default clause will lead
        # to an exception since `getattr(agg_score, 'answer_id')` will be
        # evaluated first.
        nb_answers = 0 if getattr(agg_score, 'answer_id') is None else 1
    if not account_id in accounts:
        accounts[account_id] = {}
    accounts[account_id].update({
        'nb_na_answers': nb_answers
    })


def populate_account_planned_improvements(accounts, agg_score,
                     agg_key='account_id', force_score=False):
    """
    Adds `nb_planned_improvements` to `accounts`.
    """
    account_id = getattr(agg_score, 'account_id', None)
    nb_answers = getattr(agg_score, 'nb_answers', None)
    if nb_answers is None:
        # Putting the following statement in the default clause will lead
        # to an exception since `getattr(agg_score, 'answer_id')` will be
        # evaluated first.
        nb_answers = 0 if getattr(agg_score, 'answer_id') is None else 1
    if not account_id in accounts:
        accounts[account_id] = {}
    accounts[account_id].update({
        'nb_planned_improvements': nb_answers
    })


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
            if 'sample' in scores:
                agg_scores['sample'] = scores['sample']
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


def push_improvement_factors(rollup_tree, total_numerator, total_denominator,
                             normalize_to_one=True, path_weight=1.0):
    """
    Push factors which are used to compute percentage added to a total
    score when improvements are selected.

    Recursively populate the tree *rollup_tree* with aggregated scores
    for improvements.

    ``populate_rollup`` must be called before this function in order
    to compute the aggregated denominator used to normailze the total score.

    *path_weight* is the compound weight (through multiplication)
    from the root to the node. That's the factor for how much a question
    will actually contribute to the final score.
    """
    #pylint:disable=too-many-locals,unused-argument
    values = rollup_tree[0]
    # If the total of the children weights is 1.0, we are dealing
    # with percentages so we need to normalize all children numerators
    # and denominators to compute this node score.
    root_score_weight = values.get('score_weight', 1.0)
    if len(rollup_tree[1]) > 1:
        total_score_weight = 0
        for node in six.itervalues(rollup_tree[1]):
            score_weight = node[0].get('score_weight', 1.0)
            total_score_weight += score_weight
        normalize_children = (
            (1.0 - 0.01) < total_score_weight < (1.0 + 0.01))
    else:
        # With only one children the weight will always be 1 yet we don't
        # want to normalize here.
        normalize_children = False

    for node in six.itervalues(rollup_tree[1]):
        push_improvement_factors(node,                        # recursive call
            total_numerator, total_denominator,
            normalize_children, path_weight=(path_weight * root_score_weight))

    accounts = values['accounts']
    for _, scores in six.iteritems(accounts):
        if 'opportunity_numerator' in scores:
            opportunity_denominator = scores.get('opportunity_denominator', 0)
            opportunity_numerator = scores.get('opportunity_numerator', 0)
            if total_denominator:
                scores['improvement_percentage'] = 100.0 * (
                    (total_numerator + path_weight * opportunity_numerator)
                    / (total_denominator
                       + path_weight * opportunity_denominator)
                    - (total_numerator / total_denominator))
            else:
                scores['improvement_percentage'] = 0
