"""
config for jenkins, inherits test
"""
# pylint: disable=C0111,C0103,W0612,R0914
import os

from webui.conf.settings.test import Settings as TestSettings


class Settings(TestSettings):
    def run(self, settings):
        super(Settings, self).run(settings)

        REPORTS = settings.REPO_ROOT + '/reports/'

        NOSE_ARGS = settings.NOSE_ARGS + [
            '--with-xunit', '--xunit-file=' + REPORTS + 'nosetests.xml',
            '--with-coverage', '--cover-xml',
            '--cover-xml-file=' + REPORTS + 'coverage.xml',
            '--cover-branches', '--cover-package=webui',
            '-w' + settings.PROJECT_ROOT,
        ]

        # this env var should be set on jenkins
        if 'WORKSPACE' in os.environ:
            VIRTUAL_ENV_PATH = os.environ['WORKSPACE'] + '/.env'

        settings.update(locals())
