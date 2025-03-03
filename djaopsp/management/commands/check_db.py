# Copyright (c) 2025, DjaoDjin inc.
# All rights reserved.

"""
Command for data validation

Checks that for each (grantee, account, campaign) triplets,
`portfolio.ends_at` is greater than the last time the `account`
shared `campaign` responses with the `grantee`.
"""
import datetime, logging

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count, Max
from pages.models import PageElement
from survey.models import Answer, Campaign, PortfolioDoubleOptIn, Sample, Unit
from survey.queries import sql_frozen_answers
from survey.settings import DB_PATH_SEP
from survey.utils import get_account_model, get_question_model

from ...queries import get_engagement
from ...utils import get_account_model


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):

    account_model = get_account_model()

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--exclude-units', action='append',
            dest='exclude_units', default=[],
            help='Exclude units from comparaison (ex: points)')
        parser.add_argument('--show-active', action='store_true',
            dest='show_active', default=False,
            help='Show active sample with question not in campaign')
        parser.add_argument('--show-portfolios', action='store_true',
            dest='show_portfolios', default=False,
            help='Show portfolios that do not match optins')
        parser.add_argument('--show-portfolios-fix', action='store_true',
            dest='show_portfolios_fix', default=False,
            help='Show SQL fixes for portfolios that do not match optins')
        parser.add_argument('--show-completed-notshared', action='store_true',
            dest='show_completed_notshared', default=False,
            help='Show completed but not shared responses')
        parser.add_argument('--show-updated-not-frozen', action='store_true',
            dest='show_updated_not_frozen', default=False,
            help='Show active samples that have been fully'\
                ' updated but not frozen')
        parser.add_argument('--show-duplicate-samples', action='store_true',
            dest='show_duplicate_samples', default=False,
            help='Show duplicate samples for an account')
        parser.add_argument('--show-questions', action='store_true',
            dest='show_questions', default=False,
            help='Show questions that do not match elements')
        parser.add_argument('--show-questions-fix', action='store_true',
            dest='show_questions_fix', default=False,
            help='Show SQL fixes for questions that do not match elements')
        parser.add_argument('--show-answers', action='store_true',
            dest='show_answers', default=False,
            help='Show answers that do not match elements')
        parser.add_argument('--show-answers-fix', action='store_true',
            dest='show_answers_fix', default=False,
            help='Show SQL fixes for answers that do not match elements')
        parser.add_argument('--dry-run', action='store_true',
            dest='dry_run', default=False,
            help='Do not commit database updates')

    def handle(self, *args, **options):
        #pylint:disable=too-many-locals,too-many-statements
        start_time = datetime.datetime.utcnow()
        self.check_active_samples(show=options['show_active'])
        self.check_updated_not_frozen(
            show=options['show_updated_not_frozen'])
        self.check_completed_notshared(
            show=options['show_completed_notshared'])
        self.check_portfolios(
            show=options['show_portfolios'],
            show_fix=options['show_portfolios_fix'])
        if options['show_questions'] or options['show_answers']:
            self.check_questions(
                show=options['show_questions'],
                show_fix=options['show_questions_fix'])
            self.check_answers(
                show=options['show_answers'],
                show_fix=options['show_answers_fix'])
        for campaign in Campaign.objects.all():
            self.check_duplicate_samples(campaign=campaign,
                exclude_units=options['exclude_units'],
                show=options['show_duplicate_samples'])
        end_time = datetime.datetime.utcnow()
        delta = relativedelta(end_time, start_time)
        LOGGER.info("completed in %d hours, %d minutes, %d.%d seconds",
            delta.hours, delta.minutes, delta.seconds, delta.microseconds)
        self.stderr.write("completed in %d hours, %d minutes, %d.%d seconds\n"
            % (delta.hours, delta.minutes, delta.seconds, delta.microseconds))


    def check_active_samples(self, show=False):
        count = 0
        for sample in Sample.objects.filter(is_frozen=False).select_related(
                'campaign'):
            unexpected_answers = Answer.objects.filter(
                sample=sample).exclude(
                question__in=sample.campaign.questions.all()).select_related(
                'question', 'unit')
            if unexpected_answers.exists():
                count += 1
                if show:
                    for answer in unexpected_answers:
                        self.stdout.write('%d,%s,"%s","%s"' % (
                            sample.pk, answer.created_at.date(),
                            answer.unit, answer.question.path))
        self.stderr.write("%d active samples with unexpected answers" % count)

    def check_updated_not_frozen(self, show=False):
        count = 0
        for sample in Sample.objects.filter(is_frozen=False,
                created_at__lt=Max('answers__created_at')).annotate(
                answers_count=Count('answers')).order_by(
                'created_at').select_related('campaign'):
            if not sample.get_required_unanswered_questions().exists():
                count += 1
                if show:
                    self.stdout.write('%s,%s,%s' % (
                        sample.created_at, sample.account, sample))
        self.stderr.write("%d active samples that have been updated,"\
            " answer all required questions, but are not marked complete" %
            count)


    def check_completed_notshared(self, show=False):
        for campaign in Campaign.objects.all():
            count = 0
            queryset = get_engagement(campaign, accounts=None)
            for val in queryset:
                slug = val.account.slug
                reporting_status = val.reporting_status
                if reporting_status in ('completed-notshared',):
                    count += 1
                    if show:
                        self.stdout.write('%d,%s,"%s","%s",%d,%s' % (
                            val.pk, val.created_at.date(),
                            slug, val.printable_name,
                            val.grantee_id, reporting_status))
            self.stderr.write("%d completed-notshared in campaign '%s'" % (
                count, campaign))


    def check_portfolios(self, show=False, show_fix=False):
        #pylint:disable=too-many-locals
        if show_fix:
            show = True
        duplicates_query = """
WITH duplicates AS (
  SELECT grantee_id, account_id, campaign_id, COUNT(*) AS nb_duplicates
  FROM survey_portfolio
  GROUP BY grantee_id, account_id, campaign_id
  HAVING COUNT(*) > 1)
SELECT accounts.slug, grants.slug, campaign_id, nb_duplicates FROM duplicates
INNER JOIN saas_organization AS accounts
ON accounts.id = duplicates.account_id
INNER JOIN saas_organization AS grants
ON grants.id = duplicates.grantee_id
"""
        count = 0
        sep = ""
        with connection.cursor() as cursor:
            cursor.execute(duplicates_query, params=None)
            for duplicate in cursor.fetchall():
                account_slug = duplicate[0]
                grantee_slug = duplicate[1]
                campaign_id = duplicate[2]
                nb_duplicates = duplicate[3]
                if show:
                    if not sep:
                        if show_fix:
                            self.stdout.write("BEGIN;")
                        else:
                            self.stdout.write("grantee_slug,account_slug,"\
                            "campaign_id,nb_duplicates")
                        sep = ",\n"
                    if show_fix:
                        pass
                    else:
                        self.stdout.write("%s,%s,%s,%s" % (
                            grantee_slug, account_slug,
                            str(campaign_id) if campaign_id else "-",
                            nb_duplicates))
                count += 1
        if sep and show_fix:
            self.stdout.write("COMMIT;")
        self.stderr.write("%d duplicate portfolios" % count)

        # portfolio and optins
        optins_query = """
WITH optins AS (
SELECT
    grantee_id,
    account_id,
    campaign_id,
    MAX(created_at) AS last_trigger_at
FROM survey_portfoliodoubleoptin
WHERE
    state IN (%(grant_accepted)d, %(request_accepted)d)
GROUP BY grantee_id, account_id, campaign_id
), outofsync_portfolios AS (
SELECT
    optins.grantee_id,
    optins.account_id,
    optins.campaign_id,
    optins.last_trigger_at,
    survey_portfolio.id,
    survey_portfolio.ends_at
FROM optins LEFT OUTER JOIN survey_portfolio ON (
    survey_portfolio.grantee_id = optins.grantee_id AND
    survey_portfolio.account_id = optins.account_id AND
    survey_portfolio.campaign_id = optins.campaign_id)
WHERE
    survey_portfolio.ends_at IS NULL OR
    optins.last_trigger_at > survey_portfolio.ends_at
    ORDER BY optins.last_trigger_at DESC, optins.grantee_id
), latest_completions AS (
SELECT
    account_id,
    MAX(created_at) AS latest_completed_at
FROM survey_sample
WHERE is_frozen AND extra IS NULL
GROUP BY account_id
), portfolios AS (
SELECT
    outofsync_portfolios.*,
    latest_completions.latest_completed_at AS latest_completed_at
FROM latest_completions
INNER JOIN outofsync_portfolios
ON latest_completions.account_id = outofsync_portfolios.account_id)
SELECT
  grantee_slug,
  %(account_table)s.slug AS account_slug,
  campaign_id,
  last_trigger_at,
  portfolio_id,
  ends_at,
  latest_completed_at
FROM (
SELECT
  %(account_table)s.slug AS grantee_slug,
  account_id,
  campaign_id,
  last_trigger_at,
  portfolios.id AS portfolio_id,
  ends_at,
  latest_completed_at
FROM portfolios INNER JOIN %(account_table)s
ON portfolios.grantee_id = %(account_table)s.id) AS portfolio_grantees
INNER JOIN %(account_table)s
ON portfolio_grantees.account_id = %(account_table)s.id
""" % {
    'grant_accepted': PortfolioDoubleOptIn.OPTIN_GRANT_ACCEPTED,
    'request_accepted': PortfolioDoubleOptIn.OPTIN_REQUEST_ACCEPTED,
    'account_table': self.account_model._meta.db_table
}
        count = 0
        sep = ""
        with connection.cursor() as cursor:
            cursor.execute(optins_query, params=None)
            for optin in cursor.fetchall():
                if show:
                    if not sep:
                        if show_fix:
                            self.stdout.write("BEGIN;")
                        else:
                            self.stdout.write("grantee_slug,account_slug,"\
                            "campaign_id,last_trigger_at,latest_completed_at,"\
                            "portfolio_id,ends_at")
                        sep = ",\n"
                    grantee_slug = optin[0]
                    account_slug = optin[1]
                    campaign_id = optin[2]
                    last_trigger_at = optin[3]
                    portfolio_id = optin[4]
                    ends_at = optin[5]
                    latest_completed_at = optin[6]
                    if show_fix:
                        if portfolio_id:
                            if campaign_id:
                                self.stdout.write(
                                    "UPDATE survey_portfolio SET"\
" ends_at='%(ends_at)s' WHERE grantee_id=(SELECT id FROM %(account_table)s"\
" WHERE slug='%(grantee_slug)s') AND account_id=(SELECT id"\
" FROM %(account_table)s WHERE slug='%(account_slug)s')"\
" AND campaign_id=%(campaign_id)s;" % {
                    'account_table': self.account_model._meta.db_table,
                    'grantee_slug': grantee_slug,
                    'account_slug': account_slug,
                    'ends_at': max(last_trigger_at, latest_completed_at),
                    'campaign_id': str(campaign_id) if campaign_id else "null"})
                            else:
                                self.stdout.write(
                                    "UPDATE survey_portfolio SET"\
" ends_at='%(ends_at)s' WHERE grantee_id=(SELECT id FROM %(account_table)s"\
" WHERE slug='%(grantee_slug)s') AND account_id=(SELECT id"\
" FROM %(account_table)s WHERE slug='%(account_slug)s')"\
" AND campaign_id IS NULL;" % {
                    'account_table': self.account_model._meta.db_table,
                    'grantee_slug': grantee_slug,
                    'account_slug': account_slug,
                    'ends_at': max(last_trigger_at, latest_completed_at)})
                        else:
                            self.stdout.write(
                                "INSERT INTO survey_portfolio (grantee_id,"\
"account_id,campaign_id,ends_at) VALUES ((SELECT id FROM %(account_table)s"\
" WHERE slug='%(grantee_slug)s'),(SELECT id FROM %(account_table)s"\
" WHERE slug='%(account_slug)s'),%(campaign_id)s,'%(ends_at)s');" % {
                    'account_table': self.account_model._meta.db_table,
                    'grantee_slug': grantee_slug,
                    'account_slug': account_slug,
                    'campaign_id': str(campaign_id) if campaign_id else "null",
                    'ends_at': max(last_trigger_at,
                                   latest_completed_at).strftime("%Y-%m-%d")})
                    else:
                        self.stdout.write("%s,%s,%s,%s,%s,%s,%s" % (
                            grantee_slug, account_slug,
                            str(campaign_id) if campaign_id else "-",
                            last_trigger_at.strftime("%Y-%m-%d"),
                            (latest_completed_at.strftime("%Y-%m-%d")
                             if latest_completed_at else "-"),
                            str(portfolio_id) if portfolio_id else "-",
                            ends_at.strftime("%Y-%m-%d") if ends_at else "-"))
                count += 1
        if sep and show_fix:
            self.stdout.write("COMMIT;")
        self.stderr.write("%d inaccurate portfolios" % count)

        # requests for which there are no portfolio yet
        request_no_portfolios_query = """
WITH request_no_portfolios AS (
SELECT %(account_table)s.slug AS account_slug,
       survey_portfoliodoubleoptin.grantee_id,
       survey_portfoliodoubleoptin.campaign_id,
       MIN(survey_portfoliodoubleoptin.created_at) AS created_at
FROM survey_portfoliodoubleoptin
LEFT OUTER JOIN survey_portfolio
ON survey_portfoliodoubleoptin.account_id = survey_portfolio.account_id AND
   survey_portfoliodoubleoptin.grantee_id = survey_portfolio.grantee_id
INNER JOIN %(account_table)s
ON survey_portfoliodoubleoptin.account_id = %(account_table)s.id
WHERE survey_portfoliodoubleoptin.state IN (0, 3, 1, 5) AND
      survey_portfolio.id IS NULL
GROUP BY (
    %(account_table)s.slug,
    survey_portfoliodoubleoptin.grantee_id,
    survey_portfoliodoubleoptin.campaign_id))
SELECT
  %(account_table)s.slug AS grantee_slug,
  request_no_portfolios.account_slug,
  request_no_portfolios.campaign_id,
  request_no_portfolios.created_at
FROM request_no_portfolios
INNER JOIN %(account_table)s
ON %(account_table)s.id = request_no_portfolios.grantee_id""" % {
    'account_table': self.account_model._meta.db_table
}
        count = 0
        sep = ""
        with connection.cursor() as cursor:
            cursor.execute(request_no_portfolios_query, params=None)
            for optin in cursor.fetchall():
                if show:
                    if not sep:
                        if show_fix:
                            self.stdout.write("BEGIN;")
                        else:
                            self.stdout.write("grantee_slug,account_slug,"\
                            "campaign_id,ends_at")
                        sep = ",\n"
                    grantee_slug = optin[0]
                    account_slug = optin[1]
                    campaign_id = optin[2]
                    ends_at = optin[3]
                    if show_fix:
                        self.stdout.write("INSERT INTO survey_portfolio (grantee_id, account_id, campaign_id, ends_at) VALUES ((SELECT id FROM %(account_table)s WHERE slug='%(grantee_slug)s'), (SELECT id FROM %(account_table)s WHERE slug='%(account_slug)s'), %(campaign_id)s, '%(ends_at)s');" % {
                        'account_table': self.account_model._meta.db_table,
                        'grantee_slug': grantee_slug,
                        'account_slug': account_slug,
                        'campaign_id': campaign_id,
                        'ends_at': ends_at})
                    else:
                        self.stdout.write("%s,%s,%s,%s" % (
                            grantee_slug, account_slug, campaign_id, ends_at))
                count += 1
        if sep and show_fix:
            self.stdout.write("COMMIT;")
        self.stderr.write("%d requests without an existing portfolio" % count)


    def check_questions(self, show=False, show_fix=False):
        count = 0
        for question in get_question_model().objects.all():
            slug = question.path.split(DB_PATH_SEP)[-1]
            element = PageElement.objects.get(slug=slug)
            if question.content.pk != element.pk:
                if show:
                    self.stderr.write(
                        "warning: question %s points to content %s"
                        % (question.path, question.content.slug))
                    self.stderr.write("\t    \"%s\"" % question.content.title)
                    self.stderr.write("\tvs. \"%s\"" % element.title)
                if count == 0 and show_fix:
                    self.stdout.write("BEGIN;")
                if show_fix:
                    self.stdout.write("UPDATE survey_question SET"\
" content_id=(SELECT id FROM pages_pageelement WHERE slug='%s')"\
" WHERE path='%s';" % (slug, question.path))
                count += 1
        if count and show_fix:
            self.stdout.write("COMMIT;")
        self.stderr.write("%d questions/element discrepencies" % count)


    def check_answers(self, show=False, show_fix=False):
        """
        Shows all answers which have a duplicate measurement for a triplet
        (unit, sample, question).
        """
        queryset = Answer.objects.order_by('sample__account',
            'sample', 'question', 'unit').values(
            'sample', 'question', 'unit').annotate(Count('id')).filter(
            id__count__gt=1)
        count = queryset.count()
        if show:
            deletes = []
            if count > 0:
                self.stdout.write("count,unit,frozen,sample,account,question")
            for answer in queryset:
                duplicates = Answer.objects.filter(
                    unit=answer['unit'],
                    sample=answer['sample'],
                    question=answer['question']).select_related(
                    'unit', 'question', 'sample__account')
                first = True
                for duplicate in duplicates:
                    self.stdout.write("%s,%s,%s,%s,%s,%s" % (
                        duplicate.pk,
                        duplicate.unit.slug,
                        duplicate.sample.is_frozen,
                        duplicate.sample.id,
                        duplicate.sample.account.slug,
                        duplicate.question.path))
                    if first:
                        first = False
                        continue
                    deletes += [duplicate.pk]
                self.stdout.write("\n")
            if show_fix and deletes:
                self.stdout.write("DELETE FROM survey_answer WHERE id IN (%s);"
                    % ','.join(deletes))
        self.stderr.write(
            "%d answers with same unit in (sample, question) pair" % count)


    def check_duplicate_samples(self, campaign, exclude_units=None,
                                show=False):
        """
        Shows all frozen samples that have the same answers per account
        """
        #pylint:disable=too-many-locals
        if exclude_units:
            exclude_units = Unit.objects.filter(
                slug__in=exclude_units).values_list('pk', flat=True)
        if not isinstance(campaign, Campaign):
            campaign = Campaign.objects.get(slug=str(campaign))
        count = 0
        for account in get_account_model().objects.all().order_by('slug'):
            samples = Sample.objects.filter(
                account=account, campaign=campaign,
                is_frozen=True, extra__isnull=True).order_by(
                'created_at')
            samples_iter = iter(samples)
            try:
                first_sample = next(samples_iter)
            except StopIteration:
                first_sample = None
            try:
                second_sample = next(samples_iter)
            except StopIteration:
                second_sample = None

            while first_sample and second_sample:
                first_answers = Answer.objects.raw(sql_frozen_answers(
                    campaign, [first_sample.pk]))
                second_answers = Answer.objects.raw(sql_frozen_answers(
                    campaign, [second_sample.pk]))
                first_answers_count = len(first_answers)
                second_answers_count = len(second_answers)
                if first_answers_count != second_answers_count:
                    LOGGER.debug("We have %d answers in sample %s"\
                        " and %d answers in sample %s",
                        first_answers_count, first_sample,
                        second_answers_count, second_sample)
                    try:
                        first_sample = next(samples_iter)
                    except StopIteration:
                        first_sample = None
                    try:
                        second_sample = next(samples_iter)
                    except StopIteration:
                        second_sample = None
                    continue

                identical = True
                for first_answer, second_answer in zip(first_answers,
                                                       second_answers):
                    if (exclude_units and
                        first_answer.question_id == second_answer.question_id
                        and first_answer.unit_id == second_answer.unit_id):
                        if first_answer.unit_id in exclude_units:
                            continue
                    if (first_answer.question_id != second_answer.question_id or
                        first_answer.unit_id != second_answer.unit_id or
                        first_answer.measured != second_answer.measured):
                        assert first_answer.question_id is not None
                        assert first_answer.unit_id is not None
                        assert first_answer.measured is not None
                        assert second_answer.question_id is not None
                        assert second_answer.unit_id is not None
                        assert second_answer.measured is not None
                        LOGGER.debug("Answer (%d, %d, %d) in sample %s"\
                            " and answer (%d, %d, %d) in sample %s differ.",
                            first_answer.question_id, first_answer.unit_id,
                            first_answer.measured, first_sample,
                            second_answer.question_id, second_answer.unit_id,
                            second_answer.measured, second_sample)
                        identical = False
                        break
                if identical:
                    if show:
                        self.stdout.write(
                            "samples %s and %s for %s have identical answers."
                            % (first_sample, second_sample, account))
                    count += 1
                    try:
                        second_sample = next(samples_iter)
                    except StopIteration:
                        second_sample = None
                else:
                    try:
                        first_sample = next(samples_iter)
                    except StopIteration:
                        first_sample = None
                    try:
                        second_sample = next(samples_iter)
                    except StopIteration:
                        second_sample = None
        self.stderr.write("%d pair of samples with duplicate answers"\
            " for campaign '%s'" % (count, campaign))
