# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE.

def as_valid_sheet_title(title):
    """
    Prevents 'Invalid character / found in sheet title' errors.
    """
    return title.replace('/', '-')
