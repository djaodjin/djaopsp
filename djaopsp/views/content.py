# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import json

from deployutils.crypt import JSONEncoder
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_prefixed)
from django.urls import reverse
from django.views.generic import TemplateView
from deployutils.helpers import update_context_urls
from pages.mixins import TrailMixin
from pages.views.editables import PageElementEditableView
from survey.utils import get_question_model


class ContentIndexView(TrailMixin, TemplateView):

    template_name = 'pages/index.html'

    def get_context_data(self, **kwargs):
        context = super(ContentIndexView, self).get_context_data(**kwargs)
#XXX        context.update({
#            'segments': [seg for seg in self.segments_available if seg['path']]
#        })
        update_context_urls(context, {
            'summary_index': reverse('summary_index')
        })
        return context


class ContentDetailView(PageElementEditableView):

    invalid_tiles = ['metrics']

    @property
    def segments_available(self):
        # Used by CampaignContentMixin.get_queryset
        if not hasattr(self, '_segments_available'):
            element = self.element
            element_prefix = self.full_path
            self._segments_available = [{
                'title': element.title,
                'extra': element.extra,
                'path': element_prefix,
                'indent': 0
            }]
        return self._segments_available

    def get_questions(self, prefix):
        # Used by CampaignContentMixin.get_queryset
        if not prefix.endswith(self.DB_PATH_SEP):
            prefix = prefix + self.DB_PATH_SEP
        return [{
            'path': question.get('path'),
            'rank': question.get('enumeratedquestions__rank'),
            'title': question.get('content__title'),
            'picture': question.get('content__picture'),
            'extra': self._as_extra_dict(question.get('content__extra')),
        } for question in get_question_model().objects.filter(
            path__startswith=prefix,
            enumeratedquestions__campaign=self.campaign
        ).values('path', 'enumeratedquestions__rank',
            'content__title', 'content__picture', 'content__extra').order_by(
            'enumeratedquestions__rank')]

    def get(self, request, *args, **kwargs):
        self._start_time()
        result = super(ContentDetailView, self).get(request, *args, **kwargs)
        self._report_queries("View HTML generated.")
        return result

    def get_queryset(self):
        from_root, trail = self.breadcrumbs
        total_score_weight = 0

        queryset = super(ContentDetailView, self).get_queryset()
        elements = self.remove_metrics(queryset)
        self._report_queries("array of content elements to display.")

        tiles = [element for element in elements
            if element.get('indent', 0) == 0]

        for tile in tiles:
            tile_path = "%s/%s" % (from_root, tile['slug'])
            # add the score_weight and percentage to the tile.
            score_weight = self.get_score_weight(tile_path)
            tile['score_weight'] = score_weight
            total_score_weight += score_weight

            # add status of columns
            value_headers = []
            tile['value_headers'] = value_headers
        self._report_queries("attached visiblity of columns.")

        if total_score_weight == 1.0:
            for tile in tiles:
                tile['score_percentage'] = tile.get('score_weight', 0) * 100

        return elements

    def get_context_data(self, **kwargs):
        #pylint:disable=too-many-locals
        context = super(ContentDetailView, self).get_context_data(**kwargs)
        from_root, trail = self.breadcrumbs
        context.update({
            'role': "tab",
            'root': [], # XXX remove and solve {{ root|path_to_legend }}
            'from_root': from_root,
        })

        if not trail:
            # We are the root of the content tree. All bets are off.
            return context

        # attach visible column headers
        urls = {}
        breadcrumbs = context.get('breadcrumbs', [])
        if breadcrumbs:
            content_account_slug = breadcrumbs[-1][0].account.slug
            is_content_manager = self.manages(content_account_slug)
            context.update({
                'edit_perm': is_content_manager,
                'practice': breadcrumbs[-1][0]
            })
            if is_content_manager:
                urls.update({
                    'api_upload_assets': site_prefixed(
                        '/api/auth/tokens/realms/%s/' % content_account_slug)
                })
            prefix = context['root_prefix']
            if prefix.startswith('/'): # XXX should not happen...
                prefix = prefix[1:]
            urls.update({
                'api_best_practices': reverse('pages_api_edit',
                    args=(breadcrumbs[-1][0].account.slug,)),
                'api_page_element_base': reverse(
                    'pages_api_edit_element', args=(
                        breadcrumbs[-1][0].account.slug, prefix,)) if prefix
                else reverse('pages_api_edit',
                    args=(breadcrumbs[-1][0].account.slug,)),
                'api_consumptions': reverse('api_consumption_base',
                    args=(breadcrumbs[-1][0].account.slug,)),
                'api_columns': reverse('api_column', args=('',)),
                'api_weights': reverse('api_score',
                    args=(breadcrumbs[-1][0].account.slug, '')),
            })

        if self.is_prefix:
            # Tiles & practices
            elements = self.get_queryset()
            context.update({
                'elements': json.dumps(elements, indent=2, cls=JSONEncoder),
            })
            self._report_queries("content tree built.")

            # Editor
            #pylint:disable=unused-variable
            segment_url, segment_prefix, segment_element = self.segment
            if segment_url:
                urls.update({
                    'summary_download': reverse('summary_download', args=(
                        segment_url,)),
                })
            urls.update({
                'api_alias_node': reverse('api_alias_node', args=(
                    self.element.account, '')),
                'api_mirror_node': reverse('api_mirror_node', args=(
                    self.element.account, '')),
                'api_move_node': reverse('api_move_node', args=(
                    self.element.account, '')),
            })

        update_context_urls(context, urls)
        return context
