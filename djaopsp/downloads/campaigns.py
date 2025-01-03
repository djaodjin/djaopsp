# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

from .content import PracticesSpreadsheetView
from ..api.campaigns import CampaignContentMixin
from ..compat import force_str, gettext_lazy as _


class CampaignXLSXView(CampaignContentMixin, PracticesSpreadsheetView):

    strip_segment_prefix = True

    @property
    def basename(self):
        return str(self.campaign)

    def get_headings(self):
        segments = [seg for seg in self.segments_available if seg['path']]
        return [
            force_str(_('Practices')),
            force_str(_('Level for heading, default unit for practices')),
            force_str(_('Required'))
        ] + [seg['title'] for seg in segments]

    def format_row(self, entry, key=None):
        default_unit = entry.get('default_unit', {}).get('slug')
        indent = entry.get('indent')
        if not indent:
            indent = 0
        row = [entry['title'],
               default_unit if default_unit else (indent + 1),
               entry.get('required')]
        for seg in self.segments_available:
            segments = entry.get('extra', {}).get('segments', [])
            if seg['path'] in segments:
                row += [entry['title']]
            else:
                row += ['']
        return row
