# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

import logging

from django.db.models import Max, Q
from pages.models import build_content_tree, PageElement
from survey.models import Choice, Unit
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
                return self.match not in tag.get('tags', [])
            return self.match not in tag
        return True

    def leave(self, attrs, subtrees):
        #pylint:disable=unused-argument
        return True


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
    for key, values in sorted(six.iteritems(rollup_trees),
            key=lambda node: node[1][0]['title']):
        elem, nodes = values
        extra = elem.get('extra', elem.get('tag', {}))
        try:
            tags = extra.get('tags', [])
        except AttributeError:
            tags = extra
        path = None if 'pagebreak' not in tags else elem.get('path', key)
        result += [{'title': elem['title'], 'path': path, 'indent': depth}]
        if 'pagebreak' not in tags:
            result += flatten(nodes, depth=depth + 1)
    return result


def get_segments(content_tree=None, search_query=None):
    """
    Returns a list of segment prefixes
    """
    if not content_tree:
        query_filter = Q(tag__contains='industry')
        if search_query:
            query_filter = query_filter & Q(tag__contains=search_query)
        content_tree = build_content_tree(
            roots=PageElement.objects.get_roots().filter(
                query_filter).order_by('title'),
            prefix='/', cut=ContentCut())
    segments = flatten(content_tree)
    return segments


def get_segments_from_samples(samples, content_tree=None):
    """
    Returns segments which contain at least one answer
    for samples in `sample_ids`.

    The returned dictionary has the following schema:

    .. code-block::

        {
          *sample-id*: ["segment-path", *latest_activity_at*), ...],
          ...
        }

    For example:

    .. code-block::

        get_segments_from_samples([1])

        {
          1: [("/construction", ), "/metal/boxes-and-enclosures"]
        }

    """
    try:
        results = {sample.pk: [] for sample in samples}
    except AttributeError:
        results = {sample: [] for sample in samples}
    for segment in get_segments(content_tree=content_tree):
        if segment['path']:
            for sample in Consumption.objects.filter(
                    path__startswith=segment['path'],
                    answer__sample__in=samples).values(
                    'answer__sample_id').annotate(
                        last_activity_at=Max('answer__created_at')):
                results[sample['answer__sample_id']] += [
                    (segment, sample['last_activity_at'])]
    return results


def get_testing_accounts():
    return [val['pk'] for val in get_account_model().objects.filter(
        extra__contains='testing').values('pk')]
