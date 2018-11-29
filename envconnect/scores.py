# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

"""
Compute organization assessment and improvement scores.
"""
from __future__ import unicode_literals

import datetime
from decimal import Decimal

from django.utils import six


def _normalize(scores, normalize_to_one=False):
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
    if nb_answers == nb_questions:
        # If we don't have the same number of questions
        # and answers, numerator and denominator are meaningless.
        denominator = scores.get(denominator_key, 0)
        if denominator > 0:
            scores['normalized_score'] = int(
                scores[numerator_key] * Decimal(100) / denominator)
            if 'improvement_numerator' in scores:
                scores['improvement_score'] = (
                    scores['improvement_numerator'] * Decimal(100)
                    / denominator)
            if normalize_to_one:
                if numerator_key in scores:
                    scores[numerator_key] = (
                        float(scores[numerator_key]) / denominator)
                if 'improvement_numerator' in scores:
                    scores['improvement_numerator'] = (
                        float(scores['improvement_numerator']) / denominator)
                scores[denominator_key] = Decimal(1)
        else:
            scores['normalized_score'] = Decimal(0)
    else:
        scores.pop(numerator_key, None)
        scores.pop(denominator_key, None)


def populate_rollup(rollup_tree, normalize_to_one):
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
    numerator_key = 'numerator'
    denominator_key = 'denominator'
    values = rollup_tree[0]
    slug = values.get('slug', None)
    total_score_weight = 0
    if len(rollup_tree[1]) > 1:
        for node in six.itervalues(rollup_tree[1]):
            score_weight = Decimal(node[0].get('score_weight', 1))
            total_score_weight += score_weight
        normalize_children = ((Decimal(1) - Decimal(0.01)) < total_score_weight
            and total_score_weight < (Decimal(1) + Decimal(0.01)))
    else:
        # With only one children the weight will always be 1 yet we don't
        # want to normalize here.
        normalize_children = False

    if not 'accounts' in values:
        values['accounts'] = {}
    accounts = values['accounts']
    for node in six.itervalues(rollup_tree[1]):
        populate_rollup(node, normalize_children) # recursive call
        score_weight = Decimal(node[0].get('score_weight', 1))
        for account_id, scores in six.iteritems(
                node[0].get('accounts', {})):
            if not account_id in accounts:
                accounts[account_id] = {}
            agg_scores = accounts[account_id]
            if not 'nb_answers' in agg_scores:
                agg_scores['nb_answers'] = 0
            if not 'nb_questions' in agg_scores:
                agg_scores['nb_questions'] = 0

            if 'created_at' in scores:
                if not ('created_at' in agg_scores and isinstance(
                        agg_scores['created_at'], datetime.datetime)):
                    agg_scores['created_at'] = scores['created_at']
                elif (isinstance(
                        agg_scores['created_at'], datetime.datetime) and
                      isinstance(scores['created_at'], datetime.datetime)):
                    agg_scores['created_at'] = max(
                        agg_scores['created_at'], scores['created_at'])
            nb_answers = scores['nb_answers']
            nb_questions = scores['nb_questions']
            if slug != 'totals' or nb_answers > 0:
                # Aggregation of total scores is different. We only want to
                # count scores for assessment that matter
                # for an organization's industry.
                agg_scores['nb_answers'] += nb_answers
                agg_scores['nb_questions'] += nb_questions
                for key in [numerator_key, denominator_key,
                            'improvement_numerator']:
                    agg_scores[key] = agg_scores.get(key, 0) + (
                        scores.get(key, 0) * score_weight)

    for account_id, scores in six.iteritems(accounts):
        _normalize(scores, normalize_to_one=normalize_to_one)


def push_improvement_factors(rollup_tree, total_numerator, total_denominator,
                             normalize_to_one=True, path_weight=Decimal(1)):
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
    root_score_weight = Decimal(values.get('score_weight', 1))
    if len(rollup_tree[1]) > 1:
        total_score_weight = 0
        for node in six.itervalues(rollup_tree[1]):
            score_weight = Decimal(node[0].get('score_weight', 1))
            total_score_weight += score_weight
        normalize_children = ((Decimal(1) - Decimal(0.01)) < total_score_weight
            and total_score_weight < (Decimal(1) + Decimal(0.01)))
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
                scores['improvement_percentage'] = Decimal(100) * (
                    (total_numerator + path_weight * opportunity_numerator)
                    / (total_denominator
                       + path_weight * opportunity_denominator)
                    - (total_numerator / total_denominator))
            else:
                scores['improvement_percentage'] = 0
