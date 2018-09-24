# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

"""Command to remove unused questions in the envconnect database"""

import re, sys

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.utils import six
from pages.models import PageElement, RelationShip
from pages.api.relationship import PageElementMirrorAPIView
from survey.models import Matrix

from ...models import Consumption

INDUSTRIES = [
    'architecture-design',
    'aviation-services',
    'boxes-and-enclosures',
    'construction',
    'consulting',
    'corporate-shared-services',
    'distribution-industry',
    'distribution-transformers',
    'ecec',
    'electric-procurement',
    'energy-efficiency-contracting',
    'energy-utility',
    'engineering',
    'epc',
    'fabricated-metals',
    'facilities',
    'facilities-management-industry',
    'freight-and-shipping',
    'fuel-supply',
    'gas-procurement',
    'general-contractors',
    'general-manufacturing',
    'interior-design',
    'lab-services',
    'marketing-and-communications',
    'materials-planning-inventory',
    'metal',
    'office-space-only',
    'print-services',
    'shipping-and-logistics',
    'vegetation-industry',
    'vehicle-equipment-and-parts',
    'waste-industry',
    'wire-and-cable',
    # Important pages which are not part of the sustainability content
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
#        with transaction.atomic():
#            self.copy_reference_values()
#        with transaction.atomic():
#            self.unalias_headings()
        self.delete_ghosts(do_delete=options['do_delete'])
        self.create_missing_graphs()

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

    def copy_reference_values(self):
        for prefix, icon in [
        # Architectural design > Electricity/gas
    ('/architecture-design/sustainability-architecture-design/ad-electricity/',
     'Electricity/gas'),
        # Architectural design > Fuel
    ('/architecture-design/sustainability-architecture-design/ad-transport/',
     'Fuel'),
        # Architectural design > Waste/pollution
    ('/architecture-design/sustainability-architecture-design/ad-waste/',
     'Waste/pollution'),
        # Architectural design > Water
    ('/architecture-design/sustainability-architecture-design/ad-water/',
     'Water'),
        # Construction > Procurement
    ('/construction/sustainability-construction/procurement-5d484d5/',
     'Procurement'),
        # Construction > Construction
    ('/construction/sustainability-construction/construction-bbec85a/',
     'Construction'),
        # Distribution > Warehouse facilities
    ('/distribution-industry/sustainability-distribution-industry/'\
    'warehouse-facilities',
     'Warehouse facilities'),
        # Distribution > Distribution & shipping
        #       (to Distribution & shipping, Shipping)
    ('/distribution-industry/sustainability-distribution-industry/'\
    'fleet-distribution',
     'Distribution & shipping'),
    ('/distribution-industry/sustainability-distribution-industry/'\
    'fleet-distribution',
     'Shipping'),
        ]:
            for reference in Consumption.objects.filter(
                    path__startswith=prefix):
                parts = reference.path.split('/')
                base_breadcrumbs = []
                for part in parts[1:]:
                    base_breadcrumbs += [
                        PageElement.objects.get(slug=part).title]
                base = PageElement.objects.get(slug=parts[-1])
                for element in PageElement.objects.filter(title=base.title):
                    for candidate in element.get_parent_paths():
                        breadcrumbs = [item.title for item in candidate]
                        if icon in breadcrumbs:
                            path = '/' + '/'.join(
                                [item.slug for item in candidate])
                            if not path.startswith(prefix):
                                self.stdout.write("From %s\n  To %s" % (
                                    " > ".join(base_breadcrumbs),
                                    " > ".join(
                                        [item.title for item in candidate])))
                                consumption = Consumption.objects.get(path=path)
                                consumption.environmental_value = \
                                    reference.environmental_value
                                consumption.business_value = \
                                    reference.business_value
                                consumption.implementation_ease = \
                                    reference.implementation_ease
                                consumption.profitability = \
                                    reference.profitability
                                consumption.avg_value = reference.avg_value
                                consumption.save()

    def create_missing_graphs(self):
        matrices = dict([(matrix.slug, matrix)
            for matrix in Matrix.objects.all()])
        for element in PageElement.objects.filter(
                tag__contains='industry'):
            candidates = element.get_parent_paths()
            if not candidates:
                raise RuntimeError(
                    "could not find path to '%s'." % element.slug)
            for candidate in candidates:
                key = element.slug
                if key.startswith('sustainability-'):
                    key = key[len('sustainability-'):]
                if key in matrices:
                    del matrices[key]
                else:
                    self.stderr.write("error: cannot find matrix for /%s in:"
                        % '/'.join([elem.slug for elem in candidate]))
                    for matrix_key in six.iterkeys(matrices):
                        self.stderr.write("        - %s" % matrix_key)
                    self.stdout.write(
"""
INSERT INTO survey_editablefilter (slug, title, tags) VALUES
    ('%(slug)s', '%(title)s', 'metric');
INSERT INTO survey_editablepredicate (rank, editable_filter_id, operator,
    field, selector, operand) VALUES
    (1, (select id from survey_editablefilter where slug='%(slug)s'),
    'startsWith', 'path', 'keepmatching', '/%(slug)s/sustainability-%(slug)s');
INSERT INTO survey_matrix (slug, title, metric_id, account_id) VALUES
    ('%(slug)s', '%(title)s',
    (SELECT id FROM survey_editablefilter WHERE slug='%(slug)s'),
    (SELECT id FROM saas_organization WHERE slug='envconnect'));
""" % {'slug': element.slug, 'title': element.title})
        for matrix_key in six.iterkeys(matrices):
            self.stderr.write("warning: extra matrix '%s'" % matrix_key)

    def delete_ghosts(self, do_delete=False):
        #pylint:disable=too-many-locals
        entry_points = INDUSTRIES
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
            self.stdout.write("DELETE FROM survey_question"\
                " WHERE id in %s;\n" % str(tuple([consumption.pk
                for consumption in consumptions_not_linked])))
            if do_delete:
                consumptions_not_linked.delete()

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
