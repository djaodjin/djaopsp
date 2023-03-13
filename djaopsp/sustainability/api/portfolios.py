# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
import datetime

from dateutil.relativedelta import relativedelta
from deployutils.helpers import datetime_or_now, parse_tz
from django.db import connection
from django.db.models import Count, Q
from rest_framework import generics
from rest_framework.response import Response
import pytz
from survey.helpers import construct_weekly_periods
from survey.utils import get_account_model

from djaopsp.api.portfolios import DashboardAggregateMixin
from djaopsp.utils import get_alliances


class CompletionRateMixin(DashboardAggregateMixin):

    def get_aggregate(self, account=None, labels=None, years=0):
        # XXX Use the *labels* instead of recomputing weekly periods?
        last_date = datetime_or_now(self.ends_at)
        if self.default_start_at:
            first_date = self.default_start_at
        else:
            first_date = last_date - relativedelta(months=4)
        weekends_at = construct_weekly_periods(
            first_date, last_date, years=years)
        if len(weekends_at) < 2:
            # Not enough time periods
            return []

        values = []
        account_model = get_account_model()
        requested_accounts = self.get_requested_accounts(account=account)
        nb_requested_accounts = len(requested_accounts)
        start_at = weekends_at[0]
        for ends_at in weekends_at[1:]:
            nb_frozen_samples = account_model.objects.filter(
                samples__extra__isnull=True,
                samples__is_frozen=True,
                samples__created_at__gte=start_at,
                samples__created_at__lt=ends_at,
                samples__account_id__in=requested_accounts
            ).distinct().count()
            if self.is_percentage:
                if nb_requested_accounts:
                    rate = nb_frozen_samples * 100 // nb_requested_accounts
                else:
                    rate = 0
            else:
                rate = nb_frozen_samples
            values += [(ends_at, rate)]
        return values

    def get_response_data(self, request, *args, **kwargs):
        alliances = get_alliances(self.account)
        table = []
        table += [{
            'slug': "% completion" if self.is_percentage else "nb completed",
            'printable_name': "% completion" if self.is_percentage else "nb completed",
            'values': self.get_aggregate(self.account)
        }]
        table += [{
            'slug': "vs. last year",
            'printable_name': "vs. last year",
            'values': self.get_aggregate(self.account, years=-1)
        }]
        for account in list(alliances):
            table += [{
                'slug': account.slug,
                'printable_name': account.printable_name,
                'values': self.get_aggregate(account)
            }]
        return  {
            'title': "Completion rate (%s)" % (
                '%' if self.is_percentage else "nb"),
            'scale': self.scale,
            'unit': self.unit,
            'results': table
        }


class CompletionRateAPIView(CompletionRateMixin, generics.RetrieveAPIView):
    """
    Retrieves the completion rate

    Returns the week-by-week percentage of requested accounts
    that have completed a scorecard.

    **Tags**: reporting

    **Examples**

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/completion-rate HTTP/1.1

    responds

    .. code-block:: json

        {
          "title":"Completion rate (%)",
          "scale":1,
          "unit":"percentage",
          "results":[{
            "slug": "completion-rate",
            "printable_name": "% completion",
            "values":[
              ["2020-09-13T00:00:00Z",0],
              ["2020-09-20T00:00:00Z",0],
              ["2020-09-27T00:00:00Z",0],
              ["2020-10-04T00:00:00Z",0],
              ["2020-10-11T00:00:00Z",0],
              ["2020-10-18T00:00:00Z",0],
              ["2020-10-25T00:00:00Z",0],
              ["2020-11-01T00:00:00Z",0],
              ["2020-11-08T00:00:00Z",0],
              ["2020-11-15T00:00:00Z",0],
              ["2020-11-22T00:00:00Z",0],
              ["2020-11-29T00:00:00Z",0],
              ["2020-12-06T00:00:00Z",0],
              ["2020-12-13T00:00:00Z",0],
              ["2020-12-20T00:00:00Z",0],
              ["2020-12-27T00:00:00Z",0],
              ["2021-01-03T00:00:00Z",0]
            ]
          }, {
            "slug":"last-year",
            "printable_name": "vs. last year",
            "values":[
              ["2019-09-15T00:00:00Z",0],
              ["2019-09-22T00:00:00Z",0],
              ["2019-09-29T00:00:00Z",0],
              ["2019-10-06T00:00:00Z",0],
              ["2019-10-13T00:00:00Z",0],
              ["2019-10-20T00:00:00Z",0],
              ["2019-10-27T00:00:00Z",0],
              ["2019-11-03T00:00:00Z",0],
              ["2019-11-10T00:00:00Z",0],
              ["2019-11-17T00:00:00Z",0],
              ["2019-11-24T00:00:00Z",0],
              ["2019-12-01T00:00:00Z",0],
              ["2019-12-08T00:00:00Z",0],
              ["2019-12-15T00:00:00Z",0],
              ["2019-12-22T00:00:00Z",0],
              ["2019-12-29T00:00:00Z",0],
              ["2020-01-05T00:00:00Z",0]
            ]
          }, {
            "slug":"alliance",
            "printable_name": "Alliance",
            "values":[
              ["2020-09-13T00:00:00Z",0],
              ["2020-09-20T00:00:00Z",0],
              ["2020-09-27T00:00:00Z",0],
              ["2020-10-04T00:00:00Z",0],
              ["2020-10-11T00:00:00Z",0],
              ["2020-10-18T00:00:00Z",0],
              ["2020-10-25T00:00:00Z",0],
              ["2020-11-01T00:00:00Z",0],
              ["2020-11-08T00:00:00Z",0],
              ["2020-11-15T00:00:00Z",0],
              ["2020-11-22T00:00:00Z",0],
              ["2020-11-29T00:00:00Z",0],
              ["2020-12-06T00:00:00Z",0],
              ["2020-12-13T00:00:00Z",0],
              ["2020-12-20T00:00:00Z",0],
              ["2020-12-27T00:00:00Z",0],
              ["2021-01-03T00:00:00Z",0]
            ]
          }]
        }
    """
    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_response_data(request, *args, **kwargs))



class GoalsMixin(DashboardAggregateMixin):

    title = "Goals"

    def get_aggregate(self, account=None, labels=None):
        #pylint:disable=unused-argument
        scorecards = self.get_reporting_scorecards(account)
        assessment_only_count = scorecards.exclude(
            Q(reporting_energy_target=True) |
            Q(reporting_water_target=True) |
            Q(reporting_ghg_target=True) |
            Q(reporting_waste_target=True) |
            Q(nb_planned_improvements__gt=0)).values(
                'sample__account_id').distinct().count()
        targets_and_plan_count = scorecards.filter(
            Q(reporting_energy_target=True) |
            Q(reporting_water_target=True) |
            Q(reporting_ghg_target=True) |
            Q(reporting_waste_target=True),
            nb_planned_improvements__gt=0).values(
                'sample__account_id').distinct().count()
        reporting_publicly_count = scorecards.filter(
            reporting_publicly=True).values(
                'sample__account_id').distinct().count()
        scorecards_count = scorecards.values(
                'sample__account_id').distinct().count()
        targets_or_plan_count = (
            scorecards_count - assessment_only_count - targets_and_plan_count)

        if self.is_percentage:
            if scorecards_count > 0:
                assessment_only_count = (
                    assessment_only_count * 100 // scorecards_count)
                targets_or_plan_count = (
                    targets_or_plan_count * 100 // scorecards_count)
                targets_and_plan_count = (
                    targets_and_plan_count * 100 // scorecards_count)
                reporting_publicly_count = (
                    reporting_publicly_count * 100 // scorecards_count)
            else:
                assessment_only_count = 0
                targets_or_plan_count = 0
                targets_and_plan_count = 0
                reporting_publicly_count = 0
        values = [
            ["Assessment only", assessment_only_count],
            ["Targets or plan", targets_or_plan_count],
            ["Targets and plan", targets_and_plan_count],
            ["Reporting publicly", reporting_publicly_count]
        ]
        return values


class GoalsAPIView(GoalsMixin, generics.RetrieveAPIView):
    """
    Retrieves planned improvements and targets

    Returns the number of reporting accounts with planned improvements,
    targets or both.

    **Tags**: reporting

    **Examples**

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/goals HTTP/1.1

    responds

    .. code-block:: json

        {
          "title":"Goals",
          "scale":1,
          "unit":"profiles",
          "results":[{
            "slug":"energy-utility",
            "printable_name":"Energy utility",
            "values": [
              ["Assessment only", 0],
              ["Targets or plan", 0],
              ["Targets and plan", 0]
            ]
          }, {
            "slug":"alliance",
            "printable_name":"Alliance",
            "values": [
              ["Assessment only", 0],
              ["Targets or plan", 0],
              ["Targets and plan", 0]
            ]
          }]
        }
    """
    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_response_data(request, *args, **kwargs))


class BySegmentsMixin(DashboardAggregateMixin):

    title = "Assessments completed by segments"

    def get_aggregate(self, account=None, labels=None):
        segments = {segment['path']: segment for segment in self.segments}
        by_segments = self.get_reporting_scorecards(account).filter(
            path__in=segments).values('path').annotate(
            nb_accounts=Count('path')).order_by('-nb_accounts')

        # total number of reporting accounts
        total_accounts = 0
        for segment in by_segments:
            total_accounts += segment.get('nb_accounts')
        values = []
        # Only display individually accounts that represent more than 50%.
        nb_accounts = 0
        for segment in by_segments:
            segment_path = segment.get('path')
            segment_nb_accounts = segment.get('nb_accounts')
            segment_title = segments[segment_path]['title']
            if not labels or segment_title in labels:
                segment_rate = segment_nb_accounts
                if self.is_percentage:
                    if total_accounts:
                        segment_rate = (
                            segment_nb_accounts * 100 / total_accounts)
                    else:
                        segment_rate = 0
                values += [(segment_title, segment_rate)]
                nb_accounts += segment_nb_accounts
            if not labels and nb_accounts > (total_accounts * 50) // 100:
                break
        if total_accounts - nb_accounts > 0:
            segment_nb_accounts = total_accounts - nb_accounts
            segment_rate = segment_nb_accounts
            if self.is_percentage:
                if total_accounts:
                    segment_rate = (
                        segment_nb_accounts * 100 / total_accounts)
                else:
                    segment_rate = 0
            values += [("Others", segment_rate)]
        return values


class BySegmentsAPIView(BySegmentsMixin, generics.RetrieveAPIView):
    """
    Retrieves assessments completed by segments

    Returns the number of reporting accounts aggregated by segments.

    **Tags**: reporting

    **Examples**

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/by-segments HTTP/1.1

    responds

    .. code-block:: json

        {
          "title": "Assessments completed by segments",
          "scale": 1,
          "unit": "profiles",
          "results": [{
            "slug": "energy-utility",
            "values": [
            ]
          }, {
            "slug": "alliance",
            "values": [
            ]
          }]
        }
    """
    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_response_data(request, *args, **kwargs))



class GHGEmissionsRateMixin(DashboardAggregateMixin):

    title = "GHG emissions reported"

    def get_aggregate(self, account=None, labels=None):
        #pylint:disable=unused-argument
        scorecards = self.get_reporting_scorecards(account)
        nb_reported = scorecards.filter(
            reporting_ghg_generated=True).values(
            'sample__account_id').distinct().count()
        nb_scorecards = scorecards.values(
            'sample__account_id').distinct().count()
        nb_not_reported = nb_scorecards - nb_reported
        if self.is_percentage:
            if nb_scorecards:
                nb_reported = (nb_reported  * 100 // nb_scorecards)
                nb_not_reported = (nb_not_reported * 100 // nb_scorecards)
            else:
                nb_reported = 0
                nb_not_reported = 0
        return [
            ["Reported", nb_reported],
            ["Not reported", nb_not_reported]
        ]


class GHGEmissionsRateAPIView(GHGEmissionsRateMixin, generics.RetrieveAPIView):
    """
    Retrieves GHG emissions reported (in percentage)

    Returns the percentage of reporting accounts which report GHG emissions.

    **Tags**: reporting

    **Examples**

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/ghg-emissions-rate HTTP/1.1

    responds

    .. code-block:: json

        {
          "title": "GHG emissions reported",
          "scale": 1,
          "unit": "percentage",
          "results": [{
            "slug": "energy-utility",
            "printable_name": "Energy utility",
            "values":[
              ["Reported",0],
              ["Not reported",0]
            ]
          }, {
            "slug": "alliance",
            "printable_name": "Alliance",
            "values":[
              ["Reported",0],
              ["Not reported",0]
            ]
          }]
        }
    """
    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_response_data(request, *args, **kwargs))


class GHGEmissionsAmountMixin(DashboardAggregateMixin):

    title = "GHG emissions reported"
    default_unit = 'tons'
    valid_units = []

    def construct_yearly_periods(self, first_date=None, last_date=None,
                                  timezone=None, years=0):
        # XXX Use *years* to create comparative charts?
        if not last_date:
            last_date = datetime_or_now(self.ends_at)
        if not first_date:
            first_date = last_date - relativedelta(years=4)
        at_time = first_date
        tzinfo = parse_tz(timezone)
        if not tzinfo:
            tzinfo = pytz.utc
        period_ends_at = []
        while at_time <= last_date:
            ends_at = datetime.datetime(year=at_time.year, month=1, day=1)
            if tzinfo:
                # we are interested in 00:00 local time, if we don't have
                # local time zone, fall back to 00:00 utc time
                # in case we have local timezone, replace utc with it
                ends_at = tzinfo.localize(ends_at.replace(tzinfo=None))
            period_ends_at += [ends_at]
            at_time += relativedelta(years=1)
        return period_ends_at


    def get_labels(self, aggregate=None):
        if aggregate:
            return super(GHGEmissionsAmountMixin, self).get_labels(aggregate)
        return self.construct_yearly_periods()

    @staticmethod
    def get_scope_query(path, accounts, ends_at):
        return """
WITH lastest_scope_emissions AS (
SELECT
  survey_sample.account_id,
  MAX(survey_answer.created_at) AS created_at
FROM survey_answer
INNER JOIN survey_question
  ON survey_answer.question_id = survey_question.id
INNER JOIN survey_sample
  ON survey_answer.sample_id = survey_sample.id
WHERE survey_question.path LIKE '%%%(path)s'
  AND survey_sample.account_id IN (%(account_ids)s)
  AND survey_sample.is_frozen
  AND survey_sample.extra IS NULL
  AND survey_answer.unit_id = (SELECT id FROM survey_unit WHERE slug='tons-year')
  AND survey_answer.created_at < '%(ends_at)s'
GROUP BY survey_sample.account_id)
SELECT survey_sample.account_id AS account_id,
       survey_answer.created_at AS created_at,
       measured
FROM survey_answer
INNER JOIN survey_question
  ON survey_answer.question_id = survey_question.id
INNER JOIN survey_sample
  ON survey_answer.sample_id = survey_sample.id
INNER JOIN lastest_scope_emissions
  ON survey_answer.created_at = lastest_scope_emissions.created_at
WHERE survey_question.path LIKE '%%%(path)s'
  AND survey_sample.account_id IN (%(account_ids)s)
  AND survey_sample.is_frozen
  AND survey_sample.extra IS NULL
  AND survey_answer.unit_id = (SELECT id FROM survey_unit WHERE slug='tons-year')
""" % {'path': path,
       'account_ids': ','.join([str(account.pk) for account in accounts]),
       'ends_at': ends_at}

    def get_aggregate(self, account=None, labels=None):
        if not labels:
            raise ValueError("labels cannot be `None`")
        values = []
        reporting_accounts = self.get_requested_accounts(account)
        for label in labels:
            scope1_total = 0
            scope2_total = 0
            if reporting_accounts:
                scope1_emissions = self.get_scope_query(
                    'ghg-emissions-total-scope-1-emissions',
                    reporting_accounts,
                    label)
                scope2_emissions = self.get_scope_query(
                    'ghg-emissions-total-scope-2-emissions',
                    reporting_accounts,
                    label)
                with connection.cursor() as cursor:
                    cursor.execute(scope1_emissions, params=None)
                    for emissions in cursor.fetchall():
                        # for reference:
                        #   account_id = emissions[0]
                        #   created_at = emissions[1]
                        measured = emissions[2]
                        scope1_total += measured
                with connection.cursor() as cursor:
                    cursor.execute(scope2_emissions, params=None)
                    for emissions in cursor.fetchall():
                        # for reference:
                        #   account_id = emissions[0]
                        #   created_at = emissions[1]
                        measured = emissions[2]
                        scope2_total += measured
            values += [[label, scope1_total + scope2_total]]
        return values


class GHGEmissionsAmountAPIView(GHGEmissionsAmountMixin,
                                generics.RetrieveAPIView):
    """
    Retrieves GHG emissions reported (in tons)

    Returns the total GHG emissions in tons of reporting accounts
    (for reporting accounts that actually report emissions).

    **Tags**: reporting

    **Examples**

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/ghg-emissions-amount HTTP/1.1

    responds

    .. code-block:: json

        {
          "title":  "GHG emissions reported",
          "scale": 1,
          "unit": "tons",
          "results":[{
            "slug": "energy-utility",
            "printable_name": "Energy utility",
            "values":[
            ]
          }, {
            "slug": "alliance",
            "printable_name": "Alliance",
            "values":[
            ]
          }]
        }
    """
    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_response_data(request, *args, **kwargs))
