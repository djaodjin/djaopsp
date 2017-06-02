# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import logging

from answers.models import Follow
from answers.views import (QuestionUnfollowView, QuestionFollowView,
    QuestionVoteView)
from pages.views.pages import PageElementDetailView

from ..mixins import BestPracticeMixin


LOGGER = logging.getLogger(__name__)


class BestPracticeDetailView(BestPracticeMixin, PageElementDetailView):

    context_object_name = 'best_practice'
    template_name = 'envconnect/best_practice.html'

    def get_object(self, queryset=None):
        return self.best_practice

    def get_context_data(self, *args, **kwargs):
        context = super(
            BestPracticeDetailView, self).get_context_data(*args, **kwargs)
        context.update({
            'icon': self.icon,
            'path': self.kwargs.get('path'),
            'question': self.question})
        organization = self.kwargs.get('organization', None)
        if organization:
            context.update({'organization': organization})
        if self.request.user.is_authenticated:
            context.update({'is_following': Follow.objects.get_followers(
                self.question).filter(pk=self.request.user.id).exists()})
        return context


class StarBestPracticeMixin(BestPracticeMixin):

    def get_object(self, queryset=None): #pylint: disable=unused-argument
        return self.question

    def get_redirect_url(self, *args, **kwargs): #pylint: disable=unused-argument
        return self.get_best_practice_url()


class UnfollowBestPracticeView(StarBestPracticeMixin, QuestionUnfollowView):

    pass

class FollowBestPracticeView(StarBestPracticeMixin, QuestionFollowView):

    pass


class BestPracticeVoteView(StarBestPracticeMixin, QuestionVoteView):

    pass
