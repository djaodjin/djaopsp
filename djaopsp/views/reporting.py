# Copyright (c) 2026, DjaoDjin inc.
# see LICENSE.

from deployutils.helpers import update_context_urls
from django.views.generic.base import TemplateView

from ..compat import reverse
from ..mixins import AccountMixin


class CustomScorecardEditView(AccountMixin, TemplateView):

    template_name = "app/reporting/scorecards/index.html"

    def get_context_data(self, **kwargs):
        context = super(CustomScorecardEditView, self).get_context_data(
            **kwargs)
        update_context_urls(context, {
            'api_campaign_typeahead': reverse(
                'api_reporting_campaigns', args=(self.account,)),
            'api_question_typeahead': reverse('api_campaign_base'),
        })
        return context


class CustomScorecardView(AccountMixin, TemplateView):

    template_name = "app/reporting/scorecards/index.html"

