# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import csv, logging

from django.db import transaction
from pages.models import RelationShip
from survey.models import EnumeratedQuestions, Unit
from survey.utils import get_content_model, get_question_model

from .compat import StringIO


LOGGER = logging.getLogger(__name__)

DB_PATH_SEP = '/'


def import_campaign(campaign, file_d):

    csv_file = csv.reader(StringIO(file_d.read().decode(
        'utf-8', 'ignore')) if file_d else StringIO())
    with transaction.atomic():
        seg_prefixes = []
        row = next(csv_file)
        # first row is (heading/practice title), (default_unit), segments
        for seg in row[2:]:
            title = seg
            content, _ = get_content_model().objects.get_or_create(
                title=title)
            seg_prefixes += [DB_PATH_SEP + content.slug]
        # follow on rows could be heading or practice
        _import_campaign_section(campaign, csv_file, seg_prefixes)


def _import_campaign_section(campaign, csv_reader, seg_prefixes,
                             heading=None, level=0, rank=1):
    #pylint:disable=too-many-arguments,too-many-locals
    LOGGER.debug("create section %s", heading)
    section_rank = 1
    try:
        row = next(csv_reader)
        while row:
            # XXX follow on rows could be heading or practice
            title = row[0]
            level_unit = row[1]
            section_level = 0
            default_unit = None
            try:
                section_level = int(level_unit)
            except ValueError:
                default_unit = Unit.objects.get(slug=level_unit)
            content, _ = get_content_model().objects.get_or_create(
                title=title)
            RelationShip.objects.get_or_create(
                orig_element=heading,
                dest_element=content,
                defaults={
                    'rank': section_rank
                })
            section_rank += 1
            if section_level:
                if section_level < level:
                    break
                # We have a heading
                rank = _import_campaign_section(
                    campaign, csv_reader, [DB_PATH_SEP.join([
                        prefix, heading.slug
                    ]) for prefix in seg_prefixes], content, section_level,
                    rank)
            else:
                for idx, col in enumerate(row[1:]):
                    if col:
                        path = DB_PATH_SEP.join(
                            [seg_prefixes[idx], heading.slug, content.slug])
                        LOGGER.debug("create question %s", path)
                        question, _ = \
                            get_question_model().objects.get_or_create(
                                path=path, defaults={
                                    'content': content,
                                    'default_unit': default_unit
                                })
                        EnumeratedQuestions.objects.get_or_create(
                            campaign=campaign,
                            question=question,
                            defaults={
                                'rank': rank,
                                'required': True
                            })
                        rank = rank + 1
    except StopIteration:
        pass
    return rank
