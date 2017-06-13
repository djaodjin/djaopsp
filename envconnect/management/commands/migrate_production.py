# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

"""Command to migrate the envconnect production database"""

import re, sys

from django.core.management.base import BaseCommand
from django.db import transaction
from pages.models import PageElement, RelationShip
from answers.models import Question as AnswersQuestion
from survey.models import (Answer, Question, Response, SurveyModel,
    EditablePredicate)

from ...mixins import BreadcrumbMixin
from ...models import Improvement, Consumption, ScoreWeight, ColumnHeader


class Command(BaseCommand):

    def handle(self, *args, **options):
        with transaction.atomic():
            self.relabel_to_fix_error()

    def relabel_to_fix_error(self):
        old_prefix = '/'
        new_prefix = '/'
        for consumption in Consumption.objects.filter(
            path__startswith=old_prefix):
            self.stdout.write("replace %s by %s" % (old_prefix, new_prefix))
            consumption.path = consumption.path.replace(old_prefix, new_prefix)
            consumption.save()

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

        for weight in ScoreWeight.objects.all():
            self.rename_path(weight)

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



def aggregate_surveys():
    report_title = 'Best Practices Report'
    survey = SurveyModel.objects.filter(
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
                print "warnning: couldn't find PageElement '%s'. "\
                    "Deleting consumption %d" % (last, consumption.pk)
                consumption.delete()

        for answer in Answer.objects.filter(
                question__survey__title=report_title):
            consumption_pk = int(answer.question.text)
            try:
                consumption = Consumption.objects.get(pk=consumption_pk)
                if not Answer.objects.filter(response=answer.response,
                    question=consumption.question).exists():
                    answer.question = consumption.question
                    answer.save()
                else:
                    print "warnning: duplicate answer to Consumption %d. "\
                        "Deleting answer." % consumption_pk
                    answer.delete()
            except Consumption.DoesNotExist:
                print "warnning: couldn't find Consumption %d. "\
                    "Deleting answer." % consumption_pk
                answer.delete()

        for response in Response.objects.filter(survey__title=report_title):
            response.survey = survey
            response.save()
        Improvement.objects.all().delete()
        deprecated_surveys = SurveyModel.objects.filter(
            title=report_title).exclude(pk=survey.pk)
        Question.objects.filter(survey__in=deprecated_surveys).delete()
        deprecated_surveys.delete()


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


def dump_tree(tree, indent=0):
    sys.stdout.write("%s%d | %s\n" % (' ' * indent, tree[0].id, tree[0].title))
    for node in tree[1]:
        dump_tree(node, indent=indent + 2)

def duplicate_tree(tree, suffix, top, industry_slug, path=""):
    if len(tree[1]) == 0:
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
    else:
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
            dest = duplicate_tree(node, suffix, top, industry_slug, path)
            _, _ = RelationShip.objects.get_or_create(
                orig_element=orig, dest_element=dest, tag="")
        return orig


def update_industries():
    #pylint:disable=protected-access
    bcumb = BreadcrumbMixin()
    root = PageElement.objects.get(slug='boxes-and-enclosures')
    tree = bcumb._build_tree(root, path=None, nocuts=True)
    dump_tree(tree)
    for industry in ['distribution-transformers', 'fabricated-metals',
                     'wire-and-cable', 'office-space-only', 'construction']:
        industry_page, _ = PageElement.objects.get_or_create(slug=industry)
        suffix = '-%d' % industry_page.pk
        with transaction.atomic():
            root = duplicate_tree(
                tree, suffix, 'boxes-and-enclosures', industry)
            root.slug = industry
            root.save()
        root_check = PageElement.objects.get(slug=industry)
        tree_check = bcumb._build_tree(root_check, path=None, nocuts=True)
        dump_tree(tree_check)
    for industry in ['construction', 'boxes-and-enclosures',
                     'distribution-transformers', 'fabricated-metals',
                     'wire-and-cable', 'office-space-only']:
        bcumb = BreadcrumbMixin()
        root = PageElement.objects.get(slug=industry)
        tree = bcumb._build_tree(root, path=None, nocuts=True)
        dump_tree(tree)


def update_questions_slug():
    for page in PageElement.objects.all():
        try:
            question = AnswersQuestion.objects.get(pk=page.pk)
            if page.title == question.title:
                question.slug = page.slug
                question.save()
            else:
                print "%d %s (vs. %s)" % (
                    page.pk, question.title, page.title)
        except AnswersQuestion.DoesNotExist:
            print "%d %s does not have an answers.Question" % (
                page.pk, page.title)

