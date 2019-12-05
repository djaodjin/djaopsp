# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

import logging

from deployutils.helpers import update_context_urls
from django.views.generic import TemplateView
from django.utils import six

from ..compat import reverse
from ..helpers import get_testing_accounts
from ..mixins import AccountMixin, BreadcrumbMixin, ContentCut


LOGGER = logging.getLogger(__name__)


class IndexView(BreadcrumbMixin, TemplateView):

    template_name = 'index.html'

    def flatten(self, rollup_trees, depth=0):
        result = []
        for _, values in six.iteritems(rollup_trees):
            elem, nodes = values
            result += [(depth, elem)]
            result += self.flatten(nodes, depth=depth + 1)
        return result

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        cut = ContentCut(depth=2)
        menus = []
        for root in self.get_roots().exclude(
                tag__contains='energy').order_by('title'):
            if not cut.enter(root.tag):
                menus += [(0, root)]
            else:
                rollup_trees = self._cut_tree(self.build_content_tree(
                    [root], prefix='', cut=cut), cut=cut)
                menus += self.flatten(rollup_trees)
        context.update({'industries': menus})
        update_context_urls(context, {
            'api_enable': reverse('api_enable', args=("",)),
            'api_disable': reverse('api_disable', args=("",)),
        })
        return context


class AppView(AccountMixin, IndexView):
    """
    Homepage for an organization.
    """

    template_name = 'envconnect/app.html'

    def get_context_data(self, **kwargs):
        context = super(AppView, self).get_context_data(**kwargs)
        context.update({
            'FEATURES_DEBUG': self.account.pk in get_testing_accounts()
        })
        update_context_urls(context, {
            'api_historical_scores': reverse('api_historical_scores',
                    args=(self.account, '')),
        })
        return context
