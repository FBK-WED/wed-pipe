"""
config for test
"""
# pylint: disable=C0111,C0103,W0612,R0914
import os
from webui.conf import ClassSettings


class Settings(ClassSettings):
    def run(self, settings):
        super(Settings, self).run(settings)

        DEBUG = False

        # https://docs.djangoproject.com/en/dev/topics/testing/
        PASSWORD_HASHERS = (
            'django.contrib.auth.hashers.MD5PasswordHasher',
        )

        # no cache
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
            }
        }

        # to allow data_acquisition scripts to connect to the right db
        if os.environ.get('DJANGO_CALLER') == 'script' \
                and settings.DJANGO_CONF in ('test', 'jenkins'):
            settings.DATABASES['default']['NAME'] = \
                'test_' + settings.DATABASES['default']['NAME']

        settings.TABULAR_DATABASE['NAME'] = 'test_controller-data'

        # synchronous celery
        CELERY_ALWAYS_EAGER = True

        # a string to look for in tests to check for errors
        TEMPLATE_STRING_IF_INVALID_TEST = "IMPOSSIBLE_TO_REPLICATE_INVALID"
        TEMPLATE_STRING_IF_INVALID = TEMPLATE_STRING_IF_INVALID_TEST + ": %s"

        # store sessions on files
        SESSION_ENGINE = 'django.contrib.sessions.backends.file'

        TEST_RUNNER = 'webui.tests.TestRunner'
        INSTALLED_APPS = settings.INSTALLED_APPS + ('django_nose',)

        # disable custom loggers (prevents issues with nose)
        LOGGING = settings.LOGGING
        LOGGING['loggers'] = {}

        from urlparse import urljoin
        URI_BASE_PREFIX = 'http://data-test.venturi.fbk.eu/'
        settings.TRIPLE_DATABASE['PREFIXES']["sdres"] = \
            urljoin(URI_BASE_PREFIX, "/resource/")
        settings.TRIPLE_DATABASE['PREFIXES']["sdprop"] = \
            urljoin(URI_BASE_PREFIX, "/property/")
        settings.TRIPLE_DATABASE['PREFIXES']["graph"] = \
            urljoin(URI_BASE_PREFIX, "/graph/")
        settings.TRIPLE_DATABASE['PREFIXES']["silk_graph"] = \
            urljoin(URI_BASE_PREFIX, "/graph/mapped/silk")
        settings.TRIPLE_DATABASE['PREFIXES']["data_graph_raw"] = \
            urljoin(URI_BASE_PREFIX, "/graph/raw/")
        settings.TRIPLE_DATABASE['PREFIXES']["data_graph_mapped"] = \
            urljoin(URI_BASE_PREFIX, "/graph/mapped/")
        settings.TRIPLE_DATABASE['PREFIXES']["meta_graph"] = \
            urljoin(URI_BASE_PREFIX, "/graph/meta")
        settings.TRIPLE_DATABASE['PREFIXES']["geom"] = \
            urljoin(URI_BASE_PREFIX, "/geometry/")

        settings.TRIPLE_DATABASE_MASTER['PREFIXES'] = \
            settings.TRIPLE_DATABASE['PREFIXES']
        settings.TRIPLE_DATABASE_MASTER['KWARGS']['prefixes']['sdr'] = \
            settings.TRIPLE_DATABASE['PREFIXES']['sdres']
        settings.TRIPLE_DATABASE_MASTER['KWARGS']['prefixes']['sd'] = \
            settings.TRIPLE_DATABASE['PREFIXES']['sdv1']
        settings.TRIPLE_DATABASE_MASTER['KWARGS']['prefixes']['gt'] = \
            settings.TRIPLE_DATABASE['PREFIXES']['data_graph_mapped']

        NOSE_ARGS = [
            '--logging-filter=-nose,-south',
            '--with-blockage',
            '--http-whitelist=127.0.0.1,127.0.0.1:8890,127.0.0.1:8080,'
            '127.0.0.1:8891,localhost,{0},{0}:{1},127.0.0.1:8182,'
            'localhost:8182'
            .format(
                settings.REFINE_EXTERNAL_HOST, settings.REFINE_EXTERNAL_PORT
            )
        ]

        settings.update(locals())
