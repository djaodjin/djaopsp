# Copyright (c) 2026, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

from extended_templates.backends.pdf import PdfTemplateResponse
from pages.models import PageElement
from survey.api.base import QuestionListAPIView

from ..api.samples import AssessmentContentMixin

class ImproveContentBaseView(QuestionListAPIView):

    def get_context_data(self, **kwargs):
        return {}


class ImproveContentPDFView(AssessmentContentMixin, ImproveContentBaseView):

    http_method_names = ['get']
    template_name = 'app/prints/improve.html'
    content_type = 'application/pdf'
    indent_step = '    '

    def __init__(self, **kwargs):
        super(ImproveContentPDFView, self).__init__(**kwargs)
        self.table_of_content = []

    def get(self, request, *args, **kwargs):
        #pylint:disable=attribute-defined-outside-init
        self.object_list = []
        for item in self.get_queryset():
            found = False
            if 'default_unit' in item:
                planned = item.get('planned')
                if planned:
                    for answer in planned:
                        unit = answer.get('unit')
                        if (unit.slug == 'assessment' and
                            answer.get('measured') in ['Yes', 'Mostly Yes']):
                            found = True
            if found:
                element_text_qs = PageElement.objects.filter(
                    slug=item['slug']).values_list('text', flat=True)
                element_text = element_text_qs[0] if element_text_qs else ""
                item.update({'text': element_text})
                self.object_list += [item]
                self.table_of_content += [item]
        context = self.get_context_data(**kwargs)
        context.update({
            'table_of_content': self.table_of_content,
            'object_list': self.object_list
        })
        return PdfTemplateResponse(request, self.template_name, context)
