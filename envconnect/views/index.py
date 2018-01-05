# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging

from django.core.urlresolvers import reverse
from django.views.generic import TemplateView

from ..mixins import PermissionMixin


LOGGER = logging.getLogger(__name__)


class IndexView(PermissionMixin, TemplateView):

    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        pre_industries = []
        energy_industries = []
        btw_industries = []
        metal_industries = []
        post_industries = []
        for element in self.get_roots().order_by('title'):
            tags = element.tag
            if 'enabled' in tags:
                setattr(element, 'enabled', True)
            if 'energy' in tags:
                energy_industries += [element]
            elif 'metal' in tags:
                metal_industries += [element]
            elif element.title[0] < 'E':
                pre_industries += [element]
            elif element.title[0] >= 'M':
                post_industries += [element]
            else:
                btw_industries += [element]
        context.update({
            'pre_industries': pre_industries,
            'energy_industries': energy_industries,
            'btw_industries': btw_industries,
            'metal_industries': metal_industries,
            'post_industries': post_industries})
        self.update_context_urls(context, {
            'api_enable': reverse('api_enable', args=("",)),
            'api_disable': reverse('api_disable', args=("",)),
        })
        return context
