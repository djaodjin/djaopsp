# Copyright (c) 2023, DjaoDjin inc.
# see LICENSE.

def as_percentage(val, total):
    return round(val * 100 / total) if total else 0


def as_valid_sheet_title(title):
    """
    Prevents 'Invalid character / found in sheet title' errors.
    """
    return title.replace('/', '-')
