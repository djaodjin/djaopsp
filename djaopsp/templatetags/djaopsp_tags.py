# Copyright (c) 2024, DjaoDjin inc.
# see LICENSE

from deployutils.apps.django.compat import (
    is_authenticated as base_is_authenticated)
from django import template
from django.contrib.messages.api import get_messages
from django.forms import widgets, BaseForm
from django.template.defaultfilters import capfirst
from django.utils.encoding import force_text
from survey.helpers import datetime_or_now

from ..compat import reverse, six


register = template.Library()

@register.filter()
def no_cache(asset_url):
    pos = asset_url.rfind('?')
    if pos > 0:
        asset_url = asset_url[:pos]
    return asset_url

@register.filter()
def capitalize(text):
    return capfirst(text)


@register.filter()
def date(at_time):
    return datetime_or_now(at_time).strftime('%Y-%m-%d')


@register.filter()
def messages(obj):
    """
    Messages to be displayed to the current session.
    """
    if isinstance(obj, BaseForm):
        return obj.non_field_errors()
    return get_messages(obj)


@register.filter()
def pluralize(text):
    if text.endswith('s'):
        return text
    return text + 's'


@register.filter()
def rstrip_sep(path):
    return path.rstrip('/')


@register.simple_tag
def is_active(path, urls, *args, **kwargs): #pylint: disable=unused-argument
    if path in (reverse(urls, kwargs=kwargs) for url in urls.split()):
        return "active"
    return ""


@register.filter()
def is_authenticated(request):
    return base_is_authenticated(request)


@register.filter()
def is_checkbox(field):
    return isinstance(field.widget, widgets.CheckboxInput)


@register.filter()
def is_radio(field):
    return isinstance(field.widget, widgets.RadioSelect)


@register.filter()
def is_textarea(field):
    return isinstance(field.widget, widgets.Textarea)


@register.filter()
def iterfields(form):
    return six.iteritems(form.fields)


@register.filter()
def get_bounded_field(form, key):
    bounded_field = form[key]
    if bounded_field is None:
        raise KeyError("%s not found in form" % key)
    return bounded_field


@register.filter()
def value_attr(field):
    if hasattr(field, 'value'):
        value = field.value()
        if value is None:
            value = ""
        if value != "":
            return 'value=%s' % force_text(value)
    return ""


@register.filter()
def query_parameters(api_endpoint):
    results = []
    for param in api_endpoint.get('parameters', []):
        if param['in'] == 'query':
            param['type'] = param['schema']['type']
            results += [param]
    return results


@register.filter()
def request_body_parameters(api_endpoint, defs):
    if 'requestBody' not in api_endpoint:
        return []

    results = []
    schema = \
        api_endpoint['requestBody']['content']['application/json']['schema']
    if '$ref' in schema:
        key = schema['$ref'].split('/')[-1]
        schema = defs[(key, 'schemas')].schema
    if 'properties' in schema:
        for prop_name, prop in schema['properties'].items():
            if ('required' not in prop and
                prop_name in schema.get('required', [])):
                prop.update({'required': True})
            if 'type' not in prop:
                first_enum = prop.get('allOf',[{}])[0]
                if '$ref' in first_enum:
                    key = first_enum['$ref'].split('/')[-1]
                    prop.update(defs[(key, 'schemas')].schema)
            prop.update({'name': prop_name})
            if 'type' not in prop and 'enum' in prop:
                prop.update({'type': "String"}) # XXX Country enum
            results += [prop]
    return results


@register.filter()
def responses_parameters(api_endpoint, defs):
    #pylint:disable=too-many-nested-blocks
    if 'responses' not in api_endpoint:
        return []
    results = {}
    for resp_code, param in api_endpoint['responses'].items():
        params = []
        if 'content' in param:
            schema = param['content']['application/json']['schema']
            if '$ref' in schema:
                key = schema['$ref'].split('/')[-1]
                schema = defs[(key, 'schemas')].schema
            if 'properties' in schema:
                for prop_name, prop in schema['properties'].items():
                    if 'type' not in prop:
                        first_enum = prop.get('allOf',[{}])[0]
                        if '$ref' in first_enum:
                            key = first_enum['$ref'].split('/')[-1]
                            prop.update(defs[(key, 'schemas')].schema)
                    prop.update({'name': prop_name})
                    if 'type' not in prop and 'enum' in prop:
                        prop.update({'type': "String"}) # XXX Country enum
                    params += [prop]
        results.update({resp_code: params})
    return results


def schema_properties(schema, defs):
    params = []
    if schema['type'] == 'array':
        schema = schema.get('items', {})
    if '$ref' in schema:
        key = schema['$ref'].split('/')[-1]
        schema = defs[(key, 'schemas')].schema
    if 'properties' in schema:
        for prop_name, prop in schema['properties'].items():
            try:
                if ('required' not in prop and
                    prop_name in schema.get('required', [])):
                    prop.update({'required': True})
            except TypeError:
                # `required` is not always a dictionnary. It could be a `bool`??
                pass
            if 'type' not in prop:
                first_enum = prop.get('allOf',[{}])[0]
                if '$ref' in first_enum:
                    key = first_enum['$ref'].split('/')[-1]
                    prop.update(defs[(key, 'schemas')].schema)
            prop.update({'name': prop_name})
            if 'type' not in prop and 'enum' in prop:
                prop.update({'type': "String"}) # XXX Country enum
            params += [prop]
    return params


@register.filter()
def not_key(param_name):
    return not (param_name.lower() == 'password'
            or param_name.lower().endswith('_key')
            or param_name.lower().endswith('_password'))

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
