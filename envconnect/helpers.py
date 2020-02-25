# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

import logging
from collections import namedtuple

from deployutils.helpers import datetime_or_now
from django.db import connection, connections
from django.db.utils import DEFAULT_DB_ALIAS
from survey.models import Answer, Choice, Metric, Sample, Unit
from survey.utils import get_account_model

from .models import Consumption, get_scored_answers


LOGGER = logging.getLogger(__name__)


def is_sqlite3(db_key=None):
    if db_key is None:
        db_key = DEFAULT_DB_ALIAS
    return connections.databases[db_key]['ENGINE'].endswith('sqlite3')


def as_measured_value(datapoint, unit=None, measured=None):
    if not unit:
        unit = (datapoint.unit if datapoint.unit else datapoint.metric.unit)
    if not measured:
        measured = datapoint.measured
    if unit.system in Unit.NUMERICAL_SYSTEMS:
        measured = '%d' % measured
    else:
        try:
            measured = str(Choice.objects.get(pk=measured))
        except Choice.DoesNotExist:
            LOGGER.error("cannot find Choice %s for %s",
                measured, datapoint)
            measured = ""
    return measured


def as_valid_sheet_title(title):
    """
    Prevents 'Invalid character / found in sheet title' errors.
    """
    return title.replace('/', '-')


def freeze_scores(sample, includes=None, excludes=None,
                  collected_by=None, created_at=None):
    #pylint:disable=too-many-locals
    # This function must be executed in a `transaction.atomic` block.
    LOGGER.info("freeze scores for %s based of sample %s",
        sample.account, sample.slug)
    created_at = datetime_or_now(created_at)
    score_sample = Sample.objects.create(
        created_at=created_at,
        survey=sample.survey,
        account=sample.account,
        extra=sample.extra,
        is_frozen=True)
    # Copy the actual answers
    score_metric_id = Metric.objects.get(slug='score').pk
    for answer in Answer.objects.filter(
            sample=sample).exclude(metric_id=score_metric_id):
        answer.pk = None
        answer.sample = score_sample
        answer.save()
        LOGGER.debug("save(created_at=%s, question_id=%s, metric_id=%s,"\
            " measured=%s, denominator=%s, collected_by=%s,"\
            " sample=%s, rank=%d)",
            answer.created_at, answer.question_id, answer.metric_id,
            answer.measured, answer.denominator, answer.collected_by,
            answer.sample, answer.rank)
    # Create frozen scores for answers we can derive a score from
    # (i.e. assessment).
    assessment_metric_id = Metric.objects.get(slug='assessment').pk
    scored_answers = get_scored_answers(
        Consumption.objects.get_active_by_accounts(
            sample.survey, excludes=excludes),
        assessment_metric_id, includes=includes)
    with connection.cursor() as cursor:
        cursor.execute(scored_answers, params=None)
        col_headers = cursor.description
        decorated_answer_tuple = namedtuple(
            'DecoratedAnswerTuple', [col[0] for col in col_headers])
        for decorated_answer in cursor.fetchall():
            decorated_answer = decorated_answer_tuple(
                *decorated_answer)
            if (decorated_answer.answer_id and
                decorated_answer.is_planned == sample.extra):
                numerator = decorated_answer.numerator
                denominator = decorated_answer.denominator
                LOGGER.debug("create(created_at=%s, question_id=%s,"\
                    " metric_id=%s, measured=%s, denominator=%s,"\
                    " collected_by=%s, sample=%s, rank=%d)",
                    created_at, decorated_answer.id, score_metric_id,
                    numerator, denominator, collected_by, score_sample,
                    decorated_answer.rank)
                _ = Answer.objects.create(
                    created_at=created_at,
                    question_id=decorated_answer.id,
                    metric_id=score_metric_id,
                    measured=numerator,
                    denominator=denominator,
                    collected_by=collected_by,
                    sample=score_sample,
                    rank=decorated_answer.rank)
    sample.created_at = datetime_or_now()
    sample.save()
    return score_sample


def get_segments(sample_ids):
    """
    Returns segments which contain at least one answer
    for samples in `sample_ids`.
    """
    results = []
    if is_sqlite3():
        LOGGER.warning(
        "`get_segments` does not support SQLite3 at this time. returning `[]`")
    else:
        raw_query = ("""WITH segments AS (
SELECT distinct(substring(survey_question.path from
        '.*/sustainability-[^/]+/')) AS path
    FROM survey_question INNER JOIN survey_answer
    ON survey_question.id = survey_answer.question_id WHERE sample_id IN (%s))
SELECT segments.path, pages_pageelement.title
    FROM pages_pageelement INNER JOIN segments
    ON pages_pageelement.slug = substring(segments.path from
        '/(sustainability-[^/]+)/')
    ORDER BY pages_pageelement.title;
""" %
            ", ".join([str(sample_id) for sample_id in sample_ids]))
        with connection.cursor() as cursor:
            cursor.execute(raw_query)
            for segment in cursor:
                if not segment[0].startswith('/euissca-rfx'):
                    results += [segment]
#            results = list(cursor.fetchall())
    return results


def get_testing_accounts():
    return [val['pk'] for val in get_account_model().objects.filter(
        extra__contains='testing').values('pk')]
