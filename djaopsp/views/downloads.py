# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.
from __future__ import unicode_literals

from django.views.generic import ListView
from extended_templates.backends.pdf import PdfTemplateResponse
from pages.models import PageElement

from ..api.samples import AssessmentContentMixin


class ImproveContentPDFView(AssessmentContentMixin, ListView):

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
            if 'default_unit' in item:
                element_text_qs = PageElement.objects.filter(
                    slug=item['slug']).values_list('text', flat=True)
                element_text = element_text_qs[0] if element_text_qs else ""
                item.update({'text': element_text})
                self.object_list += [item]
            self.table_of_content += [item]
        context = self.get_context_data(**kwargs)
        context.update({'table_of_content': self.table_of_content})
        return PdfTemplateResponse(request, self.template_name, context)
