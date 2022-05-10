# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from django.conf import settings

from ..compat import import_string, six


class ScoreCalculator(object):
    """
    Abstract base class to compute scores on individual answers
    for an assessment
    """
    def get_scored_answers(self, campaign,
                           prefix=None, includes=None, excludes=None):
        #pylint:disable=unused-argument,no-self-use
        return []

    def get_opportunity(self, last_frozen_assessments,
                        prefix=None, includes=None, excludes=None):
        """
        Lists opportunity (intrisic and peers-based)
        """
        #pylint:disable=unused-argument,no-self-use
        return []


def get_score_calculator(segment_path):
    """
    Returns a specific calculator for scores if one exists for
    the `segment_path`, otherwise return a default calculator.
    """
    for root_path, calculator_class in six.iteritems(
            settings.SCORE_CALCULATORS):
        if segment_path.startswith(root_path):
            return import_string(calculator_class)()
    return None
