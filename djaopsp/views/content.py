# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_url)
from deployutils.helpers import update_context_urls
from pages.views.elements import PageElementView, PageElementEditableView
from pages.views.sequences import (
    SequenceProgressView as BaseSequenceProgressView,
    SequencePageElementView as BaseSequencePageElementView)

from ..compat import gettext_lazy as _, reverse
from ..mixins import AccountMixin, SequenceProgressMixin


class SequenceProgressView(SequenceProgressMixin, BaseSequenceProgressView):
    pass


class SequencePageElementView(SequenceProgressMixin,
                              BaseSequencePageElementView):
    pass


class ContentIndexView(PageElementView):
    """
    View to display a tree of practices rooted at {path}
    """
    account_url_kwarg = 'profile'

    def get_context_data(self, **kwargs):
        context = super(ContentIndexView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'api_accounts': site_url("/api/users"),
            'download': reverse('pages_element_download', kwargs={
                'path': self.kwargs.get('path')}),
            'practices_index': reverse('pages_index'),
        })
        return context


class ContentDetailView(PageElementView):
    """
    View to display a single practice details
    """
    account_url_kwarg = 'profile'
    direct_text_load = True

    def get_context_data(self, **kwargs):
        context = super(ContentDetailView, self).get_context_data(**kwargs)
        context.update({'element': self.element})
        update_context_urls(context, {
            'api_accounts': site_url("/api/users"),
            'download': reverse('pages_element_download', kwargs={
                'path': self.kwargs.get('path')}),
            'practices_index': reverse('pages_index'),
        })
        return context


class EditablesIndexView(AccountMixin, PageElementEditableView):
    """
    View to display a tree of editable practices rooted at {path}
    """

    def get_reverse_kwargs(self):
        """
        List of kwargs taken from the url that needs to be passed through
        to ``reverse``.
        """
        return [self.account_url_kwarg, self.path_url_kwarg]


class EditablesDetailView(AccountMixin, PageElementEditableView):
    """
    View to display a single editable practice details
    """

    def get_reverse_kwargs(self):
        """
        List of kwargs taken from the url that needs to be passed through
        to ``reverse``.
        """
        return [self.account_url_kwarg, self.path_url_kwarg]

    def get_context_data(self, **kwargs):
        context = super(
            EditablesDetailView, self).get_context_data(**kwargs)
        # Adding element in the context, we are using server-side rendering
        # instead of relying on Vue to load the content. This is because
        # there seems to still be some issues with editors on
        # `.editable .edit-formatted`.
        context.update({
            'element': self.element,
            'edit_perm': (self.manages(self.element.account) or
                self.manages_broker)
        })
        return context
