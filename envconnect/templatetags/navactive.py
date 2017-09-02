# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import json, markdown, re

from django.conf import settings
from django import template
from django.core.urlresolvers import reverse
from django.utils import six
from django.utils.safestring import mark_safe
from pages.models import PageElement

from ..models import Consumption

register = template.Library()

@register.filter
def is_broker_manager(request):
    # inlined version of `deployutils.AccessiblesMixin.manages`
    for organization in request.session.get('roles', {}).get('manager', []):
        if organization['slug'] == settings.APP_NAME:
            return True
    return False


@register.filter
def assessment_choices(tag):
    return Consumption.ASSESSMENT_CHOICES.get(tag,
        Consumption.ASSESSMENT_CHOICES.get('default'))

@register.filter
def is_icon(title):
    """
    Returns True if the title passed as an argument can be interpreted
    as a path to an image asset.
    """
    return title.endswith('.png')


@register.filter
def as_icon(breadcrumbs):
    icon = {}
    if len(breadcrumbs) >= 2:
        icon.update({
            'subtitle': breadcrumbs[-1][0].title
        })
    return icon


@register.filter
def get_industry_charts(organization=None):
    charts = PageElement.objects.filter(
        tag__contains='industry').filter(tag__contains='enabled')
    for chart in charts:
        chart.breadcrumbs = [chart.title]
        chart.urls = {'matrix_api': reverse(
            'matrix_api', args=(organization, chart.slug,))}
    return charts


@register.filter
def active_category(breadcrumbs, category):
    for breadcrumb in breadcrumbs:
        try:
            if category in breadcrumb[0].tag:
                return True
        except TypeError:
            # tag might be `None`.
            pass
    return False


@register.filter
def category_entry(breadcrumbs, category=None):
    path = ""
    for breadcrumb in breadcrumbs:
        for tag in ['basic', 'sustainability']:
            if breadcrumb[0].tag and tag in breadcrumb[0].tag:
                if category:
                    look = re.match(r'^[^-]+(-\S+)', breadcrumb[0].slug)
                    path += "/" + category + look.group(1)
                else:
                    path += "/" + breadcrumb[0].slug
                return path
        path += "/" + breadcrumb[0].slug
    return path


@register.filter
def nb_self_assessment_questions(practices):
    result = 0
    for practice in practices:
        if len(practice[1]) == 0:
            result += 1
        elif (len(practice[1]) > 0
              and settings.TAG_SYSTEM not in practice[0].tag):
            result += 1
    return result


@register.filter(is_safe=True)
def markdown_filter(value):
    extensions = ("tables", "nl2br")
    html = markdown.markdown(value,
        extensions,
        safe_mode='replace',
        html_replacement_text='<em>RAW HTML NOT ALLOWED</em>',
        enable_attributes=False)
    html = html.replace('<p><img ', '<p class="markdown-image"><img ')
    html = html.replace('<table>', '<table class="table table-striped">')
    return mark_safe(html)


# Makdown filter for report: allow to add style on description
@register.filter(is_safe=True)
def markdown_filter_pdf(value, request):
    extensions = ("tables", "nl2br")
    host = "%s://%s" % (request.scheme, request.get_host())
    html = markdown.markdown(value,
        extensions,
        safe_mode='replace',
        html_replacement_text='<em>RAW HTML NOT ALLOWED</em>',
        enable_attributes=False)
    html = html.replace('<h1>',
        "<h1 style=\"font-size:22px;font-family:'Helvetica Neue';\
        font-weight:100;margin-bottom:0px;color:#555\">")
    html = html.replace('<h2>',
        "<h2 style=\"font-size:18px;font-family:'Helvetica Neue';\
        font-weight:100;margin-bottom:0px;color:#555\">")
    html = html.replace("src=\"",
        "src=\"%s" % host)
    html = html.replace('<h3>',
        "<h3 style=\"font-size:16px;font-family:'Helvetica Neue';\
        font-weight:100;margin-bottom:0px;color:#555\">")
    html = html.replace('<h4>',
        "<h3 style=\"font-size:14px;font-family:'Helvetica Neue';\
        font-weight:100;margin-bottom:0px;color:#555\">")
    html = html.replace('<h5>',
        "<h3 style=\"font-size:12px;font-family:'Helvetica Neue';\
        font-weight:100;margin-bottom:0px;color:#555\">")
    html = html.replace('<p>',
        "<p style=\"font-size:12px;font-family:'Helvetica Neue';\
        font-weight:100;margin-top:0px;text-align : justify;\">")
    html = html.replace('<table>',
        "<table style=\"font-size:12px;font-family:'Helvetica Neue';\
        font-weight:100;margin-top:0px;text-align : justify;\">")
    html = html.replace('<tr>',
        "<tr style=\"font-size:12px;font-family:'Helvetica Neue';\
        font-weight:100;margin-top:0px;text-align : justify;\">")
    html = html.replace('<th>',
        "<th style=\"border 1px solid black; padding:4px;\
        font-weight:100;margin-top:0px;text-align : justify;\">")
    html = html.replace('<td>',
        "<td style=\"border 1px solid black; padding:4px;\
        font-weight:100;margin-top:0px;text-align : justify;\">")
    return mark_safe(html)

@register.filter
def previous_to_last(breadcrumbs):
    return breadcrumbs[-2]


@register.filter
def containsTag(node, tag):#pylint:disable=invalid-name
    result = False
    if node:
        try:
            result = bool(node.tag) and tag in node.tag
        except AttributeError:
            try:
                result = tag in node.get('tag', '')
            except KeyError:
                pass
    return result

@register.filter
def iteritems(dic):
    return six.iteritems(dic)

@register.filter
def systems(nodes):
    return [node for node in six.itervalues(nodes) if node[0].get('tag', "")
        and settings.TAG_SCORECARD in node[0].get('tag', "")]

@register.filter
def to_json(value):
    if isinstance(value, six.string_types):
        return value
    return mark_safe(json.dumps(value))
