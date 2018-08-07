# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

"""
Generates SQL to create new organizations and their dashboards.
"""
import csv, logging
from collections import namedtuple

from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify
from deployutils.helpers import datetime_or_now

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    #pylint:disable=too-many-instance-attributes

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('filenames', metavar='filenames', nargs='+',
            help="CSV files with data to import")

    def handle(self, *args, **options):
        filenames = options['filenames']
        for filename in filenames:
            if filename.endswith('.csv'):
                self.stderr.write("import %s ..." % str(filename))
                self.stdout.write("BEGIN;")
                with open(filename) as obj:
                    self.import_dashboards(obj, datetime_or_now())
                self.stdout.write("COMMIT;")

    def import_dashboards(self, obj, created_at):
        csv_read = csv.reader(obj)
        try:
            first_line = [name.lower() for name in next(csv_read)]
        except StopIteration:
            self.stderr.write("error: empty file")
            return
        mytsp_record = namedtuple('mytsp_record', first_line)
        for row in csv_read:
            rec = mytsp_record._make(row)
            self.stdout.write("""
INSERT INTO saas_organization (slug, full_name, created_at,
    email, phone, street_address, locality, region, postal_code, country,
    funds_balance, is_active) VALUES (
    '%(organization_slug)s',
    '%(organization_full_name)s',
    '%(created_at)s',
    '%(organization_email)s',
    '%(organization_phone)s',
    '%(organization_street_address)s',
    '%(organization_locality)s',
    '%(organization_region)s',
    '%(organization_postal_code)s',
    '%(organization_country)s',
    0, 't');
INSERT INTO saas_role (role_description_id, user_id, organization_id) VALUES (
    1, 6,
    (SELECT id FROM saas_organization WHERE slug='%(organization_slug)s'));
INSERT INTO saas_plan (slug, title, created_at,
    is_not_priced, interval, description,
    is_active, setup_amount, period_amount, transaction_fee, unit,
    organization_id) VALUES (
    '%(organization_slug)s-report',
    'Reporting to %(organization_full_name)s',
    '%(created_at)s', 't', 4,
    'Enable reporting suppliers to share scorecard through MyTSP',
    'f', 0, 0, 0, 'usd',
    (SELECT id FROM saas_organization WHERE slug='%(organization_slug)s'));
INSERT INTO survey_matrix (slug, title, metric_id,
    account_id) VALUES (
    '%(organization_slug)s-totals',
    'Total scores by industry segment', 15,
    (SELECT id FROM saas_organization WHERE slug='%(organization_slug)s'));
"""
                % {
                    'organization_slug': slugify(rec.full_name),
                    'organization_full_name': rec.full_name,
                    'organization_email': rec.email,
                    'organization_phone': rec.phone,
                    'organization_street_address': rec.street_address,
                    'organization_locality': rec.locality,
                    'organization_region': rec.region,
                    'organization_postal_code': rec.postal_code,
                    'organization_country': rec.country,
                    'created_at': created_at,
                })
