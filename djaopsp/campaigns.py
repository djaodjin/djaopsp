# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import csv, json, logging, openpyxl, zipfile

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

    rows = []
    try:
        wbook = openpyxl.load_workbook(file_d)
        for row in wbook.active.iter_rows():
            rows += [[cell.value for cell in row]]
        # First row is title of campaign.
        # Second row is column headers (practice/heading, unit, required,
        # segments).
        col_headers = rows[1]
        rows = iter(rows[2:])
    except zipfile.BadZipFile:
        # Apparently this is not an Excel spreadsheet.
        pass

    if not rows:
        file_d.seek(0)
        csv_file = csv.reader(StringIO(file_d.read().decode(
            'utf-8', 'ignore')) if file_d else StringIO())
        # First row is title of campaign.
        # Second row is column headers (practice/heading, unit, required,
        # segments).
        col_headers = next(csv_file)
        col_headers = next(csv_file)
        rows = csv_file

    content_model = get_content_model()
    with transaction.atomic():
        # First are title of segments
        segments = _import_campaign_segments(campaign, col_headers[3:],
            content_model=content_model)
        # follow on rows could be heading or practice
        _import_campaign_section(campaign, rows, [segments],
            content_model=content_model)


def _import_campaign_segments(campaign, cols, content_model=None):
    if not content_model:
        content_model = get_content_model()

    segments = []
    for title in cols:
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
            segments += [DB_PATH_SEP + content.slug]
        except content_model.MultipleObjectsReturned as err:
            LOGGER.error("%s: segment '%s' already exists", err, title)
            raise

    return segments


def _import_campaign_section(campaign, rows, seg_prefixes,
                             headings=None, rank=1, content_model=None):
    #pylint:disable=too-many-arguments,too-many-locals,too-many-nested-blocks
    if not content_model:
        content_model = get_content_model()

    LOGGER.debug("%d segment prefixes: %s", len(seg_prefixes), seg_prefixes)
    freetext_unit = Unit.objects.get(slug='freetext')
    if headings is None:
        headings = [None]
    section_rank = 1
    try:
        row = next(rows)
        while row:
            # XXX follow on rows could be heading or practice
            title = row[0]
            level_unit = row[1]
            required = not(row[2] and row[2].lower() == "false")
            LOGGER.info('adding "%s" (level_unit=%s, required=%s) ...',
                title, level_unit, required)
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
                    LOGGER.error("%s: cannot find unit '%s'",
                        err, level_unit)
                    raise
                content, _ = content_model.objects.get_or_create(
                    title=title, account=campaign.account)
            if section_level:
                # We have a heading
                while len(seg_prefixes) > section_level:
                    seg_prefixes.pop()
                    headings.pop()
                if section_level == 1:
                    for idx, col in enumerate(row[3:]):
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
                for idx, col in enumerate(row[3:]):
                    if col:
                        path = DB_PATH_SEP.join(
                            [seg_prefixes[-1][idx], content.slug])
                        question_defaults = {
                            'content': content,
                            'default_unit': default_unit,
                        }
                        if default_unit == freetext_unit:
                            question_defaults.update({'ui_hint': "textarea"})
                        LOGGER.debug("create question %s", path)
                        question, _ = \
                            get_question_model().objects.get_or_create(
                                path=path, defaults=question_defaults)
                        EnumeratedQuestions.objects.get_or_create(
                            campaign=campaign,
                            question=question,
                            defaults={
                                'rank': rank,
                                'required': required
                            })
                        rank = rank + 1
            row = next(rows)
    except StopIteration:
        pass
    return rank
