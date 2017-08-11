# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging

from answers.views import (QuestionUnfollowView, QuestionFollowView,
    QuestionVoteView)

from ..mixins import BestPracticeMixin


LOGGER = logging.getLogger(__name__)


class StarBestPracticeMixin(BestPracticeMixin):

    def get_object(self, queryset=None): #pylint: disable=unused-argument
        return self.question

    def get_redirect_url(self, *args, **kwargs): #pylint: disable=unused-argument
        return self.get_breadcrumb_url(self.kwargs.get('path'))


class UnfollowBestPracticeView(StarBestPracticeMixin, QuestionUnfollowView):

    pass

class FollowBestPracticeView(StarBestPracticeMixin, QuestionFollowView):

    pass


class BestPracticeVoteView(StarBestPracticeMixin, QuestionVoteView):

    pass
