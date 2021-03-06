# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

"""
Views used to edit assessment campaigns
"""

from deployutils.helpers import update_context_urls
from pages.views.elements import PageElementEditableView

from .downloads import PracticesSpreadsheetView
from ..api.campaigns import CampaignContentMixin
from ..compat import reverse
from ..mixins import CampaignMixin


class CampaignEditView(CampaignMixin, PageElementEditableView):

    account_url_kwarg = 'profile'

    def get_template_names(self):
        if self.is_prefix:
            # It is not a leaf, let's return the list view
            return ['survey/campaigns/campaign.html']
        return super(CampaignEditView, self).get_template_names()

    def get_context_data(self, **kwargs):
        context = super(CampaignEditView, self).get_context_data(**kwargs)

        campaign_slug = self.kwargs.get('campaign')
        context.update({'campaign': self.campaign})
        urls = {
            'api_editable_segments': reverse('api_campaign_editable_segments',
                args=(self.account, campaign_slug))
        }
        if self.is_prefix:
            # Editor
            urls.update({
                'api_practice_typeahead': reverse(
                    'pages_api_editables_index', args=(self.account,)),
                'api_content': reverse('api_campaign_editable_content',
                        args=(self.account, campaign_slug)),
                'campaign_download': reverse('campaign_download',
                    args=(self.account, campaign_slug)),
                'api_alias_node': reverse('pages_api_alias_node', args=(
                    self.account, '')),
                'api_mirror_node': reverse('pages_api_mirror_node',
                    args=(self.account, '')),
                'api_move_node': reverse('pages_api_move_node',
                    args=(self.account, '')),
            })
        update_context_urls(context, urls)
        return context


class CampaignXLSXView(CampaignContentMixin, PracticesSpreadsheetView):

    basename = 'practices'

    def get_headings(self):
        segments = [seg for seg in self.segments_available if seg['path']]
        return [''] + [seg['title'] for seg in segments]

    def format_row(self, entry):
        row = [entry['title']]
        for seg in self.segments_available:
            tags = entry.get('extra', {}).get('tags', [])
            if seg['path'] in tags:
                row += [entry['title']]
            else:
                row += ['']
        return row
