# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

"""Command to remove unused questions in the envconnect database"""

from django.core.management.base import BaseCommand
from django.db import transaction
from pages.models import PageElement
from survey.models import Question

from ...models import Consumption

INDUSTRIES = [
    'boxes-and-enclosures',
    'construction',
    'distribution',
    'distribution-industry',
    'distribution-transformers',
    'energy-efficiency-contracting',
    'energy-utility',
    'fabricated-metals',
    'facilities-management-industry',
    'freight-and-shipping',
    'fuel-supply',
    'general-contractors',
    'general-manufacturing',
    'marketing-and-communications',
    'office-space-only',
    'print-services',
    'shipping-and-logistics',
    'vehicle-equipment-and-parts',
    'wire-and-cable',
]

class Command(BaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--delete', action='store_true',
            dest='do_delete', default=False,
            help='When set will also issue the delete query.')

    def handle(self, *args, **options):
        #pylint:disable=too-many-locals
        do_delete = options['do_delete']
        entry_points = INDUSTRIES \
            + ['basic-%s' % ind for ind in INDUSTRIES]
        roots = PageElement.objects.filter(slug__in=entry_points)
        elements = []
        for node in roots:
            node_path = "/%s" % node.slug
            self.stdout.write("%s\n" % node_path)
            elements += [node_path]
            elements += self.build_tree(node, prefix=node_path)

        with transaction.atomic():
            consumptions_not_linked = Consumption.objects.exclude(
                path__in=elements)
            self.stderr.write("BEGIN;\n")
            self.stderr.write("-- %d consumptions are not linked\n"
                % len(consumptions_not_linked))
            self.stdout.write("DELETE FROM envconnect_consumption"\
                " WHERE question_id in %s;\n" % str(tuple([consumption.pk
                for consumption in consumptions_not_linked])))
            if do_delete:
                consumptions_not_linked.delete()
            questions_not_linked = Question.objects.filter(
                pk__in=[question.pk for question in consumptions_not_linked])
            self.stdout.write("-- %d questions are not linked\n"
                % len(questions_not_linked))
            self.stdout.write("DELETE FROM survey_question WHERE id in %s;\n" %
                str(tuple([question.pk for question in questions_not_linked])))
            if do_delete:
                questions_not_linked.delete()

            # Remove PageElements which are not in entry_points
            pages_not_linked = [page for page in PageElement.objects.get_roots()
                if page.slug not in entry_points]
            self.stdout.write("-- %d pages are not linked\n"
                % len(pages_not_linked))
            self.stdout.write("DELETE FROM pages_pageelement WHERE id in %s;\n"
                % str(tuple([page.pk for page in pages_not_linked])))
            self.stdout.write("COMMIT;\n")
            if do_delete:
                PageElement.objects.filter(
                    pk__in=[page.pk for page in pages_not_linked]).delete()


    def build_tree(self, root, prefix=None, indent=''):
        elements = []
        if prefix is None:
            prefix = "/%s" % root.slug
        for node in root.relationships.all():
            node_path = "%s/%s" % (prefix, node.slug)
            self.stdout.write("%s%s\n" % (indent, node_path))
            elements += [node_path]
            elements += self.build_tree(
                node, prefix=node_path, indent=indent + '  ')
        return elements
