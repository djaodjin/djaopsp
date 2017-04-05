# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from rest_framework import generics
from survey.utils import get_account_model

from ..mixins import PermissionMixin
from ..serializers import AccountSerializer
from .benchmark import BenchmarkMixin


class SupplierListAPIView(BenchmarkMixin, PermissionMixin,
                          generics.ListAPIView):
    """
    List of suppliers accessible by the request user
    with normalized (total) score when the supplier completed
    a self-assessment.

    GET /api/suppliers

    Example Response:

        {
          "count":1,
          "next":null
          "previous":null,
          "results":[{
             "slug":"andy-shop",
             "printable_name":"Andy's Shop",
             "created_at": "2017-01-01",
             "normalized_score":94
          }]
        }
    """

    serializer_class = AccountSerializer

    def get_queryset(self):
        results = []
        rollup_tree = self.rollup_scores()
        account_scores = rollup_tree[0]['accounts']
        account_model = get_account_model()
        for org_slug in self.accessibles():
            try:
                account = account_model.objects.get(slug=org_slug)
                score = account_scores.get(account.pk, None)
                dct = {'slug': org_slug,
                    'printable_name': account.printable_name}
                if score is not None:
                    created_at = score.get('created_at', None)
                    if created_at:
                        dct.update({'last_activity_at': created_at})
                    nb_answers = score.get('nb_answers', 0)
                    nb_questions = score.get('nb_questions', 0)
                    if nb_answers == nb_questions:
                        normalized_score = score.get('normalized_score', None)
                    else:
                        normalized_score = None
                    if normalized_score is not None:
                        dct.update({'normalized_score': normalized_score})
                results += [dct]
            except account_model.DoesNotExist:
                pass
        return results
