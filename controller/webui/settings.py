# Django settings for SpazioDati project.

import os
import djcelery
import getpass

APP_ROOT = os.path.dirname(os.path.realpath(__file__))

# Celery Configuration. Django Celery Integration: http://pypi.python.org/pypi/django-celery
djcelery.setup_loader()
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Admin', 'admin@example.org'),
)

MANAGERS = ADMINS

DATABASES = {
    'default' : {
        'ENGINE'   : 'django.db.backends.postgresql_psycopg2',
        'NAME'     : 'wedpipe-controller',
        'USER'     : 'wedpipe',
        'PASSWORD' : 'webpipe',
        'HOST'     : 'localhost',
        'PORT'     : '5432'
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
LANGUAGE_CODE = 'en-us'

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

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
PROJECT_ROOT = os.path.dirname(APP_ROOT)
STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
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
SECRET_KEY = '2&lp&#z*kzgxu*m)m0@q1&!(5pe(+aow))bs(9--3d+j%9er&h'

## Import local settings

try:
    from settings_local import *
except ImportError:
    pass


# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
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
     os.path.dirname(os.path.realpath(__file__)) + '/templates'
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    # 'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    # Controller UI
    'webui.controller',
    # Celery module.
    'djcelery',
    # django jenkins integration module.
    'django_jenkins',
)

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.with_coverage',
    'django_jenkins.tasks.django_tests',
)

PROJECT_APPS = (
    'controller',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Acquisition TMP dir
username = getpass.getuser()
TMP_DIR = '/tmp/sd-controller_' + username


# ScraperWiki
#SCRAPERWIKI_APP         = 'http://vpn.example.org'
SCRAPERWIKI_APP         = 'https://scraperwiki.com'
SCRAPERWIKI_NEW_SCRAPER = SCRAPERWIKI_APP + '/scrapers/new/python'
SCRAPERWIKI_API         = SCRAPERWIKI_APP + '/api/1.0/'
SCRAPERWIKI_API_CSV     = SCRAPERWIKI_API + "/datastore/sqlite?format=csv"
METADATA_TABLE  = 'meta'

# SpazioDati Schema.
SD_SCHEMA = 'http://example.org/schema/0.1/'

# RDF Browser.
RAW_RDF_BROWSER_SERVER = 'http://raw.example.org/page/'
MAP_RDF_BROWSER_SERVER = 'http://mapped.example.org/graph/'

# Google Refine
REFINE_EXTERNAL_HOST = 'refine.example.org'
REFINE_EXTERNAL_PORT = ''
REFINE_RDF_MAPPING_BASE_URI     = 'http://mapped.example.org'
REFINE_RDF_MAPPING_GRAPH_PREFIX = REFINE_RDF_MAPPING_BASE_URI + '/graph/'
