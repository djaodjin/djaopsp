# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.
"""
This file contains helper functions that are used accross the project
but do not fit nicely into the API/Views class hierarchy.
Furthermore this functions rely on the models to be loaded. For pure
helper functions that do not rely on the order Django loads the modules,
see the file helpers.py in the same directory.
"""
import json

from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from pages.helpers import ContentCut
from pages.models import PageElement, build_content_tree, flatten_content_tree
from survey.models import Answer, Choice, Sample, Unit
from survey.utils import get_question_model, is_sqlite3


DB_PATH_SEP = '/'

def get_account_model():
    """
    Returns the ``Account`` model that is active in this project.
    """
    try:
        return django_apps.get_model(settings.ACCOUNT_MODEL)
    except ValueError:
        raise ImproperlyConfigured(
            "ACCOUNT_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured("ACCOUNT_MODEL refers to model '%s'"\
" that has not been installed" % settings.ACCOUNT_MODEL)


def get_highlights(sample):
    campaign_extra = sample.campaign.extra
    if not isinstance(campaign_extra, dict):
        try:
            campaign_extra = json.loads(campaign_extra)
        except (TypeError, ValueError):
            campaign_extra = {}
    highlights = campaign_extra.get('highlights', [])
    for highlight in highlights:
        reporting = False
        filter_q = None
        for include in highlight.get('includes'):
            if filter_q:
                filter_q |= models.Q(
                    path__endswith=DB_PATH_SEP + include)
            else:
                filter_q = models.Q(
                    path__endswith=DB_PATH_SEP + include)
        includes = get_question_model().objects.filter(filter_q).values(
            'id', 'default_unit_id')
        if includes:
            positive = Choice.objects.filter(
                unit=includes[0].get('default_unit_id')).order_by(
                'rank').first()
            reporting = Answer.objects.filter(
                question__in=[incl.get('id') for incl in includes],
                sample=sample, unit__system=Unit.SYSTEM_ENUMERATED,
                measured=positive.pk).exists()
        highlight.update({'reporting': reporting})
    return highlights


def get_latest_active_assessments(account, campaign=None):
    kwargs = {}
    if campaign:
        kwargs.update({'campaign': campaign})
    if isinstance(account, get_account_model()):
        kwargs.update({'account': account})
    else:
        kwargs.update({'account__slug': str(account)})
    return Sample.objects.filter(
        is_frozen=False, **kwargs).order_by('-created_at').select_related(
            'campaign', 'account')


def get_latest_completed_assessment(account, campaign=None):
    kwargs = {}
    if campaign:
        kwargs.update({'campaign': campaign})
    if isinstance(account, get_account_model()):
        kwargs.update({'account': account})
    else:
        kwargs.update({'account__slug': str(account)})
    return Sample.objects.filter(
        is_frozen=True, extra__isnull=True,
        **kwargs).order_by('-created_at').select_related(
            'campaign', 'account').first()


def _get_segments_query(segments):
    segments_query = None
    for segment in segments:
        if segments_query:
            segments_query = "%(segments_query)s UNION "\
                "SELECT '%(segment_path)s'%(convert_to_text)s AS path,"\
                " '%(segment_title)s'%(convert_to_text)s AS title" % {
                    'segments_query': segments_query,
                    'segment_path': segment['path'],
                    'segment_title': segment['title'],
                    'convert_to_text': ("" if is_sqlite3() else "::text")
                }
        else:
            segments_query = \
                "SELECT '%(segment_path)s'%(convert_to_text)s AS path,"\
                " '%(segment_title)s'%(convert_to_text)s AS title" % {
                    'segment_path': segment['path'],
                    'segment_title': segment['title'],
                    'convert_to_text': ("" if is_sqlite3() else "::text")
                }
    return segments_query


def get_segments_available(sample, visibility=None, owners=None,
                           segments_candidates=None):
    """
    All segments that have at least one answer
    """
    if not segments_candidates:
        segments_candidates = get_segments_candidates(
            sample.campaign, visibility=visibility, owners=owners)
    candidates = [seg for seg in segments_candidates
        if seg.get('extra', {}).get('pagebreak', False)]
    results = []
    for seg in candidates:
        prefix = seg['path']
        is_active = get_question_model().objects.filter(
            path__startswith=prefix, answer__sample=sample).exists()
        if is_active:
            results += [seg]
    return results


def get_segments_candidates(campaign, visibility=None, owners=None):
    """
    All segments that are candidates based on a campaign.
    """
    candidates = set([])
    for path in get_question_model().objects.filter(
        enumeratedquestions__campaign=campaign).values_list(
        'path', flat=True):
        candidates |= set([path.strip(DB_PATH_SEP).split(DB_PATH_SEP)[0]])
    if candidates:
        roots = PageElement.objects.get_roots(
            visibility=visibility, accounts=owners).filter(
            slug__in=candidates).order_by('title')
        content_tree = build_content_tree(roots=roots, prefix=DB_PATH_SEP,
            cut=ContentCut(), visibility=visibility, accounts=owners)
        return flatten_content_tree(content_tree)
    return []
