"""
config for development
"""
# pylint: disable=C0111,C0103,W0612,R0914
from webui.conf import ClassSettings


class Settings(ClassSettings):
    def run(self, settings):
        super(Settings, self).run(settings)

        # synchronous celery
        CELERY_ALWAYS_EAGER = True
        CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

        # Google Analytics
        GA_KEY = '123456789'

        ALLOWED_HOSTS = ['*']

        settings.update(locals())
