# Django settings for Venturi project.

import os
import djcelery
import getpass

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)

# Celery Configuration. Django Celery Integration:
# http://pypi.python.org/pypi/django-celery
djcelery.setup_loader()

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Michele Mostarda', 'mostarda@fbk.eu'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'controller',
        'USER': 'controller',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

TABULAR_DATABASE = {
    'NAME': 'controller-data',
    'USER': 'controller',
    'PASSWORD': 'password',
    'HOST': '127.0.0.1',
    'PORT': '',
}

from urlparse import urljoin
URI_BASE_PREFIX = 'http://data.venturi.eu/'
DM_URI_BASE_PREFIX = 'http://dandelion.eu/'
DM_RESOURCE_BASE_PREFIX = DM_URI_BASE_PREFIX + 'resource/'
DM_CATEGORY_BASE_PREFIX = DM_URI_BASE_PREFIX + 'ontologies/'
DM_ONTOLOGY_URL = 'http://ontologies.venturi.eu/v1.rdf'
TRIPLE_DATABASE = {
    'TYPE': 'virtuoso',
    'HOST': '127.0.0.1',
    'PORT': '8890',
    'ENDPOINT': 'sparql',
    'ADMIN_HOST': '127.0.0.1',
    'ADMIN_PORT': '1111',
    'ADMIN_USER': 'dba',
    'ADMIN_PASSWORD': 'dba',
    'LOAD_DIR': '/srv/virtuoso/data',
    'SCP_USER': None,
    'SCP_PORT': 22,
    'PREFIXES': {
        u"sdowl": ur"http://ontologies.venturi.eu/base#",
        u"sdv1": ur"http://ontologies.venturi.eu/v1#",
        u"sdres": urljoin(URI_BASE_PREFIX, "/resource/"),
        u"sdprop": urljoin(URI_BASE_PREFIX, "/property/"),
        u"graph": urljoin(URI_BASE_PREFIX, "/graph/"),
        u"data_graph_raw": urljoin(URI_BASE_PREFIX, "/graph/raw/"),
        u"data_graph_mapped": urljoin(URI_BASE_PREFIX, "/graph/mapped/"),
        u"silk_graph": urljoin(URI_BASE_PREFIX, "/graph/mapped/silk"),
        u"meta_graph": urljoin(URI_BASE_PREFIX, "/graph/meta"),
        u"geom": urljoin(URI_BASE_PREFIX, "/geometry/"),
        u"owl": ur'http://www.w3.org/2002/07/owl#',
        u"meta": ur"http://ontologies.venturi.eu/metaprop#",
    }
}

TRIPLE_DATABASE_MASTER = {
    'TYPE': 'titan',
    'HOST': '127.0.0.1',
    'PORT': '8182',
    'PREFIXES': TRIPLE_DATABASE['PREFIXES'],
    'ENDPOINT': 'graphs/graph',
    'KWARGS': {
        'graph': 'graph',
        'ontology': DM_ONTOLOGY_URL,
        'rexpro_port': '8184',
        'prefixes': {
            'sdr': TRIPLE_DATABASE['PREFIXES']['sdres'],
            'sd': TRIPLE_DATABASE['PREFIXES']['sdv1'],
            'g': TRIPLE_DATABASE['PREFIXES']['data_graph_mapped'],
            'tpoi': 'http://ontologies.venturi.eu/taxonomies/POI/v1#',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'owl': 'http://www.w3.org/2002/07/owl#',
            'purl': 'http://purl.org/dc/elements/1.1/',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
        }
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Rome'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'it-it'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and img.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

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
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'put_a_good_key_here*******************************'

## Import local settings

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    # 'django.template.loaders.filesystem.Loader',
    # 'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
    'webui.jinja2_loader.Loader',
)

JINJA2_TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

JINJA2_DISABLED_TEMPLATES = (
    'admin',
    'bootstrap',
    'jinja2-compat',
    'django_ace',
    'console',
)

JINJA2_EXTENSIONS = (
    'jinja2.ext.loopcontrols', 'jinja2.ext.with_',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'webui.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'coffin',

    'webui.controller',
    'webui.scheduler',
    'webui.slice',
    'webui.cnmain',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',

    'djcelery',

    'crispy_forms',

    'django_ace',

    'taggit',

    # DB migrations
    'south',

    # common django extensions
    'django_extensions',
)

LOGIN_URL = '/login/'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['console'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

# Acquisition TMP dir
username = getpass.getuser()
TMP_DIR = '/tmp/sd-controller_' + username


# ScraperWiki
SCRAPERWIKI_APP = 'http://vpn.venturi.eu'
METADATA_TABLE = 'meta'

# Venturi Schema.
SD_SCHEMA = 'http://venturi.eu/schema/0.1/'

# Google Refine
REFINE_EXTERNAL_HOST = 'refine.venturi.eu'
# REFINE_EXTERNAL_HOST = 'refine.venturi.eu'
REFINE_EXTERNAL_PORT = '80'

# silk
SILK_EXTERNAL_HOST = 'silk.venturi.eu'
SILK_EXTERNAL_PORT = '80'
SILK_SINGLE_MACHINE_THREADS = 32
SILK_SINGLE_MACHINE_HEAP = '2g'

# OSM Importer
OSM_DATABASES = {
    'db1': {
        'NAME': 'venturi-controller',
        'USER': 'venturi',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432'
    },
    'db2': {
        'NAME': 'venturi-test',
        'USER': 'venturi',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

BROKER_URL = 'amqp://guest:guest@localhost:5672/controller'

SLICE_DEFAULT_CATEGORY = \
    'http://ontologies.venturi.eu/taxonomies/POI/v1#POI'

try:
    from settings_local import *
except ImportError:
    pass

# BEWARE those are defined after local import because are derived from other
# vars maybe redefined in local settings

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    'django.core.context_processors.csrf',
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
)

VIRTUAL_ENV_PATH = '~/.virtualenvs/controller'

#### DO NOT CHANGE UNDER THIS LINE! ####

from webui.conf import import_


DJANGO_CONF = os.environ.get('DJANGO_CONF', 'dev')
import_('webui.conf.settings.{0}'.format(DJANGO_CONF), globals())

###### load local settings

import_('settings_local', globals(), quiet=True)
