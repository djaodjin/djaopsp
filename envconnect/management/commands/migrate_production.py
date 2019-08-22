# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

"""Command to migrate the envconnect production database"""

import random, re

from deployutils.helpers import datetime_or_now
from django.core.management.base import BaseCommand
from django.db import models, transaction
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils import six
from pages.mixins import TrailMixin
from pages.models import PageElement, RelationShip
from answers.models import Question as AnswersQuestion
from saas.models import Subscription
from saas.utils import generate_random_slug
from survey.models import (Answer, Campaign, EditablePredicate,
    EnumeratedQuestions, Sample)
from survey.utils import get_account_model

from ...api.dashboards import SupplierListBaseAPIView
from ...helpers import freeze_scores, get_testing_accounts
from ...mixins import BreadcrumbMixin, ReportMixin
from ...models import Consumption, ColumnHeader


@python_2_unicode_compatible
class Question(models.Model):

    INTEGER = 'integer'
    RADIO = 'radio'
    DROPDOWN = 'select'
    SELECT_MULTIPLE = 'checkbox'
    TEXT = 'text'

    QUESTION_TYPES = (
            (TEXT, 'text'),
            (RADIO, 'radio'),
            (DROPDOWN, 'dropdown'),
            (SELECT_MULTIPLE, 'Select Multiple'),
            (INTEGER, 'integer'),
    )

    text = models.TextField(help_text="Enter your question here.")
    survey = models.ForeignKey(Campaign, related_name='survey_questions')
    question_type = models.CharField(
        max_length=9, choices=QUESTION_TYPES, default=TEXT,
        help_text="Choose the type of answser.")
    has_other = models.BooleanField(default=False,
        help_text="If checked, allow user to enter a personnal choice."\
" (Don't forget to add an 'Other' choice at the end of your list of choices)")
    choices = models.TextField(blank=True, null=True,
        help_text="Enter choices here separated by a new line."\
" (Only for radio and select multiple)")
    rank = models.IntegerField()
    correct_answer = models.TextField(blank=True, null=True,
        help_text="Enter correct answser(s) here separated by a new line.")
    required = models.BooleanField(default=True,
        help_text="If checked, an answer is required")

    # Fields to merge from Consumption
    requires_measurements = models.BooleanField(default=False)
    environmental_value = models.IntegerField(default=1)
    business_value = models.IntegerField(default=1)
    implementation_ease = models.IntegerField(default=1)
    profitability = models.IntegerField(default=1)
    avg_energy_saving = models.CharField(max_length=50, default="-")
    avg_fuel_saving = models.CharField(max_length=50, default="-")
    capital_cost_low = models.IntegerField(null=True)
    capital_cost_high = models.IntegerField(null=True)
    capital_cost = models.CharField(max_length=50, default="-")
    payback_period = models.CharField(max_length=50, default="-")
    nb_respondents = models.IntegerField(default=0)
    opportunity = models.IntegerField(default=0)
    rate = models.IntegerField(default=0)
    avg_value = models.IntegerField(default=0)

    class Meta:
        unique_together = ('survey', 'rank')
        db_table = 'survey_question'

    def __str__(self):
        return str(self.rank)


class SuppliersAPIView(SupplierListBaseAPIView):

    def _get_filter_out_testing(self):
        return get_testing_accounts()


class Command(BaseCommand):

#    prefix = "ad-"
#    segment = 'architecture-design'
#    prefix = 'co-'
#    segment = 'consulting'
#    prefix = 'id-'
#    segment = 'interior-design'
    prefix = 'mc-'
    segment = 'marketing-and-communications'


    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('paths', metavar='command', nargs='*',
            help="url.path: /sustainability-epc/energy-70a7c33")

    def handle(self, *args, **options):
        with transaction.atomic():
            self.data_import_sql()
#            self.add_root()
#            self.add_grant_key()
#            self.update_pageelement_accounts()
#            self.migrate_survey()
#            self.migrate_completion_status()
#            self.print_updated_scores()
#            self.tag_as_json()
#            self.dump_sql_statements(options.get('paths'))
#            self.relabel_to_fix_error()
#            self.recompute_avg_value()

    def data_import_sql_recursive(self, element, suffix,
                                  path_prefix, new_path_prefix):
        if RelationShip.objects.filter(orig_element=element).exists():
            orig_element_slug = element.slug + suffix
            self.stdout.write("INSERT INTO pages_pageelement (slug, title, text, tag, account_id) VALUES ('%(slug)s', '%(title)s', '%(text)s', '%(tag)s', %(account)d);" % {
            'slug': orig_element_slug,
            'title': element.title,
            'text': element.text,
            'tag': element.tag,
            'account': 6})
            for rel in RelationShip.objects.filter(orig_element=element):
                dest_element_slug = self.data_import_sql_recursive(
                    rel.dest_element, suffix,
                    path_prefix + '/%s' % element.slug,
                    new_path_prefix + '/%s' % orig_element_slug)
                self.stdout.write("INSERT INTO pages_relationship (rank, orig_element_id, dest_element_id) VALUES (%(rank)d, (SELECT id FROM pages_pageelement WHERE slug='%(orig_element_slug)s'), (SELECT id FROM pages_pageelement WHERE slug='%(dest_element_slug)s'));"
                % {'rank': rel.rank,
                   'orig_element_slug': orig_element_slug,
                   'dest_element_slug': dest_element_slug})
        else:
            orig_element_slug = element.slug
            #self.stderr.write("XXX looking for path='%s'" % (path_prefix + '/%s' % orig_element_slug))
            best_practice = Consumption.objects.get(
                path=path_prefix + '/%s' % orig_element_slug)
            new_path = new_path_prefix + '/%s' % orig_element_slug
            self.stdout.write("INSERT INTO survey_question (path, question_type, default_metric_id, title, text, environmental_value, business_value, implementation_ease, profitability, avg_energy_saving, avg_fuel_saving, capital_cost, payback_period, nb_respondents, opportunity, rate, avg_value) VALUES ('%(path)s', '%(question_type)s', %(default_metric_id)d, '', '', 0, 0, 0, 0, '-', '-', '-', '-', 0, 0, 0, 0);" % {
                'path': new_path,
                'question_type': best_practice.question_type,
                'default_metric_id': best_practice.default_metric_id})
            pos = EnumeratedQuestions.objects.get(question=best_practice)
            self.stdout.write("INSERT INTO survey_enumeratedquestions (campaign_id, required, rank, question_id) VALUES (%(campaign_id)d, 0, (SELECT count(id) + 1 FROM survey_enumeratedquestions WHERE campaign_id=%(campaign_id)d), (SELECT id FROM survey_question WHERE path='%(new_path)s'));"% {
                'campaign_id': 1,
                'new_path': new_path})
        return orig_element_slug


    def data_import_sql(self):
        root = PageElement.objects.get(slug='additional-questions')
        path_prefix = '/metal/%s/sustainability-%s' % (
            'boxes-and-enclosures', 'boxes-and-enclosures')
        self.stdout.write("BEGIN;")
        for element in PageElement.objects.filter(slug__in=[
                'construction']):
            orig_element_slug = element.slug
            suffix = '-' + "".join([
                    random.choice("abcdef0123456789") for val in range(5)])
            new_element_slug = self.data_import_sql_recursive(
                root, suffix, path_prefix,
                '/%s/sustainability-%s' % (
                    orig_element_slug, orig_element_slug))
            self.stdout.write("INSERT INTO pages_relationship (rank, orig_element_id, dest_element_id) VALUES ((SELECT count(id) FROM pages_relationship WHERE orig_element_id=(SELECT id FROM pages_pageelement WHERE slug='%(orig_element_slug)s')), (SELECT id FROM pages_pageelement WHERE slug='%(orig_element_slug)s'), (SELECT id FROM pages_pageelement WHERE slug='%(dest_element_slug)s'));"
                % {'orig_element_slug': 'sustainability-%s' % orig_element_slug,
                   'dest_element_slug': new_element_slug})
        self.stdout.write("COMMIT;")

    def add_root(self):
        self.stdout.write("BEGIN;")
        campaign_slug = 'assessment'
        slug = 'energy-utility'
        for question in Consumption.objects.filter(
                path__startswith='/%s/' % slug):
            question_new_path = question.path.replace(
                '/%s/sustainability-%s/' % (slug, slug),
                '/euissca-procurement/sustainability-euissca-procurement/')
            self.stdout.write("INSERT INTO survey_question (path, \"text\", question_type, environmental_value, business_value, implementation_ease, profitability, avg_energy_saving, avg_fuel_saving, capital_cost_low, capital_cost_high, capital_cost, payback_period, nb_respondents, opportunity, rate, avg_value, requires_measurements) VALUES")
            self.stdout.write("('%s', '',"
                    " '%s', %d, %d, %d, %d, '%s', '%s', %d, %d,"\
                    " '%s', '%s', %d, %d, %d, %d, %d);" % (
                    question_new_path,
                    question.question_type,
                    question.environmental_value,
                    question.business_value,
                    question.implementation_ease,
                    question.profitability,
                    question.avg_energy_saving,
                    question.avg_fuel_saving,
                    question.capital_cost_low if question.capital_cost_low else 0,
                    question.capital_cost_high if question.capital_cost_high else 0,
                    question.capital_cost,
                    question.payback_period,
                    question.nb_respondents,
                    question.opportunity,
                    question.rate,
                    question.avg_value,
                    question.requires_measurements
            ))
            enc = EnumeratedQuestions.objects.get(
                campaign__slug=campaign_slug,
                question=question)
            self.stdout.write("INSERT INTO survey_enumeratedquestions (required, campaign_id, question_id, rank) VALUES")
            self.stdout.write("('f', (SELECT id FROM survey_campaign WHERE slug='%s'), (SELECT id FROM survey_question WHERE path='%s'), %d);" % (campaign_slug, question_new_path, enc.rank))
        for slug in ("corporate-shared-services",
                     "electric-procurement",
                     "gas-procurement",
                     "materials-planning-inventory"):
            for question in Consumption.objects.filter(
                    path__startswith='/%s/' % slug):
                question_new_path = question.path.replace(
                    '/%s/' % slug,
                    '/euissca-procurement/sustainability-euissca-procurement/')
                self.stdout.write("INSERT INTO survey_question (path, \"text\", question_type, environmental_value, business_value, implementation_ease, profitability, avg_energy_saving, avg_fuel_saving, capital_cost_low, capital_cost_high, capital_cost, payback_period, nb_respondents, opportunity, rate, avg_value, requires_measurements) VALUES")
                self.stdout.write("('%s', '',"
                    " '%s', %d, %d, %d, %d, '%s', '%s', %d, %d,"\
                    " '%s', '%s', %d, %d, %d, %d, %d);" % (
                    question_new_path,
                    question.question_type,
                    question.environmental_value,
                    question.business_value,
                    question.implementation_ease,
                    question.profitability,
                    question.avg_energy_saving,
                    question.avg_fuel_saving,
                    question.capital_cost_low if question.capital_cost_low else 0,
                    question.capital_cost_high if question.capital_cost_high else 0,
                    question.capital_cost,
                    question.payback_period,
                    question.nb_respondents,
                    question.opportunity,
                    question.rate,
                    question.avg_value,
                    question.requires_measurements
                ))
                enc = EnumeratedQuestions.objects.get(
                    campaign__slug=campaign_slug,
                    question=question)
                self.stdout.write("INSERT INTO survey_enumeratedquestions (required, campaign_id, question_id, rank) VALUES")
                self.stdout.write("('f', (SELECT id FROM survey_campaign WHERE slug='%s'), (SELECT id FROM survey_question WHERE path='%s'), %d);" % (campaign_slug, question_new_path, enc.rank))
        self.stdout.write("COMMIT;")

    def add_grant_key(self):
        self.stdout.write("BEGIN;")
        for subscription in Subscription.objects.filter(
                created_at='2018-08-13 07:54:31.875025-07'):
            self.stdout.write("UPDATE saas_subscription SET grant_key='%s'"\
                " WHERE id=%d;" % (generate_random_slug(), subscription.id))
        self.stdout.write("COMMIT;")


    @staticmethod
    def update_pageelement_accounts():
        with transaction.atomic():
            elems = set([])
            for question in Consumption.objects.filter(
                Q(path__startswith='/energy-utility')
                | Q(path__startswith='/corporate-shared-services')
                | Q(path__startswith='/electric-procurement')
                | Q(path__startswith='/gas-procurement')
                | Q(path__startswith='/materials-planning-inventory')):
                elems |= set(question.path[1:].split('/'))
            PageElement.objects.filter(slug__in=elems).update(account_id=148)

    @staticmethod
    def migrate_completion_status():
        created_at = datetime_or_now()
        with transaction.atomic():
            scores_api = SuppliersAPIView()
            rollup_tree = scores_api.rollup_scores()
            for account in get_account_model().objects.all():
                accounts = rollup_tree[0].get('accounts', {})
                if account.pk in accounts:
                    scores = accounts.get(account.pk, None)
                    if scores:
                        normalized_score = scores.get('normalized_score', None)
                        if normalized_score is not None:
                            sample = Sample.objects.filter(
                                extra__isnull=True,
                                survey__title=ReportMixin.report_title,
                                account=account).order_by('-created_at').first()
                            freeze_scores(sample,
                                includes=[sample],
                                excludes=get_testing_accounts(),
                                created_at=created_at)
                        improvement_score = scores.get(
                            'improvement_score', None)
                        if improvement_score is not None:
                            for sample in Sample.objects.filter(
                                    extra='is_planned',
                                    survey__title=ReportMixin.report_title,
                                    account=account):
                                sample.is_frozen = True
                                sample.save()

    @staticmethod
    def migrate_survey():
        with transaction.atomic():
            for question in Question.objects.all():
                # XXX need `question_id` in Consumption
                consumption = Consumption.objects.get(question_id=question.pk)
                question.requires_measurements = (
                    question.question_type == question.INTEGER)
                question.environmental_value = consumption.environmental_value
                question.business_value = consumption.business_value
                question.implementation_ease = consumption.implementation_ease
                question.profitability = consumption.profitability
                question.avg_energy_saving = consumption.avg_energy_saving
                question.avg_fuel_saving = consumption.avg_fuel_saving
                question.capital_cost_low = consumption.capital_cost_low
                question.capital_cost_high = consumption.capital_cost_high
                question.capital_cost = consumption.capital_cost
                question.payback_period = consumption.payback_period
                question.nb_respondents = consumption.nb_respondents
                question.opportunity = consumption.opportunity
                question.rate = consumption.rate
                question.avg_value = consumption.avg_value
                question.save()
                EnumeratedQuestions.objects.get_or_create(
                    campaign=question.survey,
                    question_id=question.pk,
                    defaults={
                        'rank': question.rank,
                        'required': question.required
                    })

    def print_account_updated_scores(self, account, key, root):
        accounts = root[0].get('accounts', {})
        if account.pk in accounts:
            scores = accounts.get(account.pk, None)
            if scores:
                normalized_score = scores.get('normalized_score', None)
                numerator = scores.get('numerator', None)
                if numerator is not None:
                    numerator = "%.2f" % numerator
                denominator = scores.get('denominator', None)
                if denominator is not None:
                    denominator = "%.2f" % denominator
                weight = root[0].get('score_weight', 1.0)
                if normalized_score is not None:
                    self.stdout.write('%.2f %s %s %.2f "%s" %s' % (
                        normalized_score, numerator, denominator, weight,
                        account.printable_name, key))
        for key, node in six.iteritems(root[1]):
            self.print_account_updated_scores(account, key, node)

    def print_updated_scores(self):
        """
        Displays the scores for each account/scorecard as a text list.
        """
        api = SuppliersAPIView()
        rollup_tree = api.rollup_scores()
        for account in get_account_model().objects.all():
            self.stdout.write('"%s"' % account.printable_name)
            self.print_account_updated_scores(account, "/", rollup_tree)

    def _slugify(self, slug):
        if slug == 'sustainability-office-space-only':
            return 'sustainability-%s' % self.segment
        look = re.match(r'^oso-(.*)', slug)
        if look:
            result = self.prefix + look.group(1)
        else:
            result = self.prefix + slug
        if len(result) > 50:
            result = result[:50]
        return result

    def dump_sql_statements_recursive(self, root):
        slug = self._slugify(root.slug)
        self.stdout.write("INSERT INTO pages_pageelement (slug, text,"\
            " account_id, title, tag) VALUES ('%(slug)s', '%(text)s',"\
            " %(account_id)s, '%(title)s', %(tag)s);" % {
                'slug': slug,
                'text': root.text.replace("'", "''"),
                'account_id': root.account_id,
                'title': root.title,
                'tag': "'%s'" % root.tag if root.tag is not None else "null"})
        orig_element_id = (
            "(SELECT id FROM pages_pageelement WHERE slug='%(slug)s')"
            % {'slug': slug})
        for edge in RelationShip.objects.filter(orig_element=root):
            if RelationShip.objects.filter(
                    orig_element=edge.dest_element).exists():
                self.dump_sql_statements_recursive(edge.dest_element)
                dest_element_slug = self._slugify(edge.dest_element.slug)
                dest_element_id = (
                    "(SELECT id FROM pages_pageelement WHERE slug='%(slug)s')"
                    % {'slug': dest_element_slug})
            else:
                dest_element_id = edge.dest_element_id
            self.stdout.write("INSERT INTO pages_relationship ("\
                " orig_element_id, dest_element_id, tag, rank) VALUES"\
                " (%(orig_element_id)s, %(dest_element_id)s,"\
                " %(tag)s, %(rank)s);" % {
                    'orig_element_id': orig_element_id,
                    'dest_element_id': dest_element_id,
                'tag': "'%s'" % edge.tag if edge.tag is not None else "null",
                    'rank': edge.rank
            })

    def dump_sql_statements(self, paths):
        self.stdout.write("BEGIN;")
        for path in paths:
            trail = TrailMixin.get_full_element_path(path)
            self.dump_sql_statements_recursive(trail[-1])
            self.stdout.write("/* Consumptions */")
            last_rank = Question.objects.aggregate(models.Max('rank')).get(
                'rank__max', 0)
            for consumption in Consumption.objects.filter(
                    path__startswith="/" + "/".join([
                    elem.slug for elem in trail])):
                question = consumption.question
                last_rank = last_rank + 1
                self.stdout.write("INSERT INTO survey_question (text,"\
                    " survey_id, question_type, has_other, choices, rank,"\
                    " correct_answer, required) VALUES (%(text)s,"\
                    " %(survey_id)s, %(question_type)s, %(has_other)s,"\
                    " %(choices)s, %(rank)s, %(correct_answer)s,"\
                    " %(required)s);" % {
                        'text': (("'%s'" % question.text.replace("'", "''"))
                            if question.text is not None else "null"),
                        'survey_id': question.survey_id,
                        'question_type':  "'%s'" % (question.question_type
                            if question.question_type is not None else "null"),
                        'has_other': "'t'" if question.has_other else "'f'",
                        'choices': "'%s'" % (question.choices
                            if question.choices is not None else "null"),
                        'rank': last_rank,
                        'correct_answer': "'%s'" % (question.correct_answer
                            if question.correct_answer is not None else "null"),
                        'required': "'t'" if question.required else "'f'",
                    })
                question_id = (
                    "(SELECT id FROM survey_question WHERE rank=%(rank)s)"
                    % {'rank': last_rank})
                parts = consumption.path.split('/')
                prefixed_parts = [""]
                prefixed_parts += [self.segment]
                prefixed_parts += ['sustainability-%s' % self.segment]
                for part in parts[3:-1]:
                    prefixed_parts += [self._slugify(part)]
                prefixed_parts += [parts[-1]]
                path = '/'.join(prefixed_parts)
                self.stdout.write("INSERT INTO envconnect_consumption ("\
                    " avg_energy_saving, capital_cost_low, capital_cost_high,"\
                    " payback_period, reported_by, avg_fuel_saving,"\
                    " environmental_value, business_value,"\
                    " implementation_ease, profitability, path,"\
                    " capital_cost,  question_id,  opportunity,"\
                    "  avg_value) VALUES ('%(avg_energy_saving)s',"\
                    " %(capital_cost_low)s, %(capital_cost_high)s,"\
                    " '%(payback_period)s', %(reported_by)s,"\
                    " '%(avg_fuel_saving)s', %(environmental_value)s,"\
                    " %(business_value)s, %(implementation_ease)s,"\
                    " %(profitability)s, '%(path)s', '%(capital_cost)s',"\
                    " %(question_id)s, %(opportunity)s, %(avg_value)s);" % {
                        'avg_energy_saving': consumption.avg_energy_saving,
            'capital_cost_low': (("'%s'" % consumption.capital_cost_low)
                if consumption.capital_cost_low is not None else "null"),
            'capital_cost_high': (("'%s'" % consumption.capital_cost_high)
                if consumption.capital_cost_high is not None else "null"),
            'payback_period': consumption.payback_period,
            'reported_by': (("'%s'" % consumption.reported_by)
                if consumption.reported_by is not None else "null"),
            'avg_fuel_saving': consumption.avg_fuel_saving,
            'environmental_value': consumption.environmental_value,
            'business_value': consumption.business_value,
            'implementation_ease': consumption.implementation_ease,
            'profitability': consumption.profitability,
            'path': path,
            'capital_cost': consumption.capital_cost,
            'question_id': question_id,
            'opportunity': consumption.opportunity,
            'avg_value': consumption.avg_value
                })
        self.stdout.write("COMMIT;")

    @staticmethod
    def recompute_avg_value():
        # Force save to trigger recomputing of `avg_value`
        for consumption in Consumption.objects.all():
            consumption.avg_value = 0
            consumption.save()

    def relabel_to_fix_error(self):
        old_prefix = '/'
        new_prefix = '/'
        for consumption in Consumption.objects.filter(
            path__startswith=old_prefix):
            self.stdout.write("replace %s by %s" % (old_prefix, new_prefix))
            consumption.path = consumption.path.replace(old_prefix, new_prefix)
            consumption.save()
        for predicate in EditablePredicate.objects.filter(
            operand__startswith=old_prefix):
            self.stdout.write("(predicate) replace %s by %s" % (
                old_prefix, new_prefix))
            predicate.operand = predicate.operand.replace(
                old_prefix, new_prefix)
            predicate.save()

    def rename_consumption(self):
        for element in PageElement.objects.filter(
                tag__contains='industry').exclude(
                slug__startswith='basic-'):
            self.stdout.write("Add root for '%s'\n" % element.slug)
            try:
                basic_element = PageElement.objects.get(
                    slug='basic-%s' % element.slug)
                basic_element.tag = 'basic'
                basic_element.save()
            except PageElement.DoesNotExist:
                basic_element = None
            root = PageElement(
                slug=element.slug,
                title=element.title,
                text=element.text,
                account=element.account,
                tag=element.tag)
            element.slug = "sustainability-%s" % element.slug
            element.tag = 'sustainability'
            element.save()
            root.save()
            if basic_element:
                RelationShip.objects.create(
                    orig_element=root,
                    dest_element=basic_element,
                    rank=0)
            RelationShip.objects.create(
                orig_element=root,
                dest_element=element,
                rank=1)

        for consumption in Consumption.objects.all():
            self.rename_path(consumption)

        for colheader in ColumnHeader.objects.all():
            self.rename_path(colheader)

        for predicate in EditablePredicate.objects.all():
            self.rename_operand(predicate)

    def rename_path(self, obj):
        parts = []
        path = obj.path
        if path.startswith('/'):
            parts = path[1:].split('/')
        else:
            parts = path.split('/')
        look = re.match('^basic-(.*)', parts[0])
        if look:
            obj.path = '/'.join(
                ['', look.group(1), parts[0]] + parts[1:])
        else:
            obj.path = '/'.join(
                ['', parts[0], "sustainability-%s" % parts[0]] + parts[1:])
        self.stdout.write(
            "Rename '%s' to '%s'\n" % (path, obj.path))
        obj.save()

    def rename_operand(self, obj):
        parts = []
        path = obj.operand
        if path.startswith('/'):
            parts = path[1:].split('/')
        else:
            parts = path.split('/')
        look = re.match('^basic-(.*)', parts[0])
        if look:
            obj.operand = '/'.join(
                ['', look.group(1), parts[0]] + parts[1:])
        else:
            obj.operand = '/'.join(
                ['', parts[0], "sustainability-%s" % parts[0]] + parts[1:])
        self.stdout.write(
            "Rename '%s' to '%s'\n" % (path, obj.operand))
        obj.save()

    def aggregate_surveys(self):
        report_title = 'Best Practices Report'
        survey = Campaign.objects.filter(
            title=report_title).order_by('pk').first()

        with transaction.atomic():
            for idx, consumption in enumerate(list(Consumption.objects.all())):
                last = consumption.path.split('/')[-1]
                try:
                    element = PageElement.objects.get(slug=last)
                    question = Question.objects.create(
                        survey=survey, text=element.title, rank=idx)
                    consumption.question = question
                    consumption.save()
                except PageElement.DoesNotExist:
                    self.stderr.write(
                        "warnning: couldn't find PageElement '%s'. "\
                        "Deleting consumption %d\n" % (last, consumption.pk))
                    consumption.delete()

            for answer in Answer.objects.filter(
                    question__survey__title=report_title):
                consumption_pk = int(answer.question.text)
                try:
                    consumption = Consumption.objects.get(pk=consumption_pk)
                    if not Answer.objects.filter(sample=answer.sample,
                        question=consumption.question).exists():
                        answer.question = consumption.question
                        answer.save()
                    else:
                        self.stderr.write(
                            "warnning: duplicate answer to Consumption %d. "\
                            "Deleting answer.\n" % consumption_pk)
                        answer.delete()
                except Consumption.DoesNotExist:
                    self.stderr.write(
                        "warnning: couldn't find Consumption %d. "\
                        "Deleting answer.\n" % consumption_pk)
                    answer.delete()

            for sample in Sample.objects.filter(
                    extra__isnull=True, survey__title=report_title):
                sample.survey = survey
                sample.save()
            deprecated_surveys = Campaign.objects.filter(
                title=report_title).exclude(pk=survey.pk)
            Question.objects.filter(survey__in=deprecated_surveys).delete()
            deprecated_surveys.delete()

    @staticmethod
    def update_capital_cost():
        with transaction.atomic():
            for obj in Consumption.objects.all():
                result = '-'
                if (obj.capital_cost_low is not None
                    and obj.capital_cost_high is not None):
                    if obj.capital_cost_low < 0:
                        result = '$' * abs(obj.capital_cost_low)
                    elif obj.capital_cost_low == \
                        obj.capital_cost_high and \
                        obj.capital_cost_high > 0:
                        result = '$' + str(obj.capital_cost_high)
                    elif obj.capital_cost_low == \
                        obj.capital_cost_high and \
                        obj.capital_cost_high < 0:
                        result = '-'
                    elif obj.capital_cost_low != \
                        obj.capital_cost_high:
                        result = '$' + str(obj.capital_cost_low) + '-' + \
                            '$' + str(obj.capital_cost_high)
                    elif obj.capital_cost_low == 0 and \
                        obj.capital_cost_high > 0:
                        result = '$' + str(obj.capital_cost_high)
                obj.capital_cost = result
                obj.save()

    def dump_tree(self, tree, indent=0):
        self.stdout.write(
            "%s%d | %s\n" % (' ' * indent, tree[0].id, tree[0].title))
        for node in tree[1]:
            self.dump_tree(node, indent=indent + 2)

    def duplicate_tree(self, tree, suffix, top, industry_slug, path=""):
        #pylint:disable=too-many-arguments
        if not tree[1]:
            # We are at the bottom. Link instead of duplicate.
            path = "%s/%s" % (path, tree[0].slug)
            try:
                consumption = Consumption.objects.get(
                    practice=tree[0], industry__slug=industry_slug)
                consumption.path = path
                consumption.save()
            except Consumption.DoesNotExist:
                Consumption.objects.create(path=path, practice=tree[0])
            return tree[0]
        if tree[0].slug == top:
            # Re-use top level industry
            orig, _ = PageElement.objects.get_or_create(slug=industry_slug)
        else:
            slug = tree[0].slug + suffix
            if len(slug) > 50:
                slug = tree[0].slug[:-(len(slug) - 50)] + suffix
            orig, _ = PageElement.objects.get_or_create(
                slug=slug, title=tree[0].title, text=tree[0].text,
                tag=tree[0].tag)
        path = "%s/%s" % (path, orig.slug)
        for node in tree[1]:
            dest = self.duplicate_tree(
                node, suffix, top, industry_slug, path)
            _, _ = RelationShip.objects.get_or_create(
                orig_element=orig, dest_element=dest, tag="")
        return orig

    def update_industries(self):
        #pylint:disable=protected-access
        bcumb = BreadcrumbMixin()
        root = PageElement.objects.get(slug='boxes-and-enclosures')
        tree = bcumb._build_tree(root, path=None, cut=None)
        self.dump_tree(tree)
        for industry in ['distribution-transformers', 'fabricated-metals',
                         'wire-and-cable', 'office-space-only', 'construction']:
            industry_page, _ = PageElement.objects.get_or_create(slug=industry)
            suffix = '-%d' % industry_page.pk
            with transaction.atomic():
                root = self.duplicate_tree(
                    tree, suffix, 'boxes-and-enclosures', industry)
                root.slug = industry
                root.save()
            root_check = PageElement.objects.get(slug=industry)
            tree_check = bcumb._build_tree(root_check, path=None, cut=None)
            self.dump_tree(tree_check)
        for industry in ['construction', 'boxes-and-enclosures',
                         'distribution-transformers', 'fabricated-metals',
                         'wire-and-cable', 'office-space-only']:
            bcumb = BreadcrumbMixin()
            root = PageElement.objects.get(slug=industry)
            tree = bcumb._build_tree(root, path=None, cut=None)
            self.dump_tree(tree)

    def update_questions_slug(self):
        for page in PageElement.objects.all():
            try:
                question = AnswersQuestion.objects.get(pk=page.pk)
                if page.title == question.title:
                    question.slug = page.slug
                    question.save()
                else:
                    self.stderr.write("%d %s (vs. %s)\n" % (
                        page.pk, question.title, page.title))
            except AnswersQuestion.DoesNotExist:
                self.stderr.write(
                    "%d %s does not have an answers.Question\n" % (
                    page.pk, page.title))
