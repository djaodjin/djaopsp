# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from django.conf import settings

def feature_flags(request): #pylint:disable=unused-argument
    return {'FEATURES_VUEJS': settings.FEATURES_VUEJS}
