# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

import json

from deployutils.crypt import JSONEncoder
from deployutils.apps.django.templatetags.deployutils_prefixtags import (
    site_prefixed)
from django.urls import reverse
from django.views.generic import TemplateView
from deployutils.helpers import update_context_urls
from pages.mixins import TrailMixin
from pages.views.elements import PageElementView, PageElementEditableView
from survey.utils import get_question_model

from ..mixins import AccountMixin


class ContentIndexView(PageElementView):

    template_name = 'pages/index.html'


class ContentDetailView(PageElementView):

    account_url_kwarg = 'profile'
    template_name = 'pages/segment.html'


class EditablesIndexView(AccountMixin, PageElementEditableView):
    """
    """

class EditablesDetailView(AccountMixin, PageElementEditableView):
    """
    """
