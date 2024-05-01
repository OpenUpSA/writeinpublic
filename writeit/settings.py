# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Django settings for writeit project.
import sys
import os
from django.conf.global_settings import LANGUAGES
from django.utils.translation import to_locale
import environ

env = environ.Env()

DEBUG = env.bool("DJANGO_DEBUG", False)
TASTYPIE_FULL_DEBUG = True
TEMPLATE_DEBUG = DEBUG
TESTING = 'test' in sys.argv

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

ADMINS = [x.split(':') for x in env.list('DJANGO_ADMINS', default=[])]

MANAGERS = ADMINS

DATABASES = {
    'default': env.db(),
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# or if not expecting simply ['localhost', '127.0.0.1', '[::1]'].
# See https://docs.djangoproject.com/en/1.8/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"] # We rely on the upstream proxy to restrict hostnames for us

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = env.str("TIME_ZONE", 'America/Chicago')

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

LOCALE_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locale')
]

# The code below sets LANGUAGES to only those we have translations
# If someone's browser sends 'Accept-Language: es', that means that it
# will be found in this list, but since there are no translations for 'es'
# it'll fall back to LANGUAGE_CODE.  However, if there is no 'es' in
# LANGUAGES, then Django will attempt to do a best match.
LANGUAGES = [l for l in LANGUAGES if os.path.exists(os.path.join(LOCALE_PATHS[0], to_locale(l[0])))]

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# If the site is being served over https change this to 'https' so that links
# to subdomains use the correct scheme.
DEFAULT_URL_SCHEME = 'http'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'pipeline.finders.PipelineFinder',
)

STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage' if TESTING else 'pipeline.storage.PipelineCachedStorage'

PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_YUI_BINARY = '/usr/bin/env yui-compressor'
PIPELINE_COMPILERS = (
    'pipeline.compilers.sass.SASSCompiler',
    )
PIPELINE_SASS_BINARY = '/usr/bin/env sassc'  # Libsass, via libsass-python
PIPELINE_CSS = {
    'writeit-instance': {
        'source_filenames': (
            'sass/instance.scss',
        ),
        'output_filename': 'css/instance.css',
    },
    'writeit-admin': {
        'source_filenames': (
            'sass/admin.scss',
        ),
        'output_filename': 'css/admin.css',
    },
    'writeit-manager': {
        'source_filenames': (
            'sass/manager.scss',
        ),
        'output_filename': 'css/manager.css',
    },
    'writeit-writeinpublic': {
        'source_filenames': (
            'sass/writeinpublic.scss',
        ),
        'output_filename': 'css/writeinpublic.css',
    }
}

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'writeit.template_loaders.SubdomainFilesystemLoader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
    )

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
    'writeit.context_processors.web_api_settings',
    'writeit.context_processors.google_analytics_settings',
    )

MIDDLEWARE_CLASSES = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'subdomains.middleware.SubdomainURLRoutingMiddleware',
    'writeit.middleware.SubdomainInThreadLocalStorageMiddleware',
    'nuntium.middleware.InstanceLocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'pagination.middleware.PaginationMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'nuntium.subdomain_urls'

# A dictionary of urlconf module paths, keyed by their subdomain.
SUBDOMAIN_URLCONFS = {
    None: 'writeit.urls',  # no subdomain, e.g. ``example.com``
    'www': 'writeit.urls',
}

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'writeit.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social.apps.django_app.default',
    'annoying',
    'celery_haystack',
    'djcelery',

    'debug_toolbar',

    'instance',
    'nuntium',
    'djangoplugins',
    'pagination',

    # Although django-popit is unused now, we need to keep it
    # installed because the earlier migrations depend on its presence.
    'popit',

    'popolo',
    'popolo_sources',
    'contactos',
    'mailit',
    'tastypie',
    'markdown_deux',
    'django_extensions',
    # Searching.
    'haystack',
    'pipeline',
    # Uncomment the next line to enable the admin:
    'django_admin_bootstrapped',
    'django.contrib.admin',
    'django_object_actions',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',

    # Multi-page form wizard
    'formtools',
    'subdomains',
    'mailreporter'
)

if TESTING:
    INSTALLED_APPS += (
        'django_nose',
        )

# SEARCH INDEX WITH ELASTICSEARCH
HAYSTACK_SIGNAL_PROCESSOR = 'celery_haystack.signals.CelerySignalProcessor'

ELASTICSEARCH_URL = env.str("ELASTICSEARCH_URL")
ELASTICSEARCH_INDEX = env.str("ELASTICSEARCH_INDEX")

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': ELASTICSEARCH_URL,
        'INDEX_NAME': ELASTICSEARCH_INDEX,
    },
}

#Testing with django
TEST_RUNNER = 'global_test_case.WriteItTestRunner'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'main': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'root': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

SENTRY_DSN = env.str("SENTRY_DSN", None)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],

        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True
    )

# POPIT TESTING RELATED
TEST_POPIT_API_HOST_IP = '127.0.0.1'
TEST_POPIT_API_PORT = '3000'
TEST_POPIT_API_SUBDOMAIN = 'whatever'

TEST_POPIT_API_URL = "http://%s.%s.xip.io:%s/api/v0.1/export.json" % (
    TEST_POPIT_API_SUBDOMAIN,
    TEST_POPIT_API_HOST_IP,
    TEST_POPIT_API_PORT,
    )


# Email settings
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", 'south-africa-assembly@writeinpublic.pa.org.za')

DEFAULT_NO_REPLY_LOCAL_PART = env.str('DEFAULT_NO_REPLY_LOCAL_PART', 'no-reply')

# DEFAULT_FROM_DOMAIN
DEFAULT_FROM_DOMAIN = env.str("DEFAULT_FROM_DOMAIN", 'writeinpublic.pa.org.za')

# In some cases it is needed that all emails come from one single
# email address, such is the case when you have just verified a single sender
SEND_ALL_EMAILS_FROM_DEFAULT_FROM_EMAIL = env.bool("SEND_ALL_EMAILS_FROM_DEFAULT_FROM_EMAIL", False)

if 'EMAIL_HOST' in os.environ:
    EMAIL_HOST = os.environ['EMAIL_HOST']
if 'EMAIL_PORT' in os.environ:
    EMAIL_PORT = os.environ['EMAIL_PORT']
if 'EMAIL_HOST_USER' in os.environ:
    EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
if 'EMAIL_HOST_PASSWORD' in os.environ:
    EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
if 'EMAIL_USE_TLS' in os.environ and os.environ['EMAIL_USE_TLS'] == 'True':
    EMAIL_USE_TLS = True
if 'EMAIL_USE_SSL' in os.environ and os.environ['EMAIL_USE_SSL'] == 'True':
    EMAIL_USE_SSL = True

EMAIL_BACKEND = env.str("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")


# CELERY CONFIGURATION

CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", 'amqp://guest:guest@rabbitmq//')
BROKER_URL = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'


from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    # Sends emails every 2 minutes
    'send-mails-every-2-minutes': {
        'task': 'nuntium.tasks.send_mails_task',
        'schedule': crontab(minute='*/2'),
    },
    # Resyncs popit every week
    'resync-popit-apis-every-week': {
        'task': 'nuntium.tasks.update_all_instances',
        'kwargs': {
            'periodicity': '1W'
        },
        'schedule': crontab(hour=5, minute=30, day_of_week=1),
    },
    # Resyncs popit every day
    'resync-popit-apis-every-day': {
        'task': 'nuntium.tasks.update_all_instances',
        'kwargs': {
            'periodicity': '1D'
        },
        'schedule': crontab(hour=5, minute=30),
    },
    # Resyncs popit twice every day
    'resync-popit-apis-twice-every-day': {
        'task': 'nuntium.tasks.update_all_instances',
        'kwargs': {
            'periodicity': '2D'
        },
        'schedule': crontab(hour='*/12'),
    },
}
# the biggest number of recipients a user can
# configure without asking the admin of the site
OVERALL_MAX_RECIPIENTS = 10
# Logs every incoming email??
INCOMING_EMAIL_LOGGING = 'None'

# Should WriteInPublic handle bounces?
FLAG_BOUNCED_CONTACTS = False


# setting to avoid db changes during test

EXTRA_APPS = ()


GOOGLE_ANALYTICS_PROPERTY_ID = env.str("GOOGLE_ANALYTICS_PROPERTY_ID", None)

# SOCIAL AUTH DETAILS
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env.str("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", None)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env.str("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", None)

AUTHENTICATION_BACKENDS = (
    'social.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SESSION_COOKIE_DOMAIN = env.str("SESSION_COOKIE_DOMAIN", "localhost")

CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_CREATE_MISSING_QUEUES = True
CELERY_HAYSTACK_TRANSACTION_SAFE = True
CELERY_HAYSTACK_DEFAULT_ALIAS = None
CELERY_HAYSTACK_RETRY_DELAY = 5 * 60
CELERY_HAYSTACK_MAX_RETRIES = 1
CELERY_HAYSTACK_DEFAULT_TASK = 'celery_haystack.tasks.CeleryHaystackSignalHandler'

# These can be set independently, but most often one will be set to True and
# the other to False. Setting both to the same boolean value will have
# undefined behaviour.
WEB_BASED = True
API_BASED = False

if TESTING:
    LOCAL_ELASTICSEARCH = True
    CELERY_ALWAYS_EAGER = True
    ELASTICSEARCH_INDEX += "-test"

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY' in os.environ:
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ['SOCIAL_AUTH_GOOGLE_OAUTH2_KEY']

if 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET' in os.environ:
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ['SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET']


try:
    from subdomains.utils import reverse
    from django.utils.translation import activate
    activate(LANGUAGE_CODE)
    LOGIN_URL = reverse('login', subdomain=None)
except:
    LOGIN_URL = '/accounts/login/'

DEBUG_TOOLBAR_PATCH_SETTINGS = False

def show_toolbar(request):
    return os.environ.get("DJANGO_DEBUG_TOOLBAR", "false").lower() == "true"

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
}

INTERNAL_IPS = ['127.0.0.1', '::1']
