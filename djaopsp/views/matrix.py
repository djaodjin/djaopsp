# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

import datetime, io, logging

from deployutils.helpers import datetime_or_now, update_context_urls
from django.db import connection
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from openpyxl import Workbook
from pages.models import PageElement, build_content_tree
from survey.helpers import get_extra
from survey.models import Unit
from survey.views.matrix import CompareView as CompareBaseView

from ..api.portfolios import SupplierListMixin
from ..compat import reverse, six
from ..helpers import as_valid_sheet_title
from ..queries import get_completed_assessments_at_by
from .portfolios import DashboardMixin, UpdatedMenubarMixin

LOGGER = logging.getLogger(__name__)


class CompareView(UpdatedMenubarMixin, DashboardMixin, CompareBaseView):
    """
    Compare samples side-by-side
    """
    breadcrumb_url = 'matrix_compare_path'

    def get_context_data(self, **kwargs):
        context = super(CompareView, self).get_context_data(**kwargs)
        update_context_urls(context, {
            'pages_index': reverse('pages_index')})
        url_kwargs = self.get_url_kwargs()
        if 'path' in self.kwargs:
            url_kwargs.update({'path': self.kwargs.get('path')})
            update_context_urls(context, {
                'download': reverse(
                    'download_matrix_compare_path', kwargs=url_kwargs),
            })
        else:
            update_context_urls(context, {
                'download': reverse(
                    'download_matrix_compare', kwargs=url_kwargs),
            })
        return context


class CompareXLSXView(DashboardMixin, SupplierListMixin, TemplateView):
    """
    Download detailed answers of each suppliers
    """
    content_type = \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    basename = 'dashboard'

    indent_step = '    '
    show_comments = True
    show_planned = False

    @staticmethod
    def _get_consumption(element):
        return element.get('consumption', None)

    @staticmethod
    def _get_tag(element):
        return element.get('tag', "")

    @staticmethod
    def _get_title(element):
        return element.get('title', "")

    @property
    def latest_assessments(self):
        if not hasattr(self, '_latest_assessments'):
            #pylint:disable=attribute-defined-outside-init
            self._latest_assessments = self.get_latest_samples(self.db_path)
        return self._latest_assessments

    def write_headers(self, wsheet):
        """
        Write table headers in the worksheet
        """
        headings = [''] + [reporting.printable_name
            for reporting in self.accounts_with_response]
        wsheet.append(headings)
        headings = [''] + [reporting.slug
            for reporting in self.accounts_with_response]
        wsheet.append(headings)
        headings = ['']
        for reporting in self.accounts_with_response:
            tags = get_extra(reporting, 'tags')
            if tags:
                headings += [','.join(tags)]
            else:
                headings += [""]
        wsheet.append(headings)

        # creates row with last completed date
        last_activity_at_by_accounts = {}
        for sample in self.latest_assessments:
            last_activity_at_by_accounts.update({
                sample.account_id: sample.created_at})
        headings = ['Last completed at']
        for reporting in self.accounts_with_response:
            account_id = reporting.pk
            last_activity_at = last_activity_at_by_accounts.get(account_id)
            if reporting.grant_key:
                headings += ["Requested"]
            elif last_activity_at:
                headings += [datetime.date(
                    last_activity_at.year,
                    last_activity_at.month,
                    last_activity_at.day)]
            else:
                headings += [""]
        wsheet.append(headings)

    def writerow(self, row, leaf=False):
        #pylint:disable=unused-argument
        self.wsheet.append(row)

    def write_tree(self, root, indent=''):
        """
        The *root* parameter looks like:
        (PageElement, [(PageElement, [...]), (PageElement, [...]), ...])
        """
        if not root[1]:
            # We reached a leaf
            row = [indent + self._get_title(root[0])]
            slug = root[0]['slug']
            by_accounts = self.by_paths.get(slug)
            if by_accounts:
                for reporting in self.accounts_with_response:
                    account_id = reporting.pk
                    if reporting.grant_key:
                        row += [""]
                    else:
                        answer = by_accounts.get(account_id, {})
                        measured = answer.get('measured', "")
                        prev = measured
                        try:
                            measured = int(measured)
                        except ValueError:
                            try:
                                measured = float(measured)
                            except ValueError:
                                pass
                        row += [measured]
                row += [slug]
            self.writerow(row, leaf=True)
        else:
            self.writerow([indent + self._get_title(root[0])])
            for element in six.itervalues(root[1]):
                self.write_tree(element, indent=indent + self.indent_step)


    def write_comments(self, root, indent=''):
        """
        The *root* parameter looks like:
        (PageElement, [(PageElement, [...]), (PageElement, [...]), ...])
        """
        if not root[1]:
            # We reached a leaf
            row = [indent + self._get_title(root[0])]
            slug = root[0]['slug']
            by_accounts = self.by_paths.get(slug)
            if by_accounts:
                for reporting in self.accounts_with_response:
                    account_id = reporting.pk
                    if reporting.grant_key:
                        row += [""]
                    else:
                        answer = by_accounts.get(account_id, {})
                        comments = answer.get('comments', "")
                        row += [comments]
                row += [slug]
            self.writerow(row, leaf=True)
        else:
            self.writerow([indent + self._get_title(root[0])])
            for element in six.itervalues(root[1]):
                self.write_comments(element, indent=indent + self.indent_step)


    def get_latest_samples(self, from_root):
        kwargs = {}
        if self.show_planned:
            kwargs.update({'extra': 'is_planned'})
        return get_completed_assessments_at_by(self.campaign,
            ends_at=self.ends_at, prefix=from_root, **kwargs)

    def get_tiles(self):
        """
        Returns a list of tiles that will be used as roots for the rows
        in the spreadsheet.
        """
        tiles = []
        for segment in self.segments_available:
            path = segment['path']
            if path:
                slug = path.split('/')[-1]
                segment_tiles = PageElement.objects.filter(
                    to_element__orig_element__slug=slug).order_by(
                    'to_element__rank')
                insert_point = None
                for segment_tile in segment_tiles:
                    found = None
                    for index, tile in enumerate(tiles):
                        if segment_tile.title == tile.title:
                            found = index
                            break
                    if found is not None:
                        insert_point = found + 1
                    else:
                        if insert_point:
                            tiles = (tiles[:insert_point] + [segment_tile] +
                                tiles[insert_point:])
                            insert_point = insert_point + 1
                        else:
                            tiles = tiles + [segment_tile]
        return tiles

    def get(self, request, *args, **kwargs):
        #pylint:disable=too-many-statements,too-many-locals
        self.by_paths = {}
        accounts_with_response = set([])
        if self.requested_accounts_pk_as_sql:
            reporting_answers_sql = """
WITH samples AS (
    %(latest_assessments)s
),
answers AS (SELECT
    survey_question.path,
    samples.account_id,
    survey_answer.measured,
    survey_answer.unit_id,
    survey_question.default_unit_id,
    survey_unit.title
FROM survey_answer
INNER JOIN survey_question
  ON survey_answer.question_id = survey_question.id
INNER JOIN samples
  ON survey_answer.sample_id = samples.id
INNER JOIN survey_unit
  ON survey_answer.unit_id = survey_unit.id
WHERE samples.account_id IN %(account_ids)s)
SELECT
  answers.path,
  answers.account_id,
  answers.measured,
  answers.unit_id,
  answers.default_unit_id,
  answers.title,
  survey_choice.text
FROM answers
LEFT OUTER JOIN survey_choice
  ON survey_choice.unit_id = answers.unit_id AND
     survey_choice.id = answers.measured
""" % {
            'latest_assessments': self.latest_assessments.query.sql,
            'account_ids': self.requested_accounts_pk_as_sql
        }
            comments_unit = Unit.objects.get(slug='freetext')
            with connection.cursor() as cursor:
                cursor.execute(reporting_answers_sql, params=None)
                for row in cursor:
                    path = row[0].split('/')[-1] # XXX slug
                    account_id = row[1]
                    measured = row[2]
                    unit_id = row[3]
                    default_unit_id = row[4]
                    text = row[6]
                    if path not in self.by_paths:
                        by_accounts = {}
                        self.by_paths.update({path: by_accounts})
                    else:
                        by_accounts = self.by_paths.get(path)
                    if account_id not in by_accounts:
                        by_accounts.update({
                            account_id: {'measured': "", 'comments': ""}})
                    if measured:
                        accounts_with_response |= set([account_id])
                    if unit_id == default_unit_id:
                        self.by_paths[path][account_id]['measured'] = (
                            text if text else measured)
                    elif unit_id == comments_unit.pk:
                        self.by_paths[path][account_id]['comments'] += str(
                            text) if text else ""

        # Use only accounts with a response otherwise we pick all suppliers
        # that are connected to a dashboard but not necessarly invited to
        # answer on a specific segment.
        # Here the code to get all suppliers, in case:
        # ```self.accounts_with_response = sorted(
        #    list(self.requested_accounts.items()),
        #    key=lambda val: val[1].organization.printable_name)```
        self.accounts_with_response = self.requested_accounts.filter(
            pk__in=accounts_with_response).order_by('extra', 'full_name') # if we try
        # to order by 'full_name', we get an error "DISTINCT ON must match
        # ORDER BY".

        # We use cut=None here so we print out the full assessment
        root = build_content_tree(roots=self.get_tiles(),
            prefix=self.db_path, cut=None)

        # Populate the worksheet
        wbook = Workbook()
        self.wsheet = wbook.active
        self.wsheet.title = as_valid_sheet_title("Answers")
        self.write_headers(self.wsheet)

        indent = ''
        for nodes in six.itervalues(root):
            self.writerow([self._get_title(nodes[0])])
            for elements in six.itervalues(nodes[1]):
                self.write_tree(elements, indent=indent + self.indent_step)

        if self.show_comments:
            self.wsheet = wbook.create_sheet(as_valid_sheet_title("Comments"))
            self.write_headers(self.wsheet)
            indent = ''
            for nodes in six.itervalues(root):
                self.writerow([self._get_title(nodes[0])])
                for elements in six.itervalues(nodes[1]):
                    self.write_comments(
                        elements, indent=indent + self.indent_step)

        # Prepares the result file
        content = io.BytesIO()
        wbook.save(content)
        content.seek(0)

        resp = HttpResponse(content, content_type=self.content_type)
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.get_filename())
        return resp

    def get_filename(self):
        return "%s-%s-%s-%s.xlsx" % (self.account.slug, self.basename,
            'planning' if self.show_planned else 'assessments',
            datetime_or_now().strftime('%Y%m%d'))
