# pylint: disable=E1103,R0904,C0111,C0103,E1101,C0302,W0232,R0201,W0212
from webui import settings
from webui.scheduler.models import Scheduler
from webui.scheduler.models.factories import DatasetSchedulerFactory, \
    AggregatorSchedulerFactory
from webui.tests import TestCase

from webui.controller.models.factories import ArchiveItemFactory, RuleFactory


class IndexViewTest(TestCase):
    def test_index_synced(self):
        obj = ArchiveItemFactory(
            file_hash='thesame',
            rule=RuleFactory(hash='thesame')
        )
        response = self.client.get('/')
        self.assertNotContains(response, obj.file_target)

    def test_index_unsynced(self):
        obj = ArchiveItemFactory(
            file_hash='thesame',
            rule=RuleFactory(hash='notthesame')
        )
        response = self.client.get('/')
        self.assertContains(response, obj.file_target)

    def test_index_archiveitem_no_rule(self):
        obj = ArchiveItemFactory(rule=None)
        response = self.client.get('/')
        self.assertNotContains(response, obj.file_target)

    def test_index_schedulers(self):
        scheduler_dataset = DatasetSchedulerFactory(
            status=Scheduler.FAIL)
        scheduler_aggregator = AggregatorSchedulerFactory(
            status=Scheduler.INCOMPLETE)
        scheduler_running = AggregatorSchedulerFactory(
            status=Scheduler.RUNNING)
        scheduler_success = AggregatorSchedulerFactory(
            status=Scheduler.SUCCESS)

        response = self.client.get('/')
        self.assertContains(
            response, scheduler_dataset.content_object.name)
        self.assertContains(
            response, scheduler_dataset.content_object.get_absolute_url())
        self.assertContains(
            response, scheduler_aggregator.content_object.name)
        self.assertContains(
            response, scheduler_aggregator.content_object.get_absolute_url())
        self.assertContains(
            response, scheduler_running.content_object.name)
        self.assertContains(
            response, scheduler_running.content_object.get_absolute_url())
        self.assertNotContains(
            response, scheduler_success.content_object.name)
        self.assertNotContains(
            response, scheduler_success.content_object.get_absolute_url())


class SparqlEndpointTest(TestCase):
    def setUp(self):
        self.url = '/sparql/'

    def test_get_with_default_query(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'SELECT DISTINCT ?concept WHERE')

    def test_get_with_given_query(self):
        query = 'something very cool but weird'
        response = self.client.get(self.url, data={'query': query})
        self.assertContains(response, query)

    def test_form_posts_on_real_endpoint(self):
        form_code = '<form action="http://{HOST}:{PORT}/{ENDPOINT}" ' \
                    'method="get">'.format(**settings.TRIPLE_DATABASE)
        response = self.client.get(self.url)
        self.assertContains(response, form_code)
