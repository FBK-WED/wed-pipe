# pylint: disable=E1103,R0904,C0111,C0103,E1101,C0302,W0232,R0201,W0212
from webui.controller.models.factories import SourceFactory, DatasetFactory
from webui.scheduler.models.factories import DatasetSchedulerFactory, \
    AggregatorSchedulerFactory
from webui.tests import TestCase
from webui.scheduler.tasks import process_source, process_dataset


class SchedulerResultDetailViewTestCase(TestCase):
    def test_it_works_for_sources(self):
        obj = SourceFactory()

        task = process_source.delay(obj)

        response = self.client.get('/s/task/{}/'.format(task.id))
        self.assertContains(response, 'Evaluating Init Handler')

    def test_it_works_for_datasets(self):
        obj = DatasetFactory()

        task = process_dataset.delay(obj)

        response = self.client.get('/s/task/{}/'.format(task.id))
        self.assertContains(response, 'Processing dataset {}'.format(obj))


class SchedulerDetailViewTestCase(TestCase):
    def test_it_works(self):
        scheduler = DatasetSchedulerFactory()

        response = self.client.get('/s/scheduler/{}/'.format(scheduler.pk))

        self.assertContains(response, scheduler.content_object.name)


class SchedulerListViewTestCase(TestCase):
    def test_with_no_params(self):
        scheduler = DatasetSchedulerFactory()

        response = self.client.get('/s/scheduler/')

        self.assertContains(response, scheduler.content_object.name)

    def test_it_filters_on_dataset(self):
        scheduler = DatasetSchedulerFactory()
        DatasetSchedulerFactory(object_id=DatasetFactory(name='NOT ME').pk)
        dataset = scheduler.content_object

        response = self.client.get(
            '/s/scheduler/?model=dataset&pk={}'.format(dataset.pk)
        )

        self.assertContains(response, dataset.name)
        self.assertNotContains(response, 'NOT ME')

    def test_it_filters_on_source(self):
        scheduler = DatasetSchedulerFactory()
        DatasetSchedulerFactory(object_id=DatasetFactory(name='NOT ME').pk)
        source = scheduler.content_object.source

        response = self.client.get(
            '/s/scheduler/?model=source&pk={}'.format(source.pk)
        )

        self.assertContains(response, scheduler.content_object.name)
        self.assertNotContains(response, 'NOT ME')

    def test_it_filters_on_aggregator(self):
        scheduler = AggregatorSchedulerFactory()
        DatasetSchedulerFactory(object_id=DatasetFactory(name='NOT ME').pk)

        response = self.client.get(
            '/s/scheduler/?model=aggregator&pk={}'.format(scheduler.object_id)
        )

        self.assertContains(response, scheduler.content_object.name)
        self.assertNotContains(response, 'NOT ME')
