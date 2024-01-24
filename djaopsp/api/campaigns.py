# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

import csv, json
from collections import OrderedDict

from django.db import transaction
from django.db.models import Max
from pages.api.elements import (PageElementEditableListAPIView,
    PageElementEditableDetail)
from pages.docs import extend_schema
from pages.mixins import TrailMixin
from pages.models import PageElement, RelationShip, flatten_content_tree
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from survey.mixins import QuestionMixin
from survey.models import EnumeratedQuestions
from survey.utils import get_question_model, get_question_serializer
from survey.settings import DB_PATH_SEP

from .serializers import ContentNodeSerializer, CreateContentElementSerializer
from ..campaigns import import_campaign
from ..compat import six
from ..mixins import CampaignMixin


class CampaignContentMixin(CampaignMixin):
    """
    Queryset to present practices in 2d matrix of segments and tiles.
    """
    strip_segment_prefix = False

    def get_questions(self, prefix):
        return [{
            'path': question.get('path'),
            'rank': question.get('enumeratedquestions__rank'),
            'default_unit': question.get('default_unit__slug'),
            'title': question.get('content__title'),
            'picture': question.get('content__picture'),
            'extra': self._as_extra_dict(question.get('content__extra')),
        } for question in get_question_model().objects.filter(
            path__startswith=prefix,
            enumeratedquestions__campaign=self.campaign
        ).values('path', 'enumeratedquestions__rank', 'default_unit__slug',
            'content__title', 'content__picture', 'content__extra').order_by(
            'enumeratedquestions__rank')]

    @staticmethod
    def _as_extra_dict(extra):
        try:
            extra = json.loads(extra)
        except (TypeError, ValueError):
            extra = {}
        return extra

    def get_queryset(self):
        #pylint:disable=too-many-locals,too-many-statements
        segments = self.sections_available
        by_tiles = OrderedDict()
        if self.kwargs.get(self.path_url_kwarg):
            strip_segment_prefix = True
        else:
            strip_segment_prefix = self.strip_segment_prefix
        for segment in segments:
            segment_prefix = segment['path']
            extra = segment.get('extra', {})
            pagebreak = extra.get('pagebreak', False) if extra else False
            if segment_prefix and pagebreak:
                queryset = self.get_questions(segment_prefix)
                for question in queryset:
                    path = question.get('path')
                    path = path[len(segment_prefix):]
                    parts = path.strip(DB_PATH_SEP).split(DB_PATH_SEP)
                    if strip_segment_prefix:
                        prefix = ''
                    else:
                        segment_prefix_parts = segment_prefix.strip(
                            DB_PATH_SEP).split(DB_PATH_SEP)
                        prefix = DB_PATH_SEP.join(
                            segment_prefix_parts[:-1])
                        if prefix:
                            prefix = DB_PATH_SEP + prefix
                        parts = [segment_prefix_parts[-1]] + parts
                    practices = by_tiles
                    for part in parts[:-1]:
                        prefix = DB_PATH_SEP.join([prefix, part])
                        if prefix not in practices:
                            practices[prefix] = ({
                                'slug': part,
                            }, OrderedDict())
                        extra = practices[prefix][0].get('extra', {})
                        segments = extra.get('segments', [])
                        extra.update({'segments': list(set(segments + [
                            segment_prefix]))})
                        if 'extra' not in practices[prefix][0]:
                            practices[prefix][0].update({'extra': extra})
                        practices = practices[prefix][1]
                    part = parts[-1]
                    prefix = DB_PATH_SEP.join([prefix, part])
                    if prefix not in practices:
                        if not ('title' in question and
                                'picture' in question and
                                'extra' in question):
                            element = PageElement.objects.filter(
                                slug=part).values(
                                'title', 'picture', 'extra').first()
                            # `rank` is aldready set in the `question` dict
                            # as it is critical it is unique accross radio
                            # buttons presented to the request.user.
                            question.update({
                                'title': element.get('title'),
                                'picture': element.get('picture'),
                                'extra': self._as_extra_dict(
                                    element.get('extra')),
                            })
                        question.update({
                            'slug': part,
#                            'url': reverse('campaign_practice_detail',
#                                args=(self.account, self.campaign,
#                                    prefix[1:] if (prefix and
#                                    prefix.startswith('/')) else prefix))
                        })
                        practices[prefix] = (question, OrderedDict())
                    extra = practices[prefix][0].get('extra', {})
                    segments = extra.get('segments', [])
                    extra.update({'segments': list(set(segments + [
                        segment_prefix]))})
                    if 'extra' not in practices[prefix][0]:
                        practices[prefix][0].update({'extra': extra})

        # Adds 'text' summaries for top-level tiles
        summaries = PageElement.objects.filter(slug__in={val[0].get('slug')
            for val in six.itervalues(by_tiles)}).values('slug', 'text')
        for summary in summaries:
            key = "%s%s" % (DB_PATH_SEP, summary.get('slug'))
            text = summary.get('text')
            if key in by_tiles:
                by_tiles[key][0].update({'text': text})

        elements = flatten_content_tree(by_tiles, sort_by_key=False)
        headings = [element['slug'] for element in elements
            if 'title' not in element]

        headings_queryset = PageElement.objects.filter(
            slug__in=headings).values(
                'slug', 'title', 'picture', 'extra').annotate(
                    rank=Max('to_element__rank'))
        headings_by_slug = {
            element['slug']: {
                'title': element['title'],
                'picture': element['picture'],
                'rank': element['rank'],
                'extra': self._as_extra_dict(element['extra'])
            } for element in headings_queryset}
        for element in elements:
            slug = element.get('slug')
            if slug:
                merged_fields = headings_by_slug.get(slug, {})
                if 'extra' in merged_fields:
                    merged_fields['extra'].update(element.get('extra', {}))
                element.update(merged_fields)
        campaign_slug = self.campaign.slug
        campaign_path = "%s%s" % (DB_PATH_SEP, campaign_slug)
        for seg_path, seg_val in six.iteritems(by_tiles):
            if seg_path == campaign_path:
                seg_val[0].update({'rank': -1})
                break
        elements = flatten_content_tree(by_tiles)
        return elements


class CampaignEditableSegmentsAPIView(CampaignContentMixin,
                                      PageElementEditableListAPIView):

    serializer_class = ContentNodeSerializer

    def get(self, request, *args, **kwargs):
        """
        List segments in a campaign

        **Tags**: editors

        **Examples

        .. code-block:: http

            GET /api/editables/alliance/campaigns/sustainability/segments\
     HTTP/1.1

        responds

        .. code-block:: json

            {
                "count": 5,
                "next": null,
                "previous": null,
                "results": [
                    {
                      "path": null,
                      "title": "Construction",
                      "tags": ["public"],
                      "indent": 0
                    },
                    {
                      "path": null,
                      "title": "Governance & management",
                      "picture": "https://assets.tspproject.org/management.png",
                      "indent": 1
                    },
                    {
                        "path": "/construction/governance/the-assessment\
    -process-is-rigorous",
                        "title": "The assessment process is rigorous",
                        "indent": 2
                    },
                    {
                      "path": null,
                      "title": "Production",
                      "picture": "https://assets.tspproject.org/production.png",
                      "indent": 1
                    },
                    {
                        "path": "/construction/production/adjust-air-fuel\
    -ratio",
                        "title": "Adjust Air fuel ratio",
                        "indent": 2
                    }
                ]
            }
        """
        segments = self.sections_available
        serializer = self.get_serializer(segments, many=True)
        return Response({'results': serializer.data})

    def post(self, request, *args, **kwargs):
        """
        Creates a segment in a campaign

        **Tags: editors

        **Example

        .. code-block:: http

            POST /api/editables/alliance/campaigns/sustainability\
/segments HTTP/1.1

        .. code-block:: json

            {
                "title": "Boxes enclosures"
            }

        responds

        .. code-block:: json

            {
                "slug": "boxes-enclosures"
            }

        """
        #pylint:disable=useless-super-delegation
        return super(CampaignEditableSegmentsAPIView, self).post(
            request, *args, **kwargs)


class CampaignEditableContentAPIView(CampaignContentMixin,
                                     PageElementEditableListAPIView):

    serializer_class = ContentNodeSerializer
    strip_segment_prefix = True

    def get_serializer_class(self):
        if self.request.method.lower() == 'post':
            return CreateContentElementSerializer
        return super(
            CampaignEditableContentAPIView, self).get_serializer_class()

    def get(self, request, *args, **kwargs):
        """
        List questions in a campaign

        **Tags**: editors

        **Examples

        .. code-block:: http

            GET /api/editables/djaopsp/campaigns/sustainability HTTP/1.1

        responds

        .. code-block:: json

            {
                "count": 5,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "path": null,
                        "title": "Construction",
                        "tags": ["public"],
                        "indent": 0
                    },
                    {
                      "path": null,
                      "title": "Governance & management",
                      "picture": "https://assets.tspproject.org/management.png",
                      "indent": 1
                    },
                    {
                        "path": "/construction/governance/the-assessment\
    -process-is-rigorous",
                        "title": "The assessment process is rigorous",
                        "indent": 2
                    },
                    {
                      "path": null,
                      "title": "Production",
                      "picture": "https://assets.tspproject.org/production.png",
                      "indent": 1
                    },
                    {
                        "path": "/construction/production/adjust-air-fuel\
    -ratio",
                        "title": "Adjust Air fuel ratio",
                        "indent": 2
                    }
                ]
            }
        """
        results = self.get_queryset()
        serializer = self.get_serializer(results, many=True)
        return Response({'results': serializer.data})

    @extend_schema(operation_id='editables_campaigns_create_index')
    def post(self, request, *args, **kwargs):
        """
        Creates a practice

        Updates the title, text and, if applicable, the metrics associated
        associated to the content element referenced by *path*.

        **Tags**: editors

        **Examples

        .. code-block:: http

            POST /api/editables/alliance/campaigns/sustainability \
 HTTP/1.1

        .. code-block:: json

            {
              "title": "Adjust air/fuel ratio",
              "parents": []
            }

        responds:

        .. code-block:: json

            {
              "title": "Adjust air/fuel ratio",
              "parents": []
            }

        """
        #pylint:disable=useless-super-delegation
        return super(CampaignEditableContentAPIView, self).post(
            request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        #pylint:disable=too-many-locals
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            parent = None
            parents = serializer.validated_data.pop('parents', [])
            if not self.path:
                # We don't have a path so let's create one
                # from the segment and tile.
                if len(parents) < 2:
                    raise ValidationError({'parents':
                        "Requires at least a segment and a tile"})
                grand_parent = None
                for part in parents:
                    grand_parent = parent
                    slug = part.get('slug')
                    if slug:
                        parent = get_object_or_404(PageElement.objects.all(),
                            account=self.account, slug=slug)
                    else:
                        parent = PageElement.objects.create(
                            account=self.account,
                            title=part.get('title'),
                            extra=json.dumps({"pagebreak":True})
                              if not grand_parent else None)
                    if grand_parent:
                        rank = RelationShip.objects.filter(
                            orig_element=grand_parent).aggregate(
                                Max('rank')).get('rank__max', None)
                        rank = 0 if rank is None else rank + 1
                        RelationShip.objects.get_or_create(
                            orig_element=grand_parent, dest_element=parent,
                            defaults={'rank': rank})
            else:
                parent = self.element

            # We are guarenteed to have a valid parent to attach the element
            # in the content DAG at this point.
            element = serializer.save(account=self.account)
            rank = RelationShip.objects.filter(orig_element=parent).aggregate(
                Max('rank')).get('rank__max', None)
            rank = 0 if rank is None else rank + 1
            RelationShip.objects.create(
                orig_element=parent, dest_element=element, rank=rank)

            # Add the question in each segment that references the tile.
            campaign = self.campaign
            rank = EnumeratedQuestions.objects.filter(
                campaign=campaign).aggregate(
                Max('rank')).get('rank__max', None)
            rank = 0 if rank is None else rank + 1
            for prefix_parts in parent.get_parent_paths():
                rank = rank + 1
                path = DB_PATH_SEP + DB_PATH_SEP.join([
                    part.slug for part in prefix_parts] + [element.slug])
                question = get_question_model().objects.create(
                    path=path, content=element)
                EnumeratedQuestions.objects.get_or_create(
                    campaign=campaign, question=question, rank=rank)

        serializer_class = super(
            CampaignEditableContentAPIView, self).get_serializer_class()
        #pylint:disable=not-callable
        serializer = serializer_class(instance=element)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data,
            status=status.HTTP_201_CREATED, headers=headers)


class CampaignUploadAPIView(CampaignContentMixin, TrailMixin,
                            generics.CreateAPIView):

    serializer_class = ContentNodeSerializer
    strip_segment_prefix = True

    def post(self, request, *args, **kwargs):
        """
        Uploads practices

        Upload all practices, tiles and segments for a campaign from a CSV file.

        **Tags**: editors

        **Examples

        Content of ``sustainability.csv``:

        .. code-block:: csv

            Joe,Smith,joesmith@example.com
            Marie,Johnson,mariejohnson@example.com

        .. code-block:: http

            POST /api/editables/alliance/campaigns/sustainability\
/upload HTTP/1.1

            Content-Disposition: form-data; name="file"; filename="sustainability.csv"
            Content-Type: text/csv

        responds:

        .. code-block:: json

            {
                "count": 5,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "path": null,
                        "title": "Construction",
                        "tags": ["public"],
                        "indent": 0
                    },
                    {
                      "path": null,
                      "title": "Governance & management",
                      "picture": "https://assets.tspproject.org/management.png",
                      "indent": 1
                    },
                    {
                        "path": "/construction/governance/the-assessment\
    -process-is-rigorous",
                        "title": "The assessment process is rigorous",
                        "indent": 2
                    },
                    {
                      "path": null,
                      "title": "Production",
                      "picture": "https://assets.tspproject.org/production.png",
                      "indent": 1
                    },
                    {
                        "path": "/construction/production/adjust-air-fuel\
    -ratio",
                        "title": "Adjust Air fuel ratio",
                        "indent": 2
                    }
                ]
            }

        """
        uploaded = request.FILES.get('file')
        try:
            import_campaign(self.campaign, uploaded)
        except csv.Error as err:
            raise ValidationError({'detail': str(err)})

        results = self.get_queryset()
        serializer = self.get_serializer(results, many=True)
        return Response({'results': serializer.data})


class CampaignEditableQuestionAPIView(QuestionMixin, CampaignContentMixin,
                                      PageElementEditableDetail):
    """
    Retrieves a question

    **Tags**: editors

    **Examples

    .. code-block:: http

        GET /api/editables/djaopsp/campaigns/sustainability\
/construction/governance/the-assessment-process-is-rigorous HTTP/1.1

    responds

    .. code-block:: json

        {
            "path": "/construction/governance/the-assessment\
-process-is-rigorous",
            "title": "The assessment process is rigorous",
            "default_unit": "assessment"
        }
    """
    serializer_class = get_question_serializer()

    def get_object(self):
        return self.question

    def delete(self, request, *args, **kwargs):
        """
        Deletes questions

        Deletes all questions under prefix *path*.

        **Tags**: editors

        **Examples

        .. code-block:: http

            DELETE /api/editables/alliance/campaigns/sustainability \
 HTTP/1.1
        """
        #pylint:disable=useless-super-delegation
        return super(CampaignEditableQuestionAPIView, self).delete(
            request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Creates a question

        Creates a new question under prefix *path*.

        **Tags**: editors

        **Examples

        .. code-block:: http

            POST /api/editables/alliance/campaigns/sustainability \
 HTTP/1.1

        .. code-block:: json

            {
              "title": "Adjust air/fuel ratio"
            }

        responds:

        .. code-block:: json

            {
                "path": "/construction/governance/the-assessment\
-process-is-rigorous",
                "title": "The assessment process is rigorous",
                "default_unit": "assessment"
            }
        """
        #pylint:disable=useless-super-delegation
        return super(CampaignEditableQuestionAPIView, self).post(
            request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Updates a question

        Updates the title, text and, if applicable, the metrics associated
        associated to the content element referenced by *path*.

        **Tags**: editors

        **Examples

        .. code-block:: http

            POST /api/editables/alliance/campaigns/sustainability \
 HTTP/1.1

        .. code-block:: json

            {
              "title": "Adjust air/fuel ratio"
            }

        responds:

        .. code-block:: json

            {
                "path": "/construction/governance/the-assessment\
-process-is-rigorous",
                "title": "The assessment process is rigorous",
                "default_unit": "assessment"
            }
        """
        #pylint:disable=useless-super-delegation
        return super(CampaignEditableQuestionAPIView, self).put(
            request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # Implementation note: overrides overide in `PageElementEditableDetail`
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        update_kwargs = {}
        for field_name, field_value in six.iteritems(serializer.validated_data):
            if field_value:
                update_kwargs.update({
                    field_name: field_value
                })

        get_question_model().objects.filter(
            path__endswith=self.db_path).update(**update_kwargs)

        return Response(serializer.data)
