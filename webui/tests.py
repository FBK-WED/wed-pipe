import re
from django.conf import settings
from django.test import TestCase as DjangoTestCase

from django_nose.runner import NoseTestSuiteRunner
from mock import patch

from scheduler.test_helpers import WorkflowTestRunner


def rdflib_graph_parse_mock(self, source=None, *args, **kwargs):
    from util import get_test_file

    if source.startswith('http'):
        local_source = re.sub('\W+', '_', source)
        source = get_test_file(local_source, app_name='cnmain')

    return rdflib_graph_parse_mock._original(self, source, *args, **kwargs)


class TestCase(DjangoTestCase):
    """ our mighty test case
    """
    _passwords = {}

    def client_login(self, user):
        """
        login self.client with the given user (assuming username=password,
        or password stored in self._passwords
        """
        try:
            username = user.username
        except AttributeError:
            username = user

        password = self._passwords.get(username, username)

        self.client.login(username=user, password=password)
        return self.client

    @staticmethod
    def _get_test_file(filename, app_name='cnmain'):
        """ utility function around get_test_file """
        from util import get_test_file
        return get_test_file(filename, app_name)

    def run(self, result=None):
        mock = patch('rdflib.Graph.parse', rdflib_graph_parse_mock)
        rdflib_graph_parse_mock._original, _ = mock.get_original()
        with mock:
            super(TestCase, self).run(result)


class TestRunner(WorkflowTestRunner, NoseTestSuiteRunner):
    """
    Our test runner: load data before execution
    """
    @staticmethod
    def _loaddevdata():
        """
        Calls loaddevdata at the before tests
        """
        from django.core.management import call_command

        call_command(
            'loaddevdata',
            reset=False, interactive=False, commit=False, verbosity=0
        )

    @staticmethod
    def _clear_graphs():
        from webui.cnmain.utils import get_virtuoso

        get_virtuoso('default').clear_regex(
            settings.TRIPLE_DATABASE['PREFIXES']['graph']
        )
        get_virtuoso('master').clear_regex(
            settings.TRIPLE_DATABASE['PREFIXES']['graph']
        )

    @staticmethod
    def _clear_store():
        """
        Cleans the tabular store before executing the tests
        """
        import sqlalchemy
        args = dict(settings.TABULAR_DATABASE)
        args['PORT'] = args.get('PORT') or 5432

        conn_string = "postgresql://{USER}:{PASSWORD}@{HOST}:" \
            "{PORT}/postgres".format(**args)
        engine = sqlalchemy.create_engine(conn_string)
        conn = engine.connect()
        conn.execute('commit')
        conn.execute(
            'drop database if exists "{0}";'.format(
                settings.TABULAR_DATABASE['NAME']
            )
        )
        conn.execute('commit')
        conn.execute(
            'create database "{0}";'.format(settings.TABULAR_DATABASE['NAME'])
        )

    def setup_databases(self):
        """
        Call self._loaddevdata() after DB creation.
        """
        self._clear_store()

        res = super(TestRunner, self).setup_databases()

        self._loaddevdata()
        return res
