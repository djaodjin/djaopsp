# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from pages.views.elements import PageElementView, PageElementEditableView

from ..mixins import AccountMixin


class ContentIndexView(PageElementView):
    """
    View to display a tree of practices rooted at {path}
    """
    account_url_kwarg = 'profile'


class ContentDetailView(PageElementView):
    """
    View to display a single practice details
    """
    account_url_kwarg = 'profile'
    direct_text_load = True


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
        context.update({'element': self.element})
        return context
