# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import os

from django_assets import Bundle, register
from django.conf import settings

#pylint: disable=invalid-name

# All the CSS we need for the entire site. This tradeoff between
# bandwidth and latency is good as long as we have a high and consistent
# utilization of all the CSS tags for all pages on the site.
css_base = Bundle(
    Bundle(os.path.join(
        settings.BASE_DIR, 'assets/less/envconnect-bootstrap.less'),
        filters='less', output='cache/bootstrap.css', debug=False),
    'vendor/font-awesome.css',
    'vendor/nv.d3.css',
    'vendor/c3.css',
    'vendor/trip.css',
    'vendor/bootstrap-toggle.css',
    'css/matrix-chart.css',
    filters='cssmin', output='cache/envconnect.css')
register('css_base', css_base)

# Minimal: jquery and bootstrap always active on the site
js_base = Bundle('vendor/jquery.js',
                 'vendor/bootstrap.js',
                 'vendor/bootbox.js',
                 'vendor/jquery.selection.js',
                 'vendor/trip.js',
            filters='yui_js', output='cache/envconnect.js')
register('js_base', js_base)

css_editor = Bundle(
    'vendor/jquery-ui.css',
    'css/djaodjin-editor.css',
    'css/djaodjin-sidebar-gallery.css',
    filters='cssmin', output='cache/editor.css')
register('css_editor', css_editor)

js_editor = Bundle(
    'vendor/typeahead.bundle.js',
    'vendor/dropzone.js',
    'vendor/jquery-ui.js',
    'vendor/jquery.ui.touch-punch.js',
    'vendor/rangy-core.js',
    'vendor/hallo.js',
    'js/djaodjin-editor.js',
    'js/djaodjin-upload.js',
    'js/djaodjin-sidebar-gallery.js',
    filters='jsmin', output='cache/editor.js')
register('js_editor', js_editor)

js_angular = Bundle(
    'vendor/angular.min.js',
    'vendor/angular-touch.min.js',
    'vendor/angular-animate.min.js',
    'vendor/angular-dragdrop.js',
    'vendor/angular-route.min.js',
    'vendor/angular-sanitize.js',
    'vendor/angular-bootstrap-tpls.js',
    filters='jsmin', output='cache/angular.js')
register('js_angular', js_angular)

js_envconnect = Bundle(
    'vendor/d3.js',
    'vendor/nv.d3.js',
    'vendor/c3.js',
    'vendor/bootstrap-toggle.js',
    'js/djaodjin-resources.js',
    'js/djaodjin-survey.js',
    'js/djaodjin-set.js',
    'js/djaodjin-categorize.js',
    'js/djaodjin-matrix.js',
    'js/matrix-chart.js',
    'js/envconnect.js',
    'js/draw-chart.js',
    filters='jsmin', output='cache/envconnect-app.js')
register('js_envconnect', js_envconnect)
