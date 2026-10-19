# Copyright (c) 2026, DjaoDjin inc.
# see LICENSE.

from survey.api.matrix import AffinityFilterAPIView as AffinityFilterBaseAPIView

from ..mixins import AccountMixin


class AffinityFilterAPIView(AccountMixin, AffinityFilterBaseAPIView):
    """
    Lists sets of profiles selected by affinity

    Returns a list of {{PAGE_SIZE}} affinity sets available to `{profile}`.

    The queryset can be further refined to match a search filter (``q``)
    and sorted on specific fields (``o``).

    **Tags**: cohorts

    **Examples**:

    .. code-block:: http

        GET /api/energy-utility/filters/affinity HTTP/1.1

    responds

    .. code-block:: json

        {
            "count": 1,
            "previous": null,
            "next": null,
            "results": [
            {
               "slug": "all",
               "title": "All profiles",
               "extra": null
           }]
        }
    """
    def get_queryset(self):
        results = []
        for plan in self.get_accessible_plans(
                self.request, profile=self.account):
            slug = plan.get('slug')
            # XXX title is not passed through the `request.session`, yet
            # we need in the serializer.
            results += [{'slug': slug, 'title': plan.get('title', slug)}]
        return results
