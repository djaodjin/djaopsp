# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

import logging, re
from collections import namedtuple

from deployutils.helpers import datetime_or_now
from django.db import connection, connections
from django.db.models import F
from django.db.utils import DEFAULT_DB_ALIAS
from survey.models import Answer, Choice, Metric, Sample, Unit
from survey.utils import get_account_model

from .models import Consumption


LOGGER = logging.getLogger(__name__)


def is_sqlite3(db_key=None):
    if db_key is None:
        db_key = DEFAULT_DB_ALIAS
    return connections.databases[db_key]['ENGINE'].endswith('sqlite3')


def as_measured_value(datapoint, unit=None, measured=None):
    if not unit:
        unit = (datapoint.unit if datapoint.unit else datapoint.metric.unit)
    if measured is None:
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


def get_segments(sample_ids):
    """
    Returns segments which contain at least one answer
    for samples in `sample_ids`.
    """
    results = []
    if is_sqlite3():
        paths = Consumption.objects.filter(
            answer__question=F('id'),
            answer__sample__in=sample_ids).order_by('path').values('path')
        segments = set([])
        for path in paths:
            look = re.match(r'^(\S+/sustainability-[a-zA-Z0-9\-]+)/',
                path.get('path', ""))
            if look:
                segments |= set([look.group(1)])
        for segment in segments:
            results += [(segment, "XXX")]
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
