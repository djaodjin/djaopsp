# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

#pylint:disable=no-name-in-module,import-error,unused-import
from django.utils.six.moves.urllib.parse import urljoin

try:
    from django.contrib.auth import get_user_model
except ImportError: # django < 1.5
    from django.contrib.auth.models import User #pylint: disable=unused-import
else:
    User = get_user_model()                     #pylint: disable=invalid-name
