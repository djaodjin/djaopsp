# Copyright (c) 2023, DjaoDjin inc.
# All rights reserved.

"""
Command to import practices/segments of a campaign
"""
import datetime, logging

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand

from ...campaigns import import_campaign

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--dry-run', action='store_true',
            dest='dry_run', default=False,
            help='Do not commit database updates')
        parser.add_argument('--campaign', action='store',
            dest='campaign',
            help='name of of the campaign')
        parser.add_argument('filename', action='store',
            dest='filename',
            help='csv file with questions for the campaign')


    def handle(self, *args, **options):
        #pylint:disable=too-many-locals,too-many-statements
        start_time = datetime.datetime.utcnow()
        self.import_campaign(
            options['campaign'],
            options['filename'])
        end_time = datetime.datetime.utcnow()
        delta = relativedelta(end_time, start_time)
        LOGGER.info("completed in %d hours, %d minutes, %d.%d seconds",
            delta.hours, delta.minutes, delta.seconds, delta.microseconds)
        self.stdout.write("completed in %d hours, %d minutes, %d.%d seconds\n"
            % (delta.hours, delta.minutes, delta.seconds, delta.microseconds))


    def import_campaign(self, campaign, filename):
        with open(filename) as file_d:
            import_campaign(campaign, file_d)
