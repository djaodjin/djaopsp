# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE.

from survey.helpers import datetime_or_now

from .content import PracticesSpreadsheetView
from ..api.samples import AssessmentContentMixin
from ..compat import six
from ..scores import get_score_calculator


class AssessPracticesXLSXView(AssessmentContentMixin, PracticesSpreadsheetView):

    base_headers = ['', 'Points', 'Assessed', 'Planned', 'Comments',
        'Opportunity']

    @property
    def intrinsic_value_headers(self):
        if not hasattr(self, '_intrinsic_value_headers'):
            #pylint:disable=attribute-defined-outside-init
            self._intrinsic_value_headers = []
            for seg in self.segments_available:
                prefix = seg.get('path')
                if prefix:
                    score_calculator = get_score_calculator(prefix)
                    if (score_calculator and
                        score_calculator.intrinsic_value_headers):
                        self._intrinsic_value_headers = \
                            score_calculator.intrinsic_value_headers
                        break
        return self._intrinsic_value_headers

    def get_headings(self):
        if not hasattr(self, 'units'):
            #pylint:disable=attribute-defined-outside-init
            self.units = {}
        self.peer_value_headers = []
        for unit in six.itervalues(self.units):
            if (unit.system == unit.SYSTEM_ENUMERATED and
                unit.slug == 'assessment'):
                self.peer_value_headers += [
                    (unit.slug, [choice.text for choice in unit.choices])]
        headers = [] + self.base_headers
        for header in self.peer_value_headers:
            headers += header[1]
        if self.peer_value_headers:
            headers += [
                "Nb respondents",
            ]
        headers += self.intrinsic_value_headers
        return headers

    def get_title_row(self):
        return [self.sample.account.printable_name,
            self.sample.created_at.strftime("%Y-%m-%d")]


    def format_row(self, entry, key=None):
        #pylint:disable=too-many-locals
        default_unit = entry.get('default_unit', {})
        default_unit_choices = []
        if default_unit:
            try:
                default_unit = default_unit.slug
            except AttributeError:
                default_unit_choices = default_unit.get('choices', [])
                default_unit = default_unit.get('slug', "")
        answers = entry.get('answers')
        primary_assessed = None
        primary_planned = None
        points = None
        comments = ""
        if answers:
            for answer in answers:
                unit = answer.get('unit')
                if unit and default_unit and unit.slug == default_unit:
                    primary_assessed = answer.get('measured')
                    continue
                if unit and unit.slug == 'freetext': #XXX
                    comments = answer.get('measured')
                if unit and unit.slug == 'points': #XXX
                    points = float(answer.get('measured'))
        planned = entry.get('planned')
        if planned:
            for answer in planned:
                unit = answer.get('unit')
                if unit and default_unit and unit.slug == default_unit:
                    primary_planned = answer.get('measured')
        # base_headers
        title = entry['title']
        if default_unit and default_unit_choices:
            subtitle = ""
            for choice in default_unit_choices:
                text = choice.get('text', "").strip()
                descr = choice.get('descr', "").strip()
                if text != descr:
                    subtitle += "\n%s - %s" % (text, descr)
            if subtitle:
                title += "\n" + subtitle
        row = [
            title,
            points,
            primary_assessed,
            primary_planned,
            comments,
            entry.get('opportunity')]

        # peer_value_headers
        for header in self.peer_value_headers:
            if default_unit and default_unit == header[0]:
                for text in header[1]:
                    row += [entry.get('rate', {}).get(text, 0)]
            else:
                for text in header[1]:
                    row += [""]
        if self.peer_value_headers:
            row += [
                entry.get('nb_respondents'),
            ]

        # intrinsic_value_headers
        avg_value = 0
        extra = entry.get('extra')
        if extra:
            intrinsic_values = extra.get('intrinsic_values')
            if intrinsic_values:
                environmental_value = intrinsic_values.get('environmental', 0)
                business_value = intrinsic_values.get('business', 0)
                profitability = intrinsic_values.get('profitability', 0)
                implementation_ease = intrinsic_values.get(
                    'implementation_ease', 0)
                avg_value = (environmental_value + business_value +
                    profitability + implementation_ease) // 4
        if avg_value:
            row += [
                environmental_value,
                business_value,
                profitability,
                implementation_ease,
                avg_value
            ]
        else:
            row += ['', '', '', '', '']
        return row

    def get_filename(self):
        return datetime_or_now().strftime("%s-%s-%%Y%%m%%d.xlsx" % (
            self.sample.account.slug, self.campaign.slug))
