# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

"""
Views used to edit assessment campaigns
"""

from deployutils.helpers import update_context_urls
from django.views.generic import TemplateView

from ..compat import reverse, gettext_lazy as _
from ..mixins import AccountMixin, CampaignMixin


class CampaignEditView(CampaignMixin, AccountMixin, TemplateView):
    """
    View to edit a campaign
    """
    account_url_kwarg = 'profile'
    template_name = 'survey/campaigns/campaign.html'

    def get_context_data(self, **kwargs):
        context = super(CampaignEditView, self).get_context_data(**kwargs)

        campaign_slug = self.kwargs.get('campaign')
        context.update({'campaign': self.campaign})
        urls = {
            'api_editable_segments': reverse('api_campaign_editable_segments',
                args=(self.account, campaign_slug))
        }
        # Editor
        urls.update({
            'api_practice_typeahead': reverse(
                'pages_api_editables_index', args=(self.account,)),
            'api_content': reverse('survey_api_campaign',
                args=(self.account, campaign_slug)),
            'api_alias_node': reverse('pages_api_alias_node', args=(
                self.account, '')),
            'api_mirror_node': reverse('pages_api_mirror_node',
                args=(self.account, '')),
            'api_move_node': reverse('pages_api_move_node',
                args=(self.account, '')),
            'api_upload': reverse('api_campaign_upload',
                args=(self.account, campaign_slug)),
            'api_units': reverse('survey_api_units'),
            'download': reverse('campaign_download',
                args=(self.account, campaign_slug)),
            'pages_editables_index': reverse('pages_editables_index',
                args=(self.account,)),
        })
        update_context_urls(context, urls)
        return context
