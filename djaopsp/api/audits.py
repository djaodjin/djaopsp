# Copyright (c) 2026, DjaoDjin inc.
# see LICENSE.

import logging

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import models, transaction
from rest_framework import generics
from rest_framework import response as http
from survey.helpers import construct_weekly_periods, datetime_or_now
from survey.models import Sample
from survey.utils import get_engaged_accounts

from ..compat import gettext_lazy as _, reverse
from ..mixins import AccountMixin, CampaignMixin, ReportMixin
from ..models import VerifiedSample
from ..helpers import as_percentage
from .portfolios import CompletionRateMixin
from .serializers import ReportingSerializer, VerifiedSampleSerializer

LOGGER = logging.getLogger(__name__)


class VerificationListAPIView(CampaignMixin, AccountMixin,
                              generics.ListAPIView):
    """
    Lists verifications

    **Tags**: reporting

    **Examples

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability-verified/notes HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 1,
          "next": null,
          "previous": null,
          "results": [
              {
                "grantee": "energy-utility",
                "account": "supplier-1",
                "campaign": "sustainability",
                "created_at": "2022-01-01T00:00:00Z",
                "ends_at": "2023-01-01T00:00:00Z",
                "state": "request-denied",
                "api_accept": null,
                "reporting_status": "completed",
                "last_activity_at": "2022-11-01T00:00:00Z",
                "requested_at": "2022-01-01T00:00:00Z"
              },
              {
                "grantee": "energy-utility",
                "account": "andy-shop",
                "campaign": "sustainability",
                "created_at": "2022-01-01T00:00:00Z",
                "ends_at": "2023-01-01T00:00:00Z",
                "state": "request-accepted",
                "api_accept": null,
                "reporting_status": "completed",
                "last_activity_at": "2022-11-01T00:00:00Z",
                "requested_at": "2022-01-01T00:00:00Z"
              }
          ]
        }
    """
    # Implementation is very close to `CompletedAssessmentsMixin`.
    serializer_class = ReportingSerializer

    def get_queryset(self):
        queryset = Sample.objects.filter(
            verified__verifier_notes__campaign=self.campaign,
            verified__verifier_notes__account=self.account).annotate(
                last_completed_at=models.F('created_at'),
                account_slug=models.F('account__slug'),
                printable_name=models.F('account__full_name'),
                email=models.F('account__email'),
                segment=models.F('campaign__title')).select_related('verified')
        return queryset

    def decorate_queryset(self, queryset):
        for sample in queryset:
            sample.score_url = reverse('scorecard',
                args=(self.account, sample.slug)) # The broker should be able
            # to access all scorecards without requiring a `Portfolio` record
            # to exist.
            sample.notes_url = reverse('api_verifier_notes_index',
                args=(self.account, sample.slug))
            try:
                sample.verified_status = sample.verified.verified_status
                sample.verified_by = sample.verified.verified_by
            except VerifiedSample.DoesNotExist: #RelatedObjectDoesNotExist:
                sample.verified_status = VerifiedSample.STATUS_NO_REVIEW
                sample.verified_by = None
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            self.decorate_queryset(page)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        self.decorate_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return http.Response(serializer.data)


class VerifierNotesIndexAPIView(ReportMixin, generics.UpdateAPIView):

    schema = None # XXX temporarily disable API doc

    def get_serializer_class(self):
        if self.request.method.lower() in ['put', 'patch']:
            return VerifiedSampleSerializer
        return super(VerifierNotesIndexAPIView, self).get_serializer_class()

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Updates verified status

        Updates the verification status

        **Tags**: assessments

        **Examples

        .. code-block:: http

            PUT /api/supplier-1/sample/0123456789abcdef/notes HTTP/1.1

        .. code-block:: json

            {
              "verified_status": ""
            }

        responds

        .. code-block:: json

            {
              "slug": "0123456789abcdef",
              "account": "supplier-1",
              "created_at": "2020-01-01T00:00:00Z",
              "is_frozen": true,
              "campaign": null,
              "updated_at": "2020-01-01T00:00:00Z"
            }
        """
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        verification = serializer.instance
        verified_status = serializer.validated_data.get('verified_status')
        verified_by = None
        if verified_status != VerifiedSample.STATUS_NO_REVIEW:
            verified_by = serializer.validated_data.get('verified_by')
            if not verified_by:
                verified_by = self.request.user
        if verification:
            verification.verified_by = verified_by
            verification.verified_status = verified_status
            verification.verifier_notes.is_frozen = bool(
                verified_status >= VerifiedSample.STATUS_REVIEW_COMPLETED)
            with transaction.atomic():
                verification.verifier_notes.save()
                verification.save()

    def get_object(self):
        return self.get_or_create_verification()


class VerifiedStatsAPIView(CompletionRateMixin, generics.RetrieveAPIView):
    """
    Retrieves week-by-week verification rate

    Returns the verification completed week-by-week.

    **Tags**: reporting

    **Examples**

    .. code-block:: http

        GET /api/energy-utility/reporting/notes HTTP/1.1

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
    def get_response_data(self, request, *args, **kwargs):
        #pylint:disable=unused-argument,too-many-locals
        completed_values, verified_values = completed_verified_by_week(
            self.account, campaign=self.campaign,
            start_at=self.accounts_start_at, ends_at=self.accounts_ends_at,
            search_terms=self.search_terms,
            is_percentage=self.is_percentage)
        table = [{
            'slug': 'completed',
            'title': _('Completed'),
            'values': completed_values
        }, {
            'slug': 'verified',
            'title': _('Verified'),
            'values': verified_values
        }]
        return {
            "title": self.title,
            'scale': self.scale,
            'unit': self.unit,
            'results': table
        }

    def retrieve(self, request, *args, **kwargs):
        resp = self.get_response_data(request, *args, **kwargs)
        return http.Response(resp)


def completed_verified_by_week(grantee, campaign=None,
                               start_at=None, ends_at=None, search_terms=None,
                               is_percentage=False):
    """
    Returns two lists with completed and verified samples per week.
    """
    #pylint:disable=too-many-arguments,too-many-positional-arguments
    #pylint:disable=too-many-locals
    last_date = datetime_or_now(ends_at)
    if start_at:
        first_date = start_at
    else:
        first_date = last_date - relativedelta(months=4)

    completed_values = []
    verified_values = []
    weekends_at = construct_weekly_periods(first_date, last_date, years=0)
    if len(weekends_at) < 2:
        # Not enough time periods
        return completed_values, verified_values

    period_start_at = weekends_at[0]
    frozen_samples_kwargs = {}
    if campaign:
        frozen_samples_kwargs.update({'campaign': campaign})
    if str(grantee) not in settings.UNLOCK_BROKERS:
        requested_accounts = get_engaged_accounts([grantee],
            campaign=campaign, aggregate_set=False, # XXX use True for alliances
            start_at=start_at, ends_at=ends_at,
            search_terms=search_terms)
        frozen_samples_kwargs.update({'account_id__in': requested_accounts})
    for period_ends_at in weekends_at[1:]:
        frozen_samples = Sample.objects.filter(
            extra__isnull=True,
            is_frozen=True,
            created_at__gte=period_start_at,
            created_at__lt=period_ends_at,
            **frozen_samples_kwargs)
        nb_verified_samples = VerifiedSample.objects.filter(
            sample__in=frozen_samples,
            verified_status__gte=VerifiedSample.STATUS_REVIEW_COMPLETED
        ).count()
        nb_frozen_samples = frozen_samples.count()
        period_start_at = period_ends_at

        if is_percentage:
            rate = as_percentage(nb_frozen_samples, nb_frozen_samples)
        else:
            rate = nb_frozen_samples
        completed_values += [(period_ends_at, rate)]
        if is_percentage:
            rate = as_percentage(nb_verified_samples, nb_frozen_samples)
        else:
            rate = nb_verified_samples
        verified_values += [(period_ends_at, rate)]

    return completed_values, verified_values
