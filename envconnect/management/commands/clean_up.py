# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

"""Command to remove unused questions in the envconnect database"""

from django.core.management.base import BaseCommand
from pages.models import PageElement
from survey.models import Question

from ...models import Consumption

INDUSTRIES = [
    'boxes-and-enclosures',
    'construction',
    'distribution',
    'distribution-transformers',
    'fabricated-metals',
    'wire-and-cable',
    'diversified-corporate-level',
    'office-space-only',
    'fuel-supply',
    'shipping-and-logistics',
    'vehicle-equipment-and-parts',
]

class Command(BaseCommand):

    def handle(self, *args, **options):
        entry_points = INDUSTRIES \
            + ['basic-%s' % ind for ind in INDUSTRIES]
        roots = PageElement.objects.filter(slug__in=entry_points)
        elements = []
        for node in roots:
            node_path = "/%s" % node.slug
            self.stdout.write("%s\n" % node_path)
            elements += [node_path]
            elements += self.build_tree(node, prefix=node_path)

        consumptions_not_linked = Consumption.objects.exclude(path__in=elements)
        self.stdout.write(
            "%d consumptions are not linked" % len(consumptions_not_linked))
        consumptions_not_linked.delete()
        questions_not_linked = Question.objects.filter(
            pk__in=[question.pk for question in consumptions_not_linked])
        self.stdout.write(
            "%d questions are not linked" % len(questions_not_linked))

        # Remove PageElements which are not in entry_points
        pages_not_linked = [page for page in PageElement.objects.get_roots()
            if page.slug not in entry_points]
        self.stdout.write(
            "%d pages are not linked" % len(pages_not_linked))
        for page in pages_not_linked:
            self.stdout.write("DELETE %s\n" % page)
            page.delete()


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
