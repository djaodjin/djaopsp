# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

"""Command to add a top level root element"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.template.defaultfilters import slugify
from survey.models import EditableFilter, EditablePredicate, Matrix
from survey.utils import get_account_model


class Command(BaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--slug', action='store',
            dest='slug', default=None,
            help='Slug to associate with the top-level element')
        parser.add_argument('title', metavar='title', default=None,
            help="Title for the root element.")

    def handle(self, *args, **options):
        title = options['title']
        slug = options['slug']
        if not slug:
            slug = slugify(title)
        with transaction.atomic():
            metric = EditableFilter.objects.create(
                slug=slug, title=title, tags='metric')
            EditablePredicate.objects.create(
                rank=1, editable_filter=metric,
                operator='startsWith', field='path', selector='keepmatching',
                operand='/%(slug)s/sustainability-%(slug)s' % {'slug': slug})
            matrix = Matrix.objects.create(slug=slug, title=title,
                metric=metric, account=get_account_model().objects.get(
                    slug=settings.APP_NAME))
            cohort = EditableFilter.objects.create(
                slug="%s-1" % slug, title=title, tags='cohort')
            EditablePredicate.objects.create(
                rank=1, editable_filter=cohort,
                operator='contains', field='extra', selector='keepmatching',
                operand='"%(slug)s"' % {'slug': slug})
            matrix.cohorts.add(cohort)
