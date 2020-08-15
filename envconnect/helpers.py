# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

import logging, re, json
from collections import namedtuple

from deployutils.helpers import datetime_or_now
from django.db import connection, connections
from django.db.models import F
from django.db.utils import DEFAULT_DB_ALIAS
from pages.models import build_content_tree, PageElement
from survey.models import Answer, Choice, Metric, Sample, Unit
from survey.utils import get_account_model

from .compat import six
from .models import Consumption


LOGGER = logging.getLogger(__name__)


class ContentCut(object):
    """
    Visitor that cuts down a content tree whenever TAG_PAGEBREAK is encountered.
    """
    TAG_PAGEBREAK = 'pagebreak'

    def __init__(self, tag=TAG_PAGEBREAK, depth=1):
        self.match = tag

    def enter(self, tag):
        if tag and self.match:
            if isinstance(tag, dict):
                return not (self.match in tag.get('tags', []))
            return not (self.match in tag)
        return True

    def leave(self, attrs, subtrees):
        #pylint:disable=unused-argument
        return True


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


def flatten(rollup_trees, depth=0):
    result = []
    for key, values in six.iteritems(rollup_trees):
        elem, nodes = values
        path = None if nodes else elem.get('path', key)
        result += [{'title': elem['title'], 'path': path, 'indent': depth}]
        result += flatten(nodes, depth=depth + 1)
    return result


def get_segments():
    """
    Returns a list of segment prefixes
    """
    content_tree = build_content_tree(
        roots=PageElement.objects.get_roots().filter(tag__contains='industry'),
        prefix='/', cut=ContentCut())
    segments = flatten(content_tree)
    return segments


def get_segments_from_samples(sample_ids):
    """
    Returns segments which contain at least one answer
    for samples in `sample_ids`.
    """
    results = []
    for segment in get_segments():
        if segment['path'] and Consumption.objects.filter(
            path__startswith=segment['path'],
            answer__question=F('id'),
            answer__sample__in=sample_ids).exists():
            results += [segment]
    return results


def get_testing_accounts():
    return [val['pk'] for val in get_account_model().objects.filter(
        extra__contains='testing').values('pk')]
