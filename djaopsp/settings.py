# Copyright (c) 2023, DjaoDjin inc.
"""
Django settings for djaopsp project.
"""
import os, sys

from deployutils.configs import load_config, update_settings

from .compat import reverse_lazy


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Default values that can be overriden by `update_settings` later on.
APP_NAME = os.path.basename(BASE_DIR)
RUN_DIR = os.path.join(BASE_DIR, 'var', 'run', 'cache')

DEBUG = True
FEATURES_USE_PORTFOLIOS = False
TESTING_USERNAMES = []

ALLOWED_HOSTS = ('*',)

DB_ENGINE = 'sqlite3'
DB_NAME = os.path.join(BASE_DIR, 'db.sqlite')
DB_HOST = ''
DB_PORT = 5432
DB_USER = None
DB_PASSWORD = None

update_settings(sys.modules[__name__],
    load_config(APP_NAME, 'credentials', 'site.conf', verbose=True))

# Enable override on command line.
for env_var in ['DEBUG', 'API_DEBUG', 'ASSETS_DEBUG', 'FEATURES_DEBUG']:
    if os.getenv(env_var):
        setattr(sys.modules[__name__], env_var, (int(os.getenv(env_var)) > 0))
    if not hasattr(sys.modules[__name__], env_var):
        setattr(sys.modules[__name__], env_var, DEBUG)
if sys.version_info[0] < 3:
    # Requires Python3+ to create API docs
    API_DEBUG = False

# Remove extra information used for documentation like examples, etc.
OPENAPI_SPEC_COMPLIANT = bool(int(os.getenv('OPENAPI_SPEC_COMPLIANT', "0")) > 0)

if not hasattr(sys.modules[__name__], "SECRET_KEY"):
    from random import choice
    SECRET_KEY = "".join([choice(
        "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*-_=+") for i in range(50)])

JWT_ALGORITHM = 'HS256'
if not hasattr(sys.modules[__name__], "JWT_SECRET_KEY"):
    JWT_SECRET_KEY = getattr(sys.modules[__name__], "DJAODJIN_SECRET_KEY",
        SECRET_KEY)

# Installed apps
# --------------
if DEBUG:
    DEBUG_APPS = (
        'django_extensions',
# XXX We cannot import name 'get_safe_settings' from 'django.views.debug'
#        'debug_toolbar',
# XXX django.contrib.admin does not support Jinja2 templates
#        'django.contrib.admin',
#        'django.contrib.admindocs',
    )
else:
    DEBUG_APPS = tuple([])

INSTALLED_APPS = DEBUG_APPS + (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'deployutils.apps.django',
    'rest_framework',
    'survey',
    'pages',
    'extended_templates',
    'djaopsp.sustainability',
    'djaopsp' # project should be the last entry.
)

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'deployutils.apps.django.middleware.RequestLoggingMiddleware',
    'deployutils.apps.django.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'djaopsp.urls'
WSGI_APPLICATION = 'djaopsp.wsgi.application'

# Logging
# -------
LOG_HANDLER = {
    'level': 'DEBUG',
    'formatter': ('request_format' if (DEBUG or
        getattr(sys.modules[__name__], 'USE_FIXTURES', False)) else 'json'),
    'filters': ['request'],
    'class':'logging.StreamHandler',
}
LOG_FILE = getattr(sys.modules[__name__], 'LOG_FILE', None)
if not DEBUG and LOG_FILE:
    LOG_HANDLER.update({
        'class':'logging.handlers.WatchedFileHandler',
        'filename': LOG_FILE
    })

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
            'format':
            'gunicorn.' + APP_NAME + '.app: [%(process)d] '\
                '%(log_level)s %(remote_addr)s %(http_host)s %(username)s'\
                ' [%(asctime)s] %(message)s',
            'datefmt': '%d/%b/%Y:%H:%M:%S %z',
            'replace': False,
            'whitelists': {
                'record': [
                    'nb_queries', 'queries_duration',
                    'charge', 'amount', 'unit', 'modified',
                    'customer', 'organization', 'provider'],
            }
        },
        'request_format': {
            'format':
            '%(levelname)s %(remote_addr)s %(username)s [%(asctime)s]'\
                ' %(message)s "%(http_user_agent)s"',
            'datefmt': '%d/%b/%Y:%H:%M:%S %z'
        }
    },
    'handlers': {
        'db_log': {
            'level': 'DEBUG',
            'formatter': 'simple',
            'filters': ['require_debug_true'],
            'class':'logging.StreamHandler',
        },
        'log': LOG_HANDLER,
        # Add `mail_admins` in top-level handler when there are no other
        # mechanism to be notified of server errors.
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
    },
    'loggers': {
        'deployutils.perf': {
            'handlers': ['log'],
            'level': 'INFO',
            'propagate': False
        },
        'deployutils': {
            'handlers': ['db_log'],
            'level': 'INFO',
            'propagate': False
        },
#        'django.db.backends': {
#           'handlers': ['db_log'],
#           'level': 'DEBUG',
#           'propagate': False
#        },
        'djaopsp': {
            'handlers': [],
            'level': 'INFO',
        },
        'extended_templates': {
            'handlers': [],
            'level': 'INFO',
        },
        'pages': {
            'handlers': [],
            'level': 'INFO',
        },
        'survey': {
            'handlers': [],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': [],
            'level': 'ERROR',
        },
        # If we don't disable 'django' handlers here, we will get an extra
        # copy on stderr.
        'django': {
            'handlers': [],
        },
        # This is the root logger.
        # The level will only be taken into account if the record is not
        # propagated from a child logger.
        #https://docs.python.org/2/library/logging.html#logging.Logger.propagate
        '': {
            'handlers': ['log'],
            'level': 'INFO'
        },
    },
}

# static assets (CSS, JavaScript, Images)
# ---------------------------------------
HTDOCS = os.path.join(BASE_DIR, 'htdocs')
STATIC_ROOT = os.path.join(HTDOCS, 'static')

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

if DEBUG:
    # Additional locations of static files
    STATICFILES_DIRS = (STATIC_ROOT, HTDOCS,)
    STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

ASSETS_MAP = {
    'cache/base.css': (
        'base/base.scss', (
            'base/*.scss',
            'vendor/bootstrap/*.scss',
            'vendor/bootstrap/mixins/*.scss',
            'vendor/bootstrap/utilities/*.scss',
            'vendor/djaodjin/*.scss',
            'vendor/toastr/*.scss'
        )
    ),
    'cache/pages.css': (
        'pages/pages.scss', (
            'pages/*.scss',
            'vendor/jquery-ui.scss',
            'vendor/bootstrap-colorpicker.scss',
            'vendor/djaodjin-pages/*.scss',
        )
    ),
    'cache/dashboard.css': (
        'dashboard/dashboard.scss', (
            'dashboard/*.scss',
            'vendor/nv.d3.scss',
            'vendor/trip.scss',
        )
    ),
    'cache/email.css': (
        'email/email.scss', (
            'email/*.scss',
        )
    ),
}

ASSETS_CDN = {}
ASSETS_ROOT = HTDOCS

# Templates engines
# -----------------
# Django 1.8+
FILE_CHARSET = 'utf-8'

TEMPLATES_DIRS = (
    os.path.join(BASE_DIR, 'djaopsp', 'sustainability', 'templates'),
    os.path.join(BASE_DIR, 'djaopsp', 'templates', 'jinja2'),
    os.path.join(BASE_DIR, 'djaopsp', 'templates'),)

# List of callables that know how to import templates from various sources.
TEMPLATES_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATES = [
    {
        'NAME': 'eml',
        'BACKEND': 'extended_templates.backends.eml.EmlEngine',
        'DIRS': TEMPLATES_DIRS,
        'OPTIONS': {
            'engine': 'html',
        }
    },
    {
        'NAME': 'pdf',
        'BACKEND': 'extended_templates.backends.pdf.PdfEngine',
        'DIRS': TEMPLATES_DIRS,
        'OPTIONS': {
            'loaders': TEMPLATES_LOADERS,
        }
    },
    {
        'NAME': 'html',
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': TEMPLATES_DIRS,
        'OPTIONS': {
            'environment': 'djaopsp.jinja2.environment'
        }
    }
]

EXTENDED_TEMPLATES = {
    'ASSETS_MAP': ASSETS_MAP,
}

EMAIL_SUBJECT_PREFIX = '[%s] ' % APP_NAME
EMAILER_BACKEND = 'extended_templates.backends.TemplateEmailBackend'
MANAGERS = getattr(sys.modules[__name__], 'ADMINS', [])


# Databases
# ---------
if not hasattr(sys.modules[__name__], 'DB_BACKEND'):
    DB_BACKEND = (DB_ENGINE if DB_ENGINE.startswith('django.db.backends.') else
        'django.db.backends.%s' % DB_ENGINE)
DATABASES = {
    'default': {
        'ENGINE':DB_BACKEND,
        'NAME': DB_NAME,
        'USER': DB_USER,                 # Not used with sqlite3.
        'PASSWORD': DB_PASSWORD,         # Not used with sqlite3.
        'HOST': DB_HOST,                 # Not used with sqlite3.
        'PORT': DB_PORT,                 # Not used with sqlite3.
        'TEST': {
            'NAME': None,
        }
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# API settings
# ------------
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        # We are using Jinja2 templates so there are no templates
        # for `rest_framework.renderers.BrowsableAPIRenderer`.
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'deployutils.apps.django.authentication.JWTAuthentication',
        # `rest_framework.authentication.SessionAuthentication` is the last
        # one in the list because it will raise a PermissionDenied if the CSRF
        # is absent.
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_SCHEMA_CLASS': 'djaopsp.views.api_docs.AutoSchema',
    'EXCEPTION_HANDLER': 'djaopsp.views.errors.drf_exception_handler',
    'SEARCH_PARAM': 'q',
    'PAGE_SIZE': 25,
    'ORDERING_PARAM': 'o'
}


# Session settings
# ----------------
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_ENGINE = 'deployutils.apps.django.backends.jwt_session_store'

JWT_ALGORITHM = 'HS256'

DEPLOYUTILS = {
    # Hardcoded mockups here.
    'MOCKUP_SESSIONS': {
        'donny': {
            'username': 'donny',   # Profile manager for TSP
            'roles': {
                'manager': [{
                    'slug': APP_NAME,
                    'printable_name': APP_NAME,
                }]},
            'site': {
                'slug': APP_NAME,
                'printable_name': APP_NAME,
                'email': '%s@localhost.localdomain' % APP_NAME
            }
        },
        'kathryn': {
            'username': 'kathryn', # Profile manager for alliance
            'roles': {
                'manager': [{
                    'slug': 'alliance',
                    'printable_name': 'Alliance',
                    "subscriptions": [{
                        "plan": "managed",
                        "ends_at": "2023-12-31T23:59:59Z"
                    }],
                }]},
            'site': {
                'slug': APP_NAME,
                'printable_name': APP_NAME,
                'email': '%s@localhost.localdomain' % APP_NAME
            }
        },
        'alice': {
            'username': 'alice',   # Profile manager for alliance tier1 member
            'roles': {
                'manager': [{
                    'slug': 'energy-utility',
                    'printable_name': 'Energy utility',
                    "subscriptions": [{
                        "plan": "tier1-members",
                        "ends_at": "2023-12-31T23:59:59Z"
                    }],
                }]},
            'site': {
                'slug': APP_NAME,
                'printable_name': APP_NAME,
                'email': '%s@localhost.localdomain' % APP_NAME
            }
        },
        'janice': {
            'username': 'janice',  # Profile manager for alliance tier2 member
            'roles': {
                'manager': [{
                    'slug': 'janice-shop',
                    'printable_name': 'Janice Shop',
                    "subscriptions": [{
                        "plan": "tier2-members",
                        "ends_at": "2023-12-31T23:59:59Z"
                    }],
                }]},
            'site': {
                'slug': APP_NAME,
                'printable_name': APP_NAME,
                'email': '%s@localhost.localdomain' % APP_NAME
            }
        },
        'steve': {
            'username': 'steve',   # Profile manager for registered organization
            'last_visited': '2017-01-01T00:00:00.000Z',
            'roles': {
                'manager': [{
                    'slug': 'supplier-1',
                    'printable_name': 'Steve Shop'
                }]},
            'site': {
                'slug': APP_NAME,
                'printable_name': APP_NAME,
                'email': '%s@localhost.localdomain' % APP_NAME
            }
        },
        'andy': {
            'username': 'andy',
            'roles': {
                'manager': [{'slug': 'andy-shop',
                    'printable_name': 'Andy Shop'}]},
            'site': {
                'slug': APP_NAME,
                'printable_name': APP_NAME,
                'email': '%s@localhost.localdomain' % APP_NAME
            }
        },
        'erin': {
            'username': 'erin',
            'roles': {
                'viewer': [{'slug': 'supplier-1',
                    'printable_name': 'Steve Shop'}]},
            'site': {
                'slug': APP_NAME,
                'printable_name': APP_NAME,
                'email': '%s@localhost.localdomain' % APP_NAME
            }
        },
    },
    'ALLOWED_NO_SESSION': [
        STATIC_URL,
        '/docs/api/',
        reverse_lazy('login'),
        reverse_lazy('homepage')
    ]
}

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

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [{
    'NAME':
    'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
}, {
    'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
}, {
    'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
}, {
    'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
}]


# Internationalization
# --------------------
# https://docs.djangoproject.com/en/3.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# djaopsp app
# -----------
ACCOUNT_MODEL = 'djaopsp.Account'
REPORTING_ACCOUNTS_CALLABLE = None
REQUESTED_ACCOUNTS_CALLABLE = None
SEND_NOTIFICATION_CALLABLE = None
SCORE_CALCULATORS = {
    '/sustainability': 'djaopsp.scores.ScoreCalculator',
}

AUDITOR_ROLE = 'auditor'
UNLOCK_PORTFOLIOS = set(['managed', 'tier1-members'])
UNLOCK_EDITORS = set(['managed'])
UNLOCK_BROKERS = set([APP_NAME])


# pages app
# ---------
PAGES = {
    'ACCOUNT_LOOKUP_FIELD': 'slug',
    'ACCOUNT_MODEL': ACCOUNT_MODEL,
}


# survey app
# ----------
SURVEY = {
    'ACCOUNT_LOOKUP_FIELD': 'slug',
    'ACCOUNT_MODEL': ACCOUNT_MODEL,
    'ACCOUNT_URL_KWARG': 'profile',
    'CONTENT_MODEL': 'pages.PageElement',
}
