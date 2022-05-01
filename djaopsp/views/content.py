# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from pages.views.elements import PageElementView, PageElementEditableView

from ..mixins import AccountMixin


class ContentIndexView(PageElementView):

    account_url_kwarg = 'profile'


class ContentDetailView(PageElementView):

    account_url_kwarg = 'profile'


class EditablesIndexView(AccountMixin, PageElementEditableView):
    """
    """
    def get_reverse_kwargs(self):
        """
        List of kwargs taken from the url that needs to be passed through
        to ``reverse``.
        """
        return [self.account_url_kwarg, self.path_url_kwarg]


class EditablesDetailView(AccountMixin, PageElementEditableView):
    """
    """
    def get_reverse_kwargs(self):
        """
        List of kwargs taken from the url that needs to be passed through
        to ``reverse``.
        """
        return [self.account_url_kwarg, self.path_url_kwarg]
