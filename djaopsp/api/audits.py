# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

import logging

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from rest_framework import generics
from rest_framework import response as http
from rest_framework.mixins import UpdateModelMixin
from survey.api.sample import SampleAnswersAPIView
from survey.helpers import construct_weekly_periods
from survey.models import Sample
from survey.queries import datetime_or_now

from ..mixins import ReportMixin
from ..models import VerifiedSample
from ..helpers import as_percentage
from .portfolios import CompletionRateMixin
from .serializers import VerifiedSampleSerializer

LOGGER = logging.getLogger(__name__)


class VerifierNotesAPIView(ReportMixin, SampleAnswersAPIView):
    """
    Lists verifier notes

    The list returned contains at least one measurement for each question
    in the campaign. If there are no measurement yet on a question, ``measured``
    will be null.

    There might be more than one measurement per question as long as there are
    no duplicated ``unit`` per question. For example, to the question
    ``adjust-air-fuel-ratio``, there could be a measurement with unit
    ``assessment`` (Mostly Yes/ Yes / No / Mostly No) and a measurement with
    unit ``freetext`` (i.e. a comment).

    The {sample} must belong to {organization}.

    {path} can be used to filter the tree of questions by a prefix.

    **Tags**: assessments

    **Examples**

    .. code-block:: http

         GET /api/supplier-1/sample/46f66f70f5ad41b29c4df08f683a9a7a/answers\
/construction HTTP/1.1

    responds

    .. code-block:: json

    {
        "count": 3,
        "previous": null,
        "next": null,
        "results": [
            {
                "question": {
                    "path": "/construction/governance/the-assessment\
-process-is-rigorous",
                    "title": "The assessment process is rigorous",
                    "default_unit": {
                        "slug": "assessment",
                        "title": "assessments",
                        "system": "enum",
                        "choices": [
                        {
                            "rank": 1,
                            "text": "mostly-yes",
                            "descr": "Mostly yes"
                        },
                        {
                            "rank": 2,
                            "text": "yes",
                            "descr": "Yes"
                        },
                        {
                            "rank": 3,
                            "text": "no",
                            "descr": "No"
                        },
                        {
                            "rank": 4,
                            "text": "mostly-no",
                            "descr": "Mostly no"
                        }
                        ]
                    },
                    "ui_hint": "radio"
                },
                "required": true,
                "measured": "yes",
                "unit": "assessment",
                "created_at": "2020-09-28T00:00:00.000000Z",
                "collected_by": "steve"
            },
            {
                "question": {
                    "path": "/construction/governance/the-assessment\
-process-is-rigorous",
                    "title": "The assessment process is rigorous",
                    "default_unit": {
                        "slug": "assessment",
                        "title": "assessments",
                        "system": "enum",
                        "choices": [
                        {
                            "rank": 1,
                            "text": "mostly-yes",
                            "descr": "Mostly yes"
                        },
                        {
                            "rank": 2,
                            "text": "yes",
                            "descr": "Yes"
                        },
                        {
                            "rank": 3,
                            "text": "no",
                            "descr": "No"
                        },
                        {
                            "rank": 4,
                            "text": "mostly-no",
                            "descr": "Mostly no"
                        }
                        ]
                    },
                    "ui_hint": "radio"
                },
                "measured": "Policy document on the public website",
                "unit": "freetext",
                "created_at": "2020-09-28T00:00:00.000000Z",
                "collected_by": "steve"
            },
            {
                "question": {
                    "path": "/construction/production/adjust-air-fuel\
-ratio",
                    "title": "Adjust Air fuel ratio",
                    "default_unit": {
                        "slug": "assessment",
                        "title": "assessments",
                        "system": "enum",
                        "choices": [
                        {
                            "rank": 1,
                            "text": "mostly-yes",
                            "descr": "Mostly yes"
                        },
                        {
                            "rank": 2,
                            "text": "yes",
                            "descr": "Yes"
                        },
                        {
                            "rank": 3,
                            "text": "no",
                            "descr": "No"
                        },
                        {
                            "rank": 4,
                            "text": "mostly-no",
                            "descr": "Mostly no"
                        }
                        ]
                    },
                    "ui_hint": "radio"
                },
                "required": true,
                "measured": null,
                "unit": null
            }
         ]
    }
    """
    schema = None # XXX temporarily disable API doc

    def post(self, request, *args, **kwargs):
        """
        Adds verifier notes to an answer

        A frozen sample cannot be edited to add and/or update answers.

        **Tags**: assessments

        **Examples

        .. code-block:: http

            POST /api/supplier-1/sample/0123456789abcdef/notes/construction \
 HTTP/1.1

        .. code-block:: json

            {}

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
        #pylint:disable=useless-super-delegation
        return super(VerifierNotesAPIView, self).post(
            request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        verification = self.get_or_create_verification()
        if verification.verifier_notes == self.sample:
            verification.verified_by = self.request.user
            verification.verified_status = VerifiedSample.STATUS_UNDER_REVIEW
            verification.save()
        return super(VerifierNotesAPIView, self).create(
            request, *args, **kwargs)


class VerifierNotesIndexAPIView(UpdateModelMixin, VerifierNotesAPIView):

    schema = None # XXX temporarily disable API doc

    def get_serializer_class(self):
        if self.request.method.lower() in ['put', 'patch']:
            return VerifiedSampleSerializer
        return super(VerifierNotesAPIView, self).get_serializer_class()

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Adds verifier notes to a sample

        A frozen sample cannot be edited to add and/or update answers.

        **Tags**: assessments

        **Examples

        .. code-block:: http

            POST /api/supplier-1/sample/0123456789abcdef/notes HTTP/1.1

        .. code-block:: json

            {}

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
        #pylint:disable=useless-super-delegation
        return super(VerifierNotesIndexAPIView, self).post(
            request, *args, **kwargs)

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
        verification.verified_by = self.request.user
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
    Retrieves verification completed

    Returns the verification completed week-by-week.

    **Tags**: reporting

    **Examples**

    .. code-block:: http

        GET /api/energy-utility/reporting/sustainability/engagement/stats\
 HTTP/1.1

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
        account = self.account
        last_date = datetime_or_now(self.accounts_ends_at)
        if self.accounts_start_at:
            first_date = self.accounts_start_at
        else:
            first_date = last_date - relativedelta(months=4)
        weekends_at = construct_weekly_periods(
            first_date, last_date, years=0)
        if len(weekends_at) < 2:
            # Not enough time periods
            return []

        completed_values = []
        verified_values = []
        requested_accounts = self.get_requested_accounts(
            account, aggregate_set=False)
        start_at = weekends_at[0]
        frozen_samples_kwargs = {}
        if str(self.account) not in settings.UNLOCK_BROKERS:
            frozen_samples_kwargs = {'account_id__in': requested_accounts}
        for ends_at in weekends_at[1:]:
            frozen_samples = Sample.objects.filter(
                extra__isnull=True,
                is_frozen=True,
                created_at__gte=start_at,
                created_at__lt=ends_at,
                **frozen_samples_kwargs)
            nb_verified_samples = VerifiedSample.objects.filter(
                sample__in=frozen_samples,
                verified_status__gte=VerifiedSample.STATUS_REVIEW_COMPLETED
            ).count()
            nb_frozen_samples = frozen_samples.count()

            if self.is_percentage:
                rate = as_percentage(nb_frozen_samples, nb_frozen_samples)
            else:
                rate = nb_frozen_samples
            completed_values += [(ends_at, rate)]
            if self.is_percentage:
                rate = as_percentage(nb_verified_samples, nb_frozen_samples)
            else:
                rate = nb_verified_samples
            verified_values += [(ends_at, rate)]
            start_at = ends_at

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
