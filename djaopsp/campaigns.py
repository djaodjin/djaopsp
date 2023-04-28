# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import csv, json, logging

from django.db import transaction
from pages.models import RelationShip
from survey.models import Campaign, EnumeratedQuestions, Unit
from survey.utils import get_content_model, get_question_model

from .compat import StringIO


LOGGER = logging.getLogger(__name__)

DB_PATH_SEP = '/'


def import_campaign(campaign, file_d):
    if not isinstance(campaign, Campaign):
        campaign = Campaign.objects.get(slug=campaign)
    content_model = get_content_model()
    csv_file = csv.reader(file_d if file_d else StringIO())
    with transaction.atomic():
        cols = []
        row = next(csv_file)
        # first row is (heading/practice title), (default_unit), segments
        for seg in row[2:]:
            title = seg
            try:
                content, _ = content_model.objects.get_or_create(
                    title=title, defaults={
                        'account_id': campaign.account_id,
                        'extra': json.dumps({
                            "pagebreak": True,
                            "searchable": True,
                            "tags": [
                                "industry", "pagebreak", "scorecard", "enabled"]
                        })
                    })
                cols += [DB_PATH_SEP + content.slug]
            except content_model.MultipleObjectsReturned as err:
                LOGGER.error("%s: segment '%s' already exists" % (err, title))
                raise
        # follow on rows could be heading or practice
        _import_campaign_section(campaign, csv_file, [cols])


def _import_campaign_section(campaign, csv_reader, seg_prefixes,
                             headings=None, rank=1):
    #pylint:disable=too-many-arguments,too-many-locals,too-many-nested-blocks
    LOGGER.debug("%d segment prefixes: %s", len(seg_prefixes), seg_prefixes)
    if headings is None:
        headings = [None]
    content_model = get_content_model()
    section_rank = 1
    try:
        row = next(csv_reader)
        while row:
            # XXX follow on rows could be heading or practice
            title = row[0]
            level_unit = row[1]
            LOGGER.info('adding "%s" (level_unit=%s) ...', title, level_unit)
            section_level = 0
            default_unit = None
            try:
                section_level = int(level_unit)
                content = content_model.objects.create(
                    title=title, account=campaign.account)
            except ValueError:
                try:
                    default_unit = Unit.objects.get(slug=level_unit)
                except Unit.DoesNotExist as err:
                    LOGGER.error("%s: cannot find unit '%s'" % (
                        err, level_unit))
                    raise
                content, _ = content_model.objects.get_or_create(
                    title=title, account=campaign.account)
            if section_level:
                # We have a heading
                while len(seg_prefixes) > section_level:
                    seg_prefixes.pop()
                    headings.pop()
                if section_level == 1:
                    for idx, col in enumerate(row[2:]):
                        if col:
                            heading = content_model.objects.get(
                                slug=seg_prefixes[0][idx][1:])
                            section_rank = RelationShip.objects.filter(
                                orig_element=heading).count() + 1
                            RelationShip.objects.get_or_create(
                                orig_element=heading,
                                dest_element=content,
                                defaults={
                                    'rank': section_rank
                                })
                else:
                    section_rank = RelationShip.objects.filter(
                        orig_element=headings[-1]).count() + 1
                    RelationShip.objects.get_or_create(
                        orig_element=headings[-1],
                        dest_element=content,
                        defaults={
                            'rank': section_rank
                        })
                seg_prefixes.append([DB_PATH_SEP.join([
                    prefix, content.slug]) for prefix in seg_prefixes[-1]])
                headings.append(content)
                assert len(seg_prefixes) == (section_level + 1)
                section_rank = 1
            else:
                # We have a practice
                RelationShip.objects.get_or_create(
                    orig_element=headings[-1],
                    dest_element=content,
                    defaults={
                        'rank': section_rank
                    })
                section_rank += 1
                for idx, col in enumerate(row[2:]):
                    if col:
                        path = DB_PATH_SEP.join(
                            [seg_prefixes[-1][idx], content.slug])
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
            row = next(csv_reader)
    except StopIteration:
        pass
    return rank
