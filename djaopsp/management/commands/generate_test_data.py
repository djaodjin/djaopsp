# Copyright (c) 2023, DjaoDjin inc.
# All rights reserved.

"""
Command to generate test data

This command is used for livedemo and recording video tutorials.
"""
import datetime, json, logging, random

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
from faker import Faker
from survey.api.sample import update_or_create_answer
from survey.models import Campaign, Choice, Sample, Unit
from survey.queries import datetime_or_now
from survey.utils import get_account_model, get_question_model

from ...scores import (freeze_scores, get_score_calculator,
    populate_scorecard_cache)
from ...models import VerifiedSample


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):

    user_model = get_user_model()
    account_model = get_account_model()

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--nb_profiles', action='store',
            dest='nb_profiles', default=100,
            help='number of profiles to generate')
        parser.add_argument('--campaign', action='store',
            dest='campaign', default='sustainability',
            help='name of of the campaign')

    def handle(self, *args, **options):
        #pylint:disable=too-many-locals,too-many-statements
        start_time = datetime.datetime.utcnow()

        campaign = options['campaign']
        verification_campaign = "%s-verified" % campaign
        fake = Faker()
        profiles = self.generate_profiles(
            nb_profiles=options['nb_profiles'], fake=fake)
        self.generate_frozen_samples(profiles, campaign, verification_campaign,
            fake=fake)

        end_time = datetime.datetime.utcnow()
        delta = relativedelta(end_time, start_time)
        LOGGER.info("completed in %d hours, %d minutes, %d.%d seconds",
            delta.hours, delta.minutes, delta.seconds, delta.microseconds)
        self.stderr.write("completed in %d hours, %d minutes, %d.%d seconds\n"
            % (delta.hours, delta.minutes, delta.seconds, delta.microseconds))

    def generate_profiles(self, nb_profiles=100, fake=None):
        profiles = []
        if not fake:
            fake = Faker()

        for demo_id in range(0, nb_profiles):
            full_name = fake.company()
            slug = slugify('demo%d' % demo_id)
            email = "%s@%s" % (slug, fake.domain_name())
            extra = None
            priority = random.randint(0, 2)
            if priority:
                extra = json.dumps({'priority': priority})
            profile, _ = self.account_model.objects.get_or_create(
                slug=slug,
                full_name=full_name,
                email=email,
                phone=fake.phone_number(),
                extra=extra)
            profiles += [profile]
        return profiles

    def generate_frozen_samples(self, profiles, campaign, verification_campaign,
                                fake=None):
        #pylint:disable=too-many-locals
        if not fake:
            fake = Faker()
        ends_at = datetime_or_now()
        start_at = ends_at - relativedelta(years=1)
        if not isinstance(campaign, Campaign):
            campaign = Campaign.objects.get(slug=str(campaign))
        if not isinstance(verification_campaign, Campaign):
            verification_campaign = Campaign.objects.get(
                slug=str(verification_campaign))
        segment_path = "/%s" % str(campaign)
        segment_title = campaign.title
        questions = get_question_model().objects.filter(
            enumeratedquestions__campaign=campaign,
            enumeratedquestions__question__path__startswith=segment_path)
        for profile in profiles:
            created_date = fake.date_between(start_at, ends_at)
            created_at = datetime_or_now(datetime.datetime(created_date.year, created_date.month, created_date.day))            
            sample = Sample.objects.create(
                campaign=campaign, account=profile, created_at=created_at)
            for question in questions:
                unit = question.default_unit
                if unit.system in (Unit.SYSTEM_ENUMERATED,):
                    choice = random.choice(Choice.objects.filter(unit=unit))
                    datapoint = {
                        'measured': choice
                    }
                    update_or_create_answer(
                        datapoint, question, sample, created_at)
            frozen_sample = freeze_scores(sample, created_at=created_at)
            calculator = get_score_calculator(segment_path)
            populate_scorecard_cache(
                frozen_sample, calculator, segment_path, segment_title)
            _verified = VerifiedSample.objects.create(
                sample=frozen_sample,
                verifier_notes=Sample.objects.create(
                    campaign=verification_campaign,
                    account=verification_campaign.account),
                verified_status=random.randint(
                    VerifiedSample.STATUS_NO_REVIEW,
                    VerifiedSample.STATUS_RIGOROUS),
                verified_by=random.choice(self.user_model.objects.filter(
                    username__in=['donny', 'alice'])))
