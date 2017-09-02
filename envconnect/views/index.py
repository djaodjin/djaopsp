# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging

from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from pages.models import PageElement

from ..mixins import PermissionMixin


LOGGER = logging.getLogger(__name__)


class IndexView(PermissionMixin, TemplateView):

    template_name = 'index.html'

    def get_context_data(self, *args, **kwargs):
        context = super(IndexView, self).get_context_data(*args, **kwargs)
        pre_industries = []
        metal_industries = []
        post_industries = []
        for element in self.get_roots().order_by('title'):
            tags = element.tag
            if 'enabled' in tags:
                setattr(element, 'enabled', True)
            if 'metal' in tags:
                metal_industries += [element]
            elif element.title[0] < 'M':
                pre_industries += [element]
            else:
                post_industries += [element]
        context.update({
            'pre_industries': pre_industries,
            'metal_industries': metal_industries,
            'post_industries': post_industries})
        self.update_context_urls(context, {
            'api_enable': reverse('api_enable', args=("",)),
            'api_disable': reverse('api_disable', args=("",)),
        })
        return context
