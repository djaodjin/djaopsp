# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

import os.path, sys

from django.contrib.messages import constants as messages
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import gettext_lazy as _

from deployutils.configs import load_config, update_settings

SLUG_RE = r'[a-zA-Z0-9-]+'
PATH_RE = r'(/[a-zA-Z0-9\-]+)*'

#pylint: disable=undefined-variable

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_NAME = os.path.basename(BASE_DIR)

update_settings(sys.modules[__name__],
    load_config(APP_NAME, 'credentials', 'site.conf', verbose=True,
        location=os.getenv("SETTINGS_LOCATION", None),
        passphrase=os.getenv("SETTINGS_CRYPT_KEY", None)))

if os.getenv('DEBUG'):
    # Enable override on command line.
    DEBUG = True if int(os.getenv('DEBUG')) > 0 else False

FEATURES_REVERT_TO_DJANGO = True
if os.getenv('FEATURES_REVERT_TO_DJANGO'):
    # Enable override on command line so we can package Jinja2 theme.
    FEATURES_REVERT_TO_DJANGO = (
        True if int(os.getenv('FEATURES_REVERT_TO_DJANGO')) > 0 else False)

# Installed apps
# --------------
if DEBUG:
    ENV_INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.admindocs',
        'debug_toolbar',
        'django_extensions',
        )
else:
    ENV_INSTALLED_APPS = tuple([])

INSTALLED_APPS = ENV_INSTALLED_APPS + (
    'gunicorn',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'deployutils.apps.django',
    'crispy_forms',
    'django_assets',
    'rest_framework',
    'saas',
    'django_comments',
    'answers',
    'survey',
    'pages',
    'envconnect',  # project should be the last entry.
)


EMAIL_SUBJECT_PREFIX = '[%s] ' % APP_NAME
EMAILER_BACKEND = 'extended_templates.backends.TemplateEmailBackend'

DATABASES = {
    'default': {
        'ENGINE':DB_ENGINE,
        'NAME': DB_NAME,
        'USER': DB_USER,                 # Not used with sqlite3.
        'PASSWORD': DB_PASSWORD,         # Not used with sqlite3.
        'HOST': DB_HOST,                 # Not used with sqlite3.
        'PORT': DB_PORT,                 # Not used with sqlite3.
        'TEST_NAME': ':memory:',
    }
}

if DEBUG:
    MIDDLEWARE_CLASSES = (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
        )
else:
    MIDDLEWARE_CLASSES = ()

MIDDLEWARE_CLASSES += (
    'django.middleware.common.CommonMiddleware',
    'deployutils.apps.django.middleware.RequestLoggingMiddleware',
    'deployutils.apps.django.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'envconnect.urls'

SITE_ID = 1  # XXX must match ActivatedUser.pk == 1 in testing.

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'envconnect.wsgi.application'

MANAGERS = ADMINS

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        # Add an unbound RequestFilter.
        'request': {
            '()': 'deployutils.apps.django.logging.RequestFilter',
        },
    },
    'formatters': {
        'simple': {
            'format': 'X X %(levelname)s [%(asctime)s] %(message)s',
            'datefmt': '%d/%b/%Y:%H:%M:%S %z'
        },
        'json': {
            '()': 'deployutils.apps.django.logging.JSONFormatter',
            'replace': False,
            'whitelists': {
                'record': [
                    'nb_queries', 'queries_duration'],
            }
        },
        'request_format': {
            'format':
            '%(remote_addr)s %(username)s %(levelname)s [%(asctime)s]'\
                ' %(message)s "%(http_user_agent)s"',
            'datefmt': '%d/%b/%Y:%H:%M:%S %z'
        },
        'syslog_format': {
            'format':
            'gunicorn.' + APP_NAME + '.app: [%(process)d] '\
                '%(remote_addr)s %(username)s %(levelname)s [%(asctime)s]'\
                ' %(message)s "%(http_user_agent)s"',
            'datefmt': '%d/%b/%Y:%H:%M:%S %z'
        },
    },
    'handlers': {
        'db_logfile': {
            'level': 'DEBUG',
            'formatter': 'simple',
            'filters': ['require_debug_true'],
            'class':'logging.handlers.WatchedFileHandler',
            'filename': '-'.join(os.path.splitext(LOG_FILE)[0].split(
                '-')[:-1] + ['db']) + os.path.splitext(LOG_FILE)[1],
        },
        'json_logfile': {
            'level': 'DEBUG',
            'formatter': 'json',
            'filters': ['request'],
            'class':'logging.handlers.WatchedFileHandler',
            'filename': '-'.join(os.path.splitext(LOG_FILE)[0].split(
                '-')[:-1] + ['events']) + os.path.splitext(LOG_FILE)[1],
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'logfile': {
            'level': 'DEBUG',
            'formatter': 'request_format',
            'filters': ['request'],
            'class':'logging.handlers.WatchedFileHandler',
            'filename': LOG_FILE
        },
        'syslog': {
            'level': 'DEBUG',
            'formatter': 'syslog_format',
            'filters': ['request'],
            'class':'logging.handlers.SysLogHandler',
        }
    },
    'loggers': {
        'deployutils': {
            'handlers': ['db_logfile'],
            'level': 'INFO',
            'propagate': False
        },
#        'django.db.backends': {
#           'handlers': ['db_logfile'],
#           'level': 'DEBUG',
#           'propagate': False
#        },
        'envconnect': {
            'handlers': [],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': [],
            'level': 'ERROR',
        },
        # This is the root logger.
        # The level will only be taken into account if the record is not
        # propagated from a child logger.
        #https://docs.python.org/2/library/logging.html#logging.Logger.propagate
        '': {
            'handlers': ['logfile', 'json_logfile', 'mail_admins'],
            'level': 'INFO'
        },
    },
}

if DEBUG:
    LOGGING['handlers'].update({
        'logfile':{
            'level':'DEBUG',
            'formatter': 'request_format',
            'filters': ['request'],
            'class':'logging.StreamHandler',
        }
    })


# Language settings
# -----------------

# ADD languages
LANGUAGES = (
    ('en-us', _('English')),
    ('fr', _('French')),
    ('es', _('Spanish')),
)

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# add LOCALE_PATHS for i18n in case of manually change
LOCALE_PATHS = (
    BASE_DIR + '/locale',
)

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
#
# We must use UTC here otherwise the date of request in gunicorn access
# and error logs will be off compared to the dates shown in nginx logs.
# (see https://github.com/benoitc/gunicorn/issues/963)
TIME_ZONE = 'UTC'


# Static assets
# -------------
HTDOCS = os.path.join(BASE_DIR, 'htdocs')

ASSETS_DEBUG = DEBUG
ASSETS_AUTO_BUILD = DEBUG
ASSETS_ROOT = os.path.join(HTDOCS, 'static')

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
if not hasattr(sys.modules[__name__], 'MEDIA_ROOT'):
    MEDIA_ROOT = os.path.join(HTDOCS, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/%s/' % APP_NAME

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
APP_STATIC_ROOT = HTDOCS + '/static'
if DEBUG:
    STATIC_ROOT = ''
    # Additional locations of static files
    STATICFILES_DIRS = (APP_STATIC_ROOT,)
    STATIC_URL = '/%s/static/' % APP_NAME
else:
    STATIC_ROOT = APP_STATIC_ROOT
    STATIC_URL = '/static/'

ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django_assets.finders.AssetsFinder'
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Template settings
# -----------------
# There is no bootstrap class for ".alert-error".
MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

CRISPY_TEMPLATE_PACK = 'bootstrap3'
CRISPY_CLASS_CONVERTERS = {'textinput':"form-control"}

# List of callables that know how to import templates from various sources.
_TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

_TEMPLATE_DIRS = [
    os.path.join(BASE_DIR, 'envconnect', 'templates')]
if FEATURES_REVERT_TO_DJANGO:
    _TEMPLATE_DIRS += [
        os.path.join(BASE_DIR, 'envconnect', 'templates', 'django')]
else:
    _TEMPLATE_DIRS += [
        os.path.join(BASE_DIR, 'envconnect', 'templates', 'jinja2')]


_TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
)

# Django 1.8+
TEMPLATES = [
    {
        'BACKEND': 'extended_templates.backends.eml.EmlEngine',
        'DIRS': _TEMPLATE_DIRS,
    },
    {
        'BACKEND': 'extended_templates.backends.pdf.PdfEngine',
        'DIRS': _TEMPLATE_DIRS,
        'OPTIONS': {
            'loaders': _TEMPLATE_LOADERS,
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': _TEMPLATE_DIRS,
        'OPTIONS': {
            'context_processors': [
    'django.contrib.auth.context_processors.auth', # because of admin/
    'django.template.context_processors.request',
    'django.template.context_processors.media',
            ],
            'loaders': _TEMPLATE_LOADERS,
            'libraries': {},
            'builtins': [
                'envconnect.templatetags.navactive',
                'django_assets.templatetags.assets',
                'deployutils.apps.django.templatetags.deployutils_prefixtags',
                'deployutils.apps.django.templatetags.deployutils_extratags']
        }
    }]


# debug_toolbar settings
# ----------------------
DEBUG_TOOLBAR_PATCH_SETTINGS = False
DEBUG_TOOLBAR_CONFIG = {
    'JQUERY_URL': '%svendor/jquery.js' % STATIC_URL,
    'SHOW_COLLAPSED': True,
}
INTERNAL_IPS = ('127.0.0.1', '::1')  # Yes, this one is also for debug_toolbar.

# User settings
# -------------
LOGIN_URL = 'login'
if DEBUG:
    LOGIN_REDIRECT_URL = '/%s/app/' % APP_NAME
else:
    LOGIN_REDIRECT_URL = '/app/'
ACCOUNT_ACTIVATION_DAYS = 2


# The Django Middleware expects to find the authentication backend
# before returning an authenticated user model.
AUTHENTICATION_BACKENDS = (
    'deployutils.apps.django.backends.auth.ProxyUserBackend',
    # XXX We cannot remove dependency on a db `User` until django_comments
    # is made to use the deployutils version.
    'django.contrib.auth.backends.ModelBackend'
)

# Session settings
# ----------------
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_ENGINE = 'deployutils.apps.django.backends.encrypted_cookies'

DEPLOYUTILS = {
    # Hardcoded mockups here.
    'MOCKUP_SESSIONS': {
        'donny': {
            'username': 'donny',
            'roles': {
                'manager': [
                    {'slug': 'envconnect', 'full_name': 'Enviro-Connect',
                    'printable_name': 'Enviro-Connect'}]},
            'site': {'email': 'donny@djaodjin.com'}},
        'steve': {
            'username': 'steve',
            'roles': {
                'manager': [{'slug': 'steve-shop',
                    'printable_name': 'Steve Shop'}]},
            'site': {'email': 'donny+steve@djaodjin.com'}},
        'andy': {
            'username': 'andy',
            'roles': {
                'manager': [{'slug': 'andy-shop',
                    'printable_name': 'Andy Shop'}]},
            'site': {'email': 'donny+andy@djaodjin.com'}},
        'erin': {
            'username': 'erin',
            'roles': {
                'viewer': [{'slug': 'steve-shop',
                    'printable_name': 'Steve Shop'}]},
            'site': {'email': 'donny+erin@djaodjin.com'}},
    },
    'ALLOWED_NO_SESSION': [
        STATIC_URL,
        reverse_lazy('login'), reverse_lazy('registration_register'),
        reverse_lazy('homepage'), reverse_lazy('homepage_index')]
}

ACCOUNT_MODEL = 'saas.Organization'

# SaaS settings
# -------------
# XXX waiting for PostgreSQL 9.5
#if DB_ENGINE.endswith('postgresql_psycopg2'):
#    SAAS = {
#        'EXTRA_FIELD': 'django.contrib.postgres.fields.JSONField'
#    }

# Survey settings
# ---------------
SURVEY = {
    'ACCOUNT_MODEL': 'saas.Organization',
    'ACCOUNT_LOOKUP_FIELD': 'slug',
    'ACCOUNT_SERIALIZER': 'saas.api.serializers.OrganizationSerializer',
    'QUESTION_SERIALIZER': 'envconnect.serializers.ConsumptionSerializer'
}

# Awnsers app
# -----------
ANSWERS = {
    'QUESTION_MODEL': 'pages.PageElement'
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}

PAGES = {
    'ACCOUNT_MODEL': 'saas.Organization',
    'DEFAULT_ACCOUNT_CALLABLE': 'saas.models.get_broker',
    'PAGELEMENT_SERIALIZER' : "envconnect.serializers.PageElementSerializer"
}

VERSION_REGISTERED_APP = (
    'envconnect',
)

# API settings
# ------------
REST_FRAMEWORK = {
    'PAGE_SIZE': 25,
}

# envconnect
TAG_SYSTEM = 'system'
TAG_SCORECARD = 'scorecard'
