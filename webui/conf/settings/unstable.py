"""
config for production
"""
# pylint: disable=C0111,C0103,W0612,R0914
import os

from webui.conf import ClassSettings


class Settings(ClassSettings):
    def run(self, settings):
        super(Settings, self).run(settings)

        HOME_ROOT = os.path.dirname(settings.REPO_ROOT)

        STATIC_ROOT = os.path.join(HOME_ROOT, 'static')
        MEDIA_ROOT = os.path.join(HOME_ROOT, 'media')

        DEBUG = False

        ADMINS = (
            ('Marco Amadori', 'amadori@fbk.eu'),
        )

        VIRTUAL_ENV_PATH = '/home/venturi.fbk/.virtualenvs/controller'

        EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

        RAVEN_CONFIG = {
            'dsn': 'http://ba81fbd9745f4564af97d329b6ffcef8:'
                   '7869985194f841c6a58ba957c976c1b2@sentry.venturi.fbk.eu/5'
        }
#
        INSTALLED_APPS = tuple(settings.INSTALLED_APPS) + (
            'raven.contrib.django.raven_compat',
        )

        settings.TRIPLE_DATABASE['HOST'] = 'controller.venturi.fbk.eu'

        LOGGING = {
            'version': 1,
            'disable_existing_loggers': True,
            'root': {
                'level': 'WARNING',
                'handlers': ['sentry'],
            },
            'formatters': {
                'verbose': {
                    'format': '%(levelname)s %(asctime)s %(module)s '
                              '%(process)d %(thread)d %(message)s'
                },
            },
            'handlers': {
                'sentry': {
                    'level': 'ERROR',
                    'class': 'raven.contrib.django.raven_compat.handlers'
                             '.SentryHandler',
                },
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
                'raven': {
                    'level': 'DEBUG',
                    'handlers': ['console'],
                    'propagate': False,
                },
                'sentry.errors': {
                    'level': 'DEBUG',
                    'handlers': ['console'],
                    'propagate': False,
                },
            },
        }

        ALLOWED_HOSTS = ['controller.venturi.fbk.eu']

        settings.update(locals())
