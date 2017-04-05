# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging

from django.views.generic import TemplateView
from pages.models import PageElement

from ..mixins import PermissionMixin


LOGGER = logging.getLogger(__name__)


class IndexView(PermissionMixin, TemplateView):

    template_name = 'index.html'

    def get_context_data(self, *args, **kwargs):
        context = super(IndexView, self).get_context_data(*args, **kwargs)
        for element in PageElement.objects.filter(tag__contains='industry'):
            tags = element.tag.split(',')
            if 'enabled' in tags:
                context.update({
                    "%s_attrs" % element.slug.replace('-', '_'): "checked"})
        return context
