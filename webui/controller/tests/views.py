# pylint: disable=E1103,R0904,C0111,C0103,E1101,C0302,W0232,R0201,W0212
from urllib import quote_plus
from mock import MagicMock, patch

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from webui.cnmain.utils import get_virtuoso_endpoint

from webui.controller.models import Source, Dataset, ArchiveItem, Aggregator, \
    AggregatorArchiveItem
from webui.controller.models.factories import SourceFactory, DatasetFactory, \
    ArchiveItemFactory, RuleFactory, AggregatorFactory
from webui.controller.views import source_fetch_metadata
from webui.scheduler.models import Scheduler
from webui.scheduler.models.factories import DatasetSchedulerFactory, \
    AggregatorSchedulerFactory
from webui.importer.importer import MetadataImporter
from webui.tests import TestCase


class SourceListViewTest(TestCase):
    def test_get(self):
        response = self.client.get('/c/source/')
        self.assertContains(response, 'Source list')
        self.assertNotContains(
            response, settings.TEMPLATE_STRING_IF_INVALID_TEST
        )

    def test_contains_links(self):
        response = self.client.get('/c/source/')
        self.assertContains(response, '/c/source/create/')
        for source in Source.objects.all():
            self.assertContains(response, source.name)
            self.assertContains(response, source.get_absolute_url())


class SourceDetailViewTest(TestCase):
    def setUp(self):
        self.source = Source.objects.all()[0]

    def test_get(self):
        response = self.client.get(self.source.get_absolute_url())
        self.assertContains(response, self.source.name)

    def test_contains_edit_link(self):
        response = self.client.get(self.source.get_absolute_url())
        self.assertContains(
            response, self.source.get_absolute_url() + 'edit/'
        )

    def test_contains_sparql_metagraph_query(self):
        from webui.cnmain.utils import get_sparql_query_metagraph_info
        query = get_sparql_query_metagraph_info(self.source)
        response = self.client.get(self.source.get_absolute_url())
        self.assertContains(
            response, '<a href="/sparql/?query=' + quote_plus(query)
        )


class SourceCreateViewTest(TestCase):
    def setUp(self):
        self.create_url = '/c/source/create/'
        self.post_data = dict(SourceFactory.attributes(), user=1)

    def test_get_authenticated(self):
        self.client_login('admin')
        response = self.client.get(self.create_url)
        self.assertContains(response, 'Scraperwiki url')

    def test_get_anonymous(self):
        response = self.client.get(self.create_url)
        self.assertRedirects(response, '/login/?next=' + self.create_url)

    def test_post_authenticated(self):
        self.client_login('admin')

        # TODO[vad]: this is slow!
        Source.objects.all().delete()
        response = self.client.post(self.create_url, data=self.post_data)

        self.assertEqual(response.status_code, 302)
        source = Source.objects.get()
        self.assertEqual(source.name, self.post_data['name'])
        self.assertEqual(source.description, self.post_data['description'])

    def test_post_anonymous(self):
        Source.objects.all().delete()

        response = self.client.post(self.create_url, self.post_data)
        self.assertRedirects(response, '/login/?next=' + self.create_url)

        self.assertEqual(Source.objects.count(), 0)


class SourceUpdateViewTest(TestCase):
    def setUp(self):
        self.source = Source.objects.all()[0]
        self.update_url = self.source.get_absolute_url() + 'edit/'
        self.post_data = dict(SourceFactory.attributes(), user=1)

    def test_get_authenticated(self):
        self.client_login('admin')
        response = self.client.get(self.update_url)
        self.assertContains(response, 'Scraperwiki url')
        self.assertContains(response, self.source.description)

    def test_get_anonymous(self):
        response = self.client.get(self.update_url)
        self.assertRedirects(response, '/login/?next=' + self.update_url)

    def test_post_authenticated(self):
        self.client_login('admin')

        response = self.client.post(self.update_url, data=self.post_data)
        self.assertRedirects(response, self.source.get_absolute_url())

        source = Source.objects.get(pk=self.source.pk)
        self.assertEqual(source.name, self.post_data['name'])
        self.assertEqual(source.description, self.post_data['description'])

    def test_post_anonymous(self):
        response = self.client.post(self.update_url, data=self.post_data)
        self.assertRedirects(response, '/login/?next=' + self.update_url)

        source = Source.objects.get(pk=self.source.pk)
        self.assertNotEqual(source.name, self.post_data['name'])
        self.assertNotEqual(source.description, self.post_data['description'])


class DatasetDetailViewTest(TestCase):
    def setUp(self):
        self.dataset = Dataset.objects.all()[0]

    def test_get(self):
        response = self.client.get(self.dataset.get_absolute_url())
        self.assertContains(response, self.dataset.name)
        self.assertNotContains(
            response, settings.TEMPLATE_STRING_IF_INVALID_TEST
        )

    def test_contains_edit_link(self):
        response = self.client.get(self.dataset.get_absolute_url())
        self.assertContains(
            response, self.dataset.get_absolute_url() + 'edit/'
        )

    def test_contains_sparql_metagraph_query(self):
        from webui.cnmain.utils import get_sparql_query_metagraph_info
        query = get_sparql_query_metagraph_info(self.dataset)
        response = self.client.get(self.dataset.get_absolute_url())
        self.assertContains(
            response, '<a href="/sparql/?query=' + quote_plus(query)
        )


class DatasetCreateViewTest(TestCase):
    def setUp(self):
        self.source = Source.objects.all()[0]
        self.create_url = self.source.get_absolute_url() + 'dataset/create/'
        self.post_data = DatasetFactory.attributes()

    def test_get_authenticated(self):
        self.client.login(username='admin', password='admin')
        response = self.client.get(self.create_url)
        self.assertContains(response, 'Update rule')

    def test_get_anonymous(self):
        response = self.client.get(self.create_url)
        self.assertRedirects(response, '/login/?next=' + self.create_url)

    def test_post_authenticated(self):
        self.client.login(username='admin', password='admin')

        Dataset.objects.all().delete()
        response = self.client.post(self.create_url, data=self.post_data)

        self.assertEqual(response.status_code, 302)
        dataset = Dataset.objects.get()
        self.assertEqual(dataset.name, self.post_data['name'])
        self.assertEqual(dataset.description, self.post_data['description'])
        self.assertEqual(dataset.source, self.source)

    def test_post_anonymous(self):
        Dataset.objects.all().delete()

        response = self.client.post(self.create_url, self.post_data)
        self.assertRedirects(response, '/login/?next=' + self.create_url)

        self.assertEqual(Dataset.objects.count(), 0)


class DatasetUpdateViewTest(TestCase):
    def setUp(self):
        self.dataset = Dataset.objects.all()[0]
        self.update_url = self.dataset.get_absolute_url() + 'edit/'
        self.post_data = DatasetFactory.attributes()

    def test_get_authenticated(self):
        self.client.login(username='admin', password='admin')
        response = self.client.get(self.update_url)
        self.assertContains(response, 'Update rule')
        self.assertContains(response, self.dataset.description)

    def test_get_anonymous(self):
        response = self.client.get(self.update_url)
        self.assertRedirects(response, '/login/?next=' + self.update_url)

    def test_post_authenticated(self):
        self.client.login(username='admin', password='admin')

        response = self.client.post(self.update_url, data=self.post_data)
        self.assertRedirects(response, self.dataset.get_absolute_url())

        source = self.dataset.source
        dataset = Dataset.objects.get(pk=self.dataset.pk)
        self.assertEqual(dataset.name, self.post_data['name'])
        self.assertEqual(dataset.description, self.post_data['description'])
        self.assertEqual(dataset.source, source)

    def test_post_anonymous(self):
        response = self.client.post(self.update_url, data=self.post_data)
        self.assertRedirects(response, '/login/?next=' + self.update_url)

        source = self.dataset.source
        dataset = Dataset.objects.get(pk=self.dataset.pk)
        self.assertNotEqual(dataset.name, self.post_data['name'])
        self.assertNotEqual(dataset.description, self.post_data['description'])
        self.assertEqual(dataset.source, source)


class SourceFetchMetadataTestCase(TestCase):
    def test_source_fetch_metadata_success(self):
        request = MagicMock()
        request.method = 'POST'
        source = SourceFactory(
            name='test-source',
            scraper_name='prodottiprotettitrentino',
            scraperwiki_url=settings.SCRAPERWIKI_APP,
            scraper_api_key='61f623f3-04ba-4c71-ba8e-acc5e88b8202',
        )

        with patch.object(
                MetadataImporter,
                'read_metadata',
                return_value={'total': 1, 'errors': 0, 'report': []}):
            with patch.object(messages, 'info') as messages_info:
                source_fetch_metadata(request, source.pk)
                MetadataImporter.read_metadata.assert_called_once_with(
                    source
                )
                messages_info.assert_called_once_with(
                    request,
                    '1 metadata imported, 0 errors'
                )

    def test_source_fetch_metadata_fail(self):
        request = MagicMock()
        request.method = 'POST'
        source = SourceFactory(
            name='test-source',
            scraper_name='',
            scraperwiki_url=settings.SCRAPERWIKI_APP,
            scraper_api_key='61f623f3-04ba-4c71-ba8e-acc5e88b8202',
        )

        # pylint: disable=W0613
        def side_fun(*args, **kwargs):
            raise Exception('A scraper name must be specified.')

        with patch.object(
                MetadataImporter,
                'read_metadata',
                side_effect=side_fun):
            with patch.object(messages, 'error') as messages_error:
                source_fetch_metadata(request, source.pk)
                messages_error.assert_called_once_with(
                    request,
                    'Error while updating metadata'
                )


class WorkflowViews(TestCase):
    def setUp(self):
        self.source = Source.objects.all()[0]
        self.dataset = Dataset.objects.all()[0]
        self.source_workflow_url = \
            reverse('source_workflow', args=[self.source.pk, ])
        self.dataset_workflow_url = \
            reverse('dataset_workflow', args=[self.dataset.pk, ])

    def test_can_run_workflow_from_source(self):
        Scheduler.objects.all().delete()
        response = self.client.get(self.source.get_absolute_url())
        self.assertContains(response, self.source_workflow_url)

        response = self.client.post(self.source_workflow_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response['Location'].startswith('http://testserver/s/task/')
        )
        self.assertEqual(Scheduler.objects.count(), 1)

    def test_can_run_workflow_from_dataset(self):
        Scheduler.objects.all().delete()
        response = self.client.get(self.dataset.get_absolute_url())
        self.assertContains(response, self.dataset_workflow_url)

        response = self.client.post(self.dataset_workflow_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response['Location'].startswith('http://testserver/s/task/')
        )
        self.assertEqual(Scheduler.objects.count(), 1)

    def test_can_specify_to_skip_datasets_scheduled_recently(self):
        Scheduler.objects.all().delete()
        DatasetSchedulerFactory(object_id=self.source.datasets.get().pk)
        response = self.client.post(
            self.source_workflow_url,
            {'last_executed': 99999},
            follow=True
        )
        self.assertContains(response, 'No datasets to process')
        self.assertEqual(Scheduler.objects.count(), 1)


class SourceUploadMetadataFromCSV(TestCase):
    def setUp(self):
        self.source = Source.objects.all()[0]
        self.xmlfile_path = self._get_test_file('schema.xml', 'controller')
        self.csvfile_malformed_path = self._get_test_file(
            'source_metadata_malformed.csv', 'controller'
        )
        self.csvfile_correct_path = self._get_test_file(
            'source_metadata_correct.csv', 'controller'
        )
        self.upload_url = reverse(
            'source_upload_metadata', args=(self.source.pk, )
        )

    def test_require_post(self):
        for method in ['get', 'put', 'delete']:
            response = getattr(self.client, method)(self.upload_url)
            self.assertEqual(response.status_code, 405)  # method not allowed

    def test_source_upload_metadata_failed_no_file(self):
        response = self.client.post(self.upload_url)
        self.assertEqual(response.status_code, 400)  # bad request

    def test_source_upload_metadata_failed_wrong_type(self):
        post_data = {
            'upload_csv_file': open(self.xmlfile_path)
        }
        response = self.client.post(self.upload_url, post_data, follow=True)
        self.assertContains(response, 'error')
        self.assertContains(response, 'wrong type')

    def test_source_upload_metadata_failed_malformed_file(self):
        post_data = {
            'upload_csv_file': open(self.csvfile_malformed_path)
        }
        response = self.client.post(self.upload_url, post_data, follow=True)
        self.assertContains(response, 'error')
        self.assertContains(response, 'is an invalid keyword argument')

    def test_source_upload_metadata_success(self):
        Dataset.objects.all().delete()
        post_data = {
            'upload_csv_file': open(self.csvfile_correct_path)
        }
        response = self.client.post(self.upload_url, post_data, follow=True)

        self.assertContains(response, 'success')
        self.assertEqual(Dataset.objects.count(), 1)
        self.assertEqual(Dataset.objects.get().source, self.source)


class ArchiveItemDetailView(TestCase):
    def setUp(self):
        self.archive_item = ArchiveItemFactory()

    def test_archiveitem_empty(self):
        obj = ArchiveItemFactory()
        response = self.client.get(obj.get_absolute_url())

        self.assertContains(response, obj.dataset.get_absolute_url())
        self.assertContains(response, obj.dataset.source.get_absolute_url())
        self.assertContains(response, obj.tablename)

        self.assertNotContains(response, "Rule")
        self.assertNotContains(response, settings.REFINE_EXTERNAL_HOST)

    def test_archiveitem_with_refine_data(self):
        obj = ArchiveItemFactory(
            refine_url="http://blablah.com", refine_projectid="123213"
        )
        response = self.client.get(obj.get_absolute_url())

        self.assertContains(response, obj.refine_url)

    def test_archiveitem_with_rule(self):
        obj = ArchiveItemFactory(rule=RuleFactory())
        response = self.client.get(obj.get_absolute_url())

        self.assertContains(response, obj.rule.rule)

    def test_archiveitem_edit_rule(self):
        obj = ArchiveItemFactory(rule=RuleFactory())
        new_rule = '[{"that": "is a brand new rule :D"}]'

        response = self.client.post(
            obj.get_absolute_url(), {"rule": new_rule}, follow=True
        )

        self.assertContains(
            response,
            "[\n  {\n    &quot;that&quot;: &quot;is a brand new rule " +
            ":D&quot;\n  }\n]"
        )

    def test_contains_sparql_metagraph_query(self):
        from webui.cnmain.utils import get_sparql_query_metagraph_info
        query = get_sparql_query_metagraph_info(self.archive_item)
        response = self.client.get(self.archive_item.get_absolute_url())
        self.assertContains(
            response, '<a href="/sparql/?query=' + quote_plus(query)
        )

    def test_contains_sparql_datagraph_raw_query(self):
        from webui.cnmain.utils import get_sparql_query_graph
        query = get_sparql_query_graph(self.archive_item.datagraph_raw_name)
        response = self.client.get(self.archive_item.get_absolute_url())
        self.assertContains(
            response, '<a href="/sparql/?query=' + quote_plus(query)
        )

    def test_contains_sparql_datagraph_mapped_query(self):
        from webui.cnmain.utils import get_sparql_query_graph
        query = get_sparql_query_graph(self.archive_item.datagraph_mapped_name)
        response = self.client.get(self.archive_item.get_absolute_url())
        self.assertContains(
            response, '<a href="/sparql/?query=' + quote_plus(query)
        )


class ArchiveItemCSVView(TestCase):
    def test_archiveitem_csv_no_table(self):
        obj = ArchiveItemFactory()
        csv_url = reverse("archiveitem_csv", kwargs={"pk": obj.pk})

        response = self.client.get(csv_url)
        self.assertEqual(response.status_code, 404)

    def test_archiveitem_csv_ok(self):
        obj = ArchiveItemFactory()
        with patch.object(
            ArchiveItem, 'data',
            return_value=((x, x, 42) for x in range(20))
        ):
            csv_url = reverse("archiveitem_csv", kwargs={"pk": obj.pk})

            response = self.client.get(csv_url)

            self.assertEqual(response['Content-Type'], 'text/csv')
            self.assertContains(response, '1,1,42')
            self.assertEqual(len(response.content.split("\n")), 21)


class ArchiveItemRefineSyncView(TestCase):
    def test_archiveitem_sync(self):
        from refine.refine import IllegalRuleCheckSum
        rule = {"amazing": "rule"}
        obj = ArchiveItemFactory(
            rule=RuleFactory(hash="LOL", rule=rule),
            file_hash="WUT"
        )

        with self.assertRaises(IllegalRuleCheckSum):
            obj.get_refine_rule()

        self.client.post(
            reverse("archiveitem_refine_sync", kwargs={'pk': obj.pk})
        )

        obj = ArchiveItem.objects.get(pk=obj.pk)
        self.assertEquals(obj.get_refine_rule(), rule)


class ArchiveItemMappedStatsView(TestCase):
    def test_contains_mapped_stats_link(self):
        obj = ArchiveItem.objects.all()[0]
        response = self.client.get(obj.get_absolute_url())
        self.assertContains(
            response, '<a href="{}mapped/stats/'.format(obj.get_absolute_url())
        )

    def test_mapped_stats(self):
        from webui.scheduler.tasks import process_dataset

        obj = Dataset.objects.get(name='osm-dataset')
        process_dataset.delay(obj)

        archive_item = obj.archive_items.all()[0]
        response = self.client.get(
            archive_item.get_absolute_url() + 'mapped/stats/'
        )
        self.assertContains(response, "10")
        self.assertContains(response, "5")


class ArchiveItemAggregatorAddView(TestCase):
    def setUp(self):
        self.archiveitem = ArchiveItemFactory()
        self.aggregator = AggregatorFactory()
        self.url = reverse('archiveitem_aggregator_add',
                           args=(self.archiveitem.pk, ))

    def test_add(self):
        post_data = {"aggregator": self.aggregator.pk}
        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertEquals(len(self.archiveitem.aggregators.all()), 1)
        self.assertContains(response, 'success')

    def test_add_invalid(self):
        post_data = {"aggregator": 99999}
        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertEquals(len(self.archiveitem.aggregators.all()), 0)
        self.assertContains(response, 'error')


class ArchiveItemAggregatorDelView(TestCase):
    def setUp(self):
        self.archiveitem = ArchiveItemFactory()
        self.aggregator = AggregatorFactory()
        AggregatorArchiveItem.objects.create(
            aggregator=self.aggregator,
            archiveitem=self.archiveitem,
        )
        self.url = reverse('archiveitem_aggregator_del',
                           args=(self.archiveitem.pk, ))

    def test_del(self):
        self.client_login('admin')
        self.assertEquals(len(self.archiveitem.aggregators.all()), 1)

        post_data = {"aggregator": self.aggregator.pk}
        response = self.client.post(self.url, data=post_data, follow=True)

        self.assertContains(response, 'success')
        self.assertEquals(len(self.archiveitem.aggregators.all()), 0)

    def test_del_invalid(self):
        self.client_login('admin')

        self.assertEquals(len(self.archiveitem.aggregators.all()), 1)

        post_data = {"aggregator": 99999}
        response = self.client.post(self.url, data=post_data, follow=True)
        self.assertEquals(len(self.archiveitem.aggregators.all()), 1)
        self.assertContains(response, 'error')

        response = self.client.get(self.archiveitem.get_absolute_url())
        self.assertContains(response, self.aggregator.name)


class AggregatorListViewTest(TestCase):
    def test_get(self):
        self.client_login('admin')

        response = self.client.get('/c/aggregator/')
        self.assertContains(response, 'Aggregator list')
        self.assertNotContains(
            response, settings.TEMPLATE_STRING_IF_INVALID_TEST
        )

    def test_contains_links(self):
        self.client_login('admin')

        response = self.client.get('/c/aggregator/')
        self.assertContains(response, '/c/aggregator/create/')
        for aggregator in Aggregator.objects.all():
            self.assertContains(response, aggregator.name)
            self.assertContains(response, aggregator.get_absolute_url())


class AggregatorDetailViewTest(TestCase):
    def setUp(self):
        self.client_login('admin')

        self.aggregator = AggregatorFactory()
        self.export_url = reverse(
            'aggregator_export', args=(self.aggregator.pk, )
        )
        self.workflow_url = reverse(
            'aggregator_workflow', args=[self.aggregator.pk, ])

    def test_get(self):
        response = self.client.get(self.aggregator.get_absolute_url())
        self.assertContains(response, self.aggregator.name)

    def test_contains_edit_link(self):
        response = self.client.get(self.aggregator.get_absolute_url())
        self.assertContains(
            response, self.aggregator.get_absolute_url() + 'edit/'
        )

    def test_contains_archiveitems(self):
        item1 = ArchiveItemFactory()
        item2 = ArchiveItemFactory()
        for item in (item1, item2):
            AggregatorArchiveItem.objects.create(
                aggregator=self.aggregator,
                archiveitem=item
            )

        response = self.client.get(self.aggregator.get_absolute_url())
        self.assertContains(response, item1.get_absolute_url())
        self.assertContains(response, item2.get_absolute_url())

    def test_contains_rule(self):
        self.aggregator.silk_rule = 'tanto gentile e tanto onesta pare'
        self.aggregator.save()

        response = self.client.get(self.aggregator.get_absolute_url())
        self.assertContains(response, self.aggregator.silk_rule)

    def test_contains_schedulers(self):
        response = self.client.get(self.aggregator.get_absolute_url())
        self.assertContains(response, 'No scheduler found')

        scheduler = AggregatorSchedulerFactory(object_id=self.aggregator.pk)
        response = self.client.get(self.aggregator.get_absolute_url())
        self.assertNotContains(response, 'No scheduler found')
        self.assertContains(response, scheduler.get_absolute_url())

    def test_contains_silk_link(self):
        response = self.client.get(self.aggregator.get_absolute_url())
        silk_url = 'http://{}:{}/workbench/'.format(
            settings.SILK_EXTERNAL_HOST, settings.SILK_EXTERNAL_PORT
        )
        self.assertContains(response, silk_url)

    def test_can_download_silk_project_file(self):
        self.client_login('admin')

        response = self.client.get(self.aggregator.get_absolute_url())
        self.assertContains(response, self.export_url + '?download')

        response = self.client.get(self.export_url + '?download')
        self.assertEqual(response['Content-Type'], 'text/xml; charset=utf-8')
        self.assertTrue(response.has_header('Content-Disposition'))
        self.assertNotEqual(response.content.strip(), '')

    def test_can_run_workflow(self):
        self.client_login('admin')
        Scheduler.objects.all().delete()
        response = self.client.get(self.aggregator.get_absolute_url())
        self.assertContains(response, self.workflow_url)

        response = self.client.post(self.workflow_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response['Location'].startswith('http://testserver/s/task/')
        )
        self.assertEqual(Scheduler.objects.count(), 1)

    def test_can_view_silk_project_file_without_downloading(self):
        self.client_login('admin')
        response = self.client.get(self.export_url)
        self.assertEqual(response['Content-Type'], 'text/xml; charset=utf-8')
        self.assertFalse(response.has_header('Content-Disposition'))
        self.assertNotEqual(response.content.strip(), '')

    def test_silk_project_file_is_valid(self):
        import xml.etree.ElementTree as ET

        self.client_login('admin')

        item1 = ArchiveItemFactory()
        item2 = ArchiveItemFactory()
        for item in (item1, item2):
            AggregatorArchiveItem.objects.create(
                aggregator=self.aggregator,
                archiveitem=item
            )

        response = self.client.get(self.export_url)
        tree = ET.fromstring(response.content)

        self.assertIn(
            (settings.TRIPLE_DATABASE['PREFIXES']['sdv1'], 'sd'),
            [(x.get('namespace'), x.get('id'))
             for x in tree.findall('.//Prefix')]
        )

        # check datasources
        datasources = tree.findall('.//DataSource')
        self.assertEqual(len(datasources), 3)
        self.assertEqual(datasources[0].get('id'), 'master-graph')

        mastergraph = datasources[0]
        datasources = datasources[1:]

        # check datasources endpoints
        self.assertEqual(
            mastergraph.find('Param[@name="host"]').get('value'),
            settings.TRIPLE_DATABASE_MASTER['HOST']
        )
        self.assertEqual(
            [get_virtuoso_endpoint()] * 2,
            [x.find('Param[@name="endpointURI"]').get("value")
             for x in datasources]
        )

        # check datasources graph names
        self.assertEqual(
            mastergraph.find('Param[@name="graph"]').get('value'),
            settings.TRIPLE_DATABASE_MASTER["KWARGS"]["graph"]
        )
        self.assertEqual(
            [item1.datagraph_mapped_name, item2.datagraph_mapped_name],
            [x.find('Param[@name="graph"]').get("value")
             for x in datasources]
        )

        # check tasks
        datasource_ids = [x.get('id') for x in datasources]
        tasks = tree.findall('.//LinkingTask')
        self.assertEqual(len(tasks), 2)
        self.assertEqual(
            datasource_ids,
            [x.find('.//Interlink').get('id') for x in tasks]
        )

        # check task parameters
        for datasource_id, task in zip(datasource_ids, tasks):
            self.assertEqual(
                task.find('.//SourceDataset').get('dataSource'),
                datasource_id
            )
            self.assertEqual(
                task.find('.//TargetDataset').get('dataSource'),
                'master-graph'
            )
            self.assertEqual(
                task.find('.//SourceDataset').find('RestrictTo').text.strip(),
                '?a rdf:type <{}> .'.format(self.aggregator.entity_type)
            )
            self.assertEqual(
                task.find('.//TargetDataset').find('RestrictTo').text.strip(),
                'b -> {}'.format(self.aggregator.vertex_selector)
            )
            self.assertIsNone(task.find('.//LinkageRule').text)
            self.assertIsNone(task.find('.//Filter').text)
            self.assertIsNone(task.find('.//Outputs').text)
            self.assertIsNone(task.find('.//PositiveEntities').text)
            self.assertIsNone(task.find('.//NegativeEntities').text)
            self.assertIsNone(
                task.find('.//Alignment/')
                    .find('{}Alignment'.format('{http://knowledgeweb.'
                                               'semanticweb.org'
                                               '/heterogeneity/alignment#}')
                          ).text
            )


class AggregatorCreateViewTest(TestCase):
    def setUp(self):
        self.create_url = '/c/aggregator/create/'
        self.post_data = dict(AggregatorFactory.attributes())

    def test_post(self):
        self.client_login('admin')
        Aggregator.objects.all().delete()
        response = self.client.post(self.create_url, data=self.post_data)

        self.assertEqual(response.status_code, 302)
        aggregator = Aggregator.objects.get()
        self.assertEqual(aggregator.name, self.post_data['name'])
        self.assertEqual(aggregator.description, self.post_data['description'])


class AggregatorUpdateViewTest(TestCase):
    def setUp(self):
        self.aggregator = AggregatorFactory()
        self.update_url = self.aggregator.get_absolute_url() + 'edit/'
        self.post_data = dict(AggregatorFactory.attributes())

    def test_get(self):
        self.client_login('admin')
        response = self.client.get(self.update_url)
        self.assertContains(response, self.aggregator.name)
        self.assertContains(response, self.aggregator.description)

    def test_post(self):
        self.client_login('admin')
        archiveitem = ArchiveItemFactory()
        self.post_data['archiveitems'] = [archiveitem.pk]
        print self.post_data
        response = self.client.post(self.update_url, data=self.post_data)
        self.assertRedirects(response, self.aggregator.get_absolute_url())

        aggregator = Aggregator.objects.get(pk=self.aggregator.pk)
        self.assertEqual(aggregator.name, self.post_data['name'])
        self.assertEqual(aggregator.description, self.post_data['description'])
        self.assertIn(archiveitem, aggregator.archiveitems.all())


class AggregatorImportViewTest(TestCase):
    def setUp(self):
        self.aggregator = AggregatorFactory()
        self.update_url = self.aggregator.get_absolute_url() + 'post/'
        self.post_data = dict()
        self.post_data['silk_rule_file'] = open(
            self._get_test_file('config.xml', 'controller')
        )

    def test_post(self):
        self.client_login('admin')

        archiveitem = ArchiveItemFactory()
        self.post_data['archiveitems'] = [archiveitem.pk]
        response = self.client.post(self.update_url, data=self.post_data)
        self.assertRedirects(response, self.aggregator.get_absolute_url())

        aggregator = Aggregator.objects.get(pk=self.aggregator.pk)
        self.assertEqual(
            aggregator.silk_rule.strip().replace("\n", ""),
            '<LinkageRule>        '
            '<Compare id="unnamed_5" metric="levenshtein" required="false" '
            'threshold="0.0" weight="1">          '
            '<TransformInput function="lowerCase" id="unnamed_3">            '
            '<Input id="unnamed_1" path="?a/sd:Event#name" />          '
            '</TransformInput>          <TransformInput function="lowerCase" '
            'id="unnamed_4">            '
            '<Input id="unnamed_2" path="?b/sd:Event#name" />          '
            '</TransformInput>          <Param name="minChar" value="0" />'
            '          <Param name="maxChar" value="z" />        '
            '</Compare>      </LinkageRule>'.strip()
        )
