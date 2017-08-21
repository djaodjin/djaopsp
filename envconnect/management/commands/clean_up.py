# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

"""Command to remove unused questions in the envconnect database"""

import re, sys

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from pages.models import PageElement, RelationShip
from pages.api.relationship import PageElementMirrorAPIView
from survey.models import Question

from ...models import Consumption

INDUSTRIES = [
    'architecture-design',
    'boxes-and-enclosures',
    'construction',
    'consulting',
    'distribution-industry',
    'distribution-transformers',
    'energy-efficiency-contracting',
    'energy-utility',
    'epc',
    'fabricated-metals',
    'facilities-management-industry',
    'freight-and-shipping',
    'fuel-supply',
    'general-contractors',
    'general-manufacturing',
    'interior-design',
    'marketing-and-communications',
    'print-services',
    'office-space-only',
    'vehicle-equipment-and-parts',
    'shipping-and-logistics',
    'wire-and-cable',
]


class BestPracticeUnalias(PageElementMirrorAPIView):

    @staticmethod
    def mirror_leaf(leaf, prefix="", new_prefix=""):
        for consumption in Consumption.objects.filter(path__startswith=prefix):
            new_path = None
            look = re.match(r"^%s/(.*)$" % prefix, consumption.path)
            if look:
                new_path = new_prefix + "/" + look.group(1)
            elif consumption.path == prefix:
                new_path = new_prefix
            if new_path:
                sys.stderr.write("consumption: from %s to %s\n" % (
                    consumption.path, new_path))
                consumption.path = new_path
                consumption.save()
        return leaf


class Command(BaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--delete', action='store_true',
            dest='do_delete', default=False,
            help='When set will also issue the delete query.')

    def handle(self, *args, **options):
        #pylint:disable=too-many-locals
        do_delete = options['do_delete']
        entry_points = INDUSTRIES

        with transaction.atomic():
            self.unalias_headings()

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

    def unalias_headings(self):
        """
        Replace aliased headings by copies.
        """
        unaliases = []
        with connection.cursor() as cursor:
            cursor.execute("""select dest_element_id from (
    select dest_element_id, count(orig_element_id) as cnt from (
        select * from pages_relationship where dest_element_id not in (
            select A.dest_element_id from pages_relationship A
                          left outer join pages_relationship B
                       on A.dest_element_id = B.orig_element_id
        where B.orig_element_id IS NULL)) as headings
        group by dest_element_id)
    as counted where cnt > 1;""")
            for row in cursor.fetchall():
                edges = list(RelationShip.objects.filter(
                    dest_element_id=row[0]))[0:-1]
                self.stdout.write("edges for %d: %s" % (row[0], edges))
                for edge in edges:
                    candidates = edge.dest_element.get_parent_paths(
                        hints=[edge.orig_element.slug])
                    if len(candidates) > 1:
                        prefixes = []
                        for candidate in candidates:
                            prefixes += ["/" + "/".join([
                                node.slug for node in candidate[:-1]])]
                        self.stderr.write("warning: %d candidates for %s (%s)"
                            % (len(prefixes), edge, prefixes))
                        for prefix in prefixes:
                            parts = prefix.split('/')
                            edge = RelationShip.objects.get(
                                orig_element__slug=parts[-2],
                                dest_element__slug=parts[-1])
                            unaliases += [(prefix, edge)]
                    else:
                        prefix = "/" + "/".join([
                            node.slug for node in candidates[0][:-1]])
                        unaliases += [(prefix, edge)]
        for unalias in unaliases:
            edge = unalias[1]
            prefix = unalias[0]
            if not prefix.endswith(edge.dest_element.slug):
                self.stdout.write(
                    "unalias %s/%s" % (prefix, edge.dest_element.slug))
                edge.dest_element = BestPracticeUnalias().mirror_recursive(
                    edge.dest_element, prefix=prefix, new_prefix=prefix)
                edge.save()
