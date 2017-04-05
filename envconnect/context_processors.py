# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from django.contrib.sites.models import Site

def site(request): #pylint:disable=unused-argument
    return {'site': Site.objects.get_current()}
