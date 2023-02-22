# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.
import datetime

from dateutil.relativedelta import relativedelta, SU

from pytz import timezone, UnknownTimeZoneError
from pytz.tzinfo import DstTzInfo


def as_valid_sheet_title(title):
    """
    Prevents 'Invalid character / found in sheet title' errors.
    """
    return title.replace('/', '-')


def parse_tz(tzone):
    if issubclass(type(tzone), DstTzInfo):
        return tzone
    if tzone:
        try:
            return timezone(tzone)
        except UnknownTimeZoneError:
            pass
    return None
