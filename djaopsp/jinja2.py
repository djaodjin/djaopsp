# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE

from __future__ import absolute_import

from django.conf import settings
import django.template.defaulttags
from django.utils.translation import gettext, ngettext
from deployutils.apps.django.themes import get_template_search_path
from deployutils.apps.django.templatetags import (deployutils_extratags,
    deployutils_prefixtags)
from jinja2.ext import i18n
from jinja2.sandbox import SandboxedEnvironment as Jinja2Environment

from .compat import import_string, reverse
from .templatetags import djaopsp_tags

def environment(**options):
    # If we don't force ``auto_reload`` to True, in DEBUG=0, the templates
    # would only be compiled on the first edit.
    options.update({'auto_reload': True})
    if 'loader' in options:
        if isinstance(options['loader'], str):
            loader_class = import_string(options['loader'])
        else:
            loader_class = options['loader'].__class__
        options['loader'] = loader_class(get_template_search_path())
    env = Jinja2Environment(extensions=[i18n], **options)
    # i18n
    env.install_gettext_callables(gettext=gettext, ngettext=ngettext,
        newstyle=True)
    # Generic filters to render pages
    env.filters['asset'] = deployutils_prefixtags.asset
    env.filters['absolute_uri'] = deployutils_extratags.absolute_uri
    env.filters['host'] = deployutils_extratags.host
    env.filters['is_authenticated'] = deployutils_extratags.is_authenticated
    env.filters['date'] = djaopsp_tags.date
    env.filters['messages'] = djaopsp_tags.messages
    env.filters['no_cache'] = djaopsp_tags.no_cache
    env.filters['pluralize'] = djaopsp_tags.pluralize
    env.filters['site_url'] = deployutils_prefixtags.site_url
    env.filters['to_json'] = deployutils_extratags.to_json

    # for form fields in jinja2/_form_fields.html
    env.filters['is_checkbox'] = djaopsp_tags.is_checkbox
    env.filters['is_radio'] = djaopsp_tags.is_radio
    env.filters['is_textarea'] = djaopsp_tags.is_textarea

    env.globals.update({
        'DATETIME_FORMAT': "MMM dd, yyyy",
    })
    if settings.DEBUG:
        env.filters['addslashes'] = django.template.defaultfilters.addslashes
        env.globals.update({
            'ASSETS_DEBUG': settings.ASSETS_DEBUG,
            'DEBUG': settings.DEBUG,
            'DEMO_SCREENSHOT': getattr(settings, 'DEMO_SCREENSHOT', False),
            'FEATURES_DEBUG': settings.FEATURES_DEBUG,
            'cycle': django.template.defaulttags.cycle,
            'url': reverse,
        })
    if settings.API_DEBUG:
        env.filters['query_parameters'] = \
            djaopsp_tags.query_parameters
        env.filters['request_body_parameters'] = \
            djaopsp_tags.request_body_parameters
        env.filters['responses_parameters'] = \
            djaopsp_tags.responses_parameters
        env.filters['schema_properties'] = \
            djaopsp_tags.schema_properties
        env.filters['not_key'] = \
            djaopsp_tags.not_key

    return env
