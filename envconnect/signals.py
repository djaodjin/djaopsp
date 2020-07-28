# Copyright (c) 2020, DjaoDjin inc.
# see LICENSE.

from answers.models import Follow, get_question_model
from answers.signals import question_new
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.contrib.sites.requests import RequestSite
from django.dispatch import Signal, receiver
from django_comments.signals import comment_was_posted
from extended_templates.backends import get_email_backend

from .compat import reverse


assessment_completed = Signal(providing_args=[#pylint:disable=invalid-name
    'assessment', 'path', 'notified'])

#pylint: disable=unused-argument
def get_site(request):
    if Site._meta.installed: #pylint: disable=protected-access
        site = Site.objects.get_current()
    else:
        site = RequestSite(request)
    return site


@receiver(question_new, dispatch_uid="question_new_notice")
def on_question_new(sender, question, request, *args, **kwargs):
    broker = request.session.get('site', {})
    notify_email = broker['email']
    get_email_backend().send(
        recipients=[notify_email],
        template='notification/question_new.eml',
        context={'question': question, 'site': get_site(request)})


@receiver(comment_was_posted, dispatch_uid="comment_was_posted_notice")
def on_answer_posted(sender, comment, request, *args, **kwargs):
    question_ctype = ContentType.objects.get_for_model(get_question_model())
    if comment.content_type == question_ctype:
        question = comment.content_object
        back_url = request.build_absolute_uri(request.POST.get('next', ""))
#        back_url = request.build_absolute_uri(
#            reverse('summary', args=("/%s" % question,)))
        get_email_backend().send(
            recipients=[notified.email
                for notified in Follow.objects.get_followers(question)],
            template='notification/question_updated.eml',
            context={'request': request,
                     'question': question,
                     'back_url': back_url,
                     'site': get_site(request)})
        # Subscribe the commenting user to this question
        Follow.objects.subscribe(question, user=request.user)


@receiver(assessment_completed, dispatch_uid="assessment_completed_notice")
def on_assessment_completed(assessment, path, notified, *args, **kwargs):
    request = kwargs.get('request', None)
    reason = kwargs.get('reason', None)
    recipients = [manager.email
        for manager in notified.with_role('manager')]
    if not recipients:
        # Avoids 500 errors when no managers
        recipients = [settings.DEFAULT_FROM_EMAIL]
    back_url = request.build_absolute_uri(
        reverse('scorecard_organization',
                args=(assessment.account, assessment, path)))
    get_email_backend().send(
        recipients=recipients,
        template='notification/assessment_completed.eml',
        context={'organization': assessment.account,
                 'reason': reason,
                 'back_url': back_url,
                 'site': get_site(request)})
