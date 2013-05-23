# pylint: disable=E1103,R0904,C0111,C0103,E1101,C0302,W0232,R0201,W0212
from unittest import skip

from mock import patch, MagicMock

from django.conf import settings

from webui.cnmain.utils import get_virtuoso_endpoint
from webui.controller.models import Source, ArchiveItem, Aggregator, Dataset, \
    AggregatorArchiveItem
from webui.controller.models.factories import SourceFactory, DatasetFactory, \
    RuleFactory, AggregatorFactory, ArchiveItemFactory
from webui.scheduler.models import Scheduler
from webui.scheduler.models.factories import SchedulerFactory
from webui.tests import TestCase
from webui.scheduler.tasks import process_source, process_dataset, \
    process_aggregator


class ProcessSourceTestCase(TestCase):
    def test_it_logs_using_redis_logger(self):
        obj = SourceFactory()

        loggy = MagicMock()
        with patch('webui.scheduler.tasks.get_redis_logger',
                   return_value=loggy):
            process_source.delay(obj)

            self.assert_(loggy.info.called)

    def test_dataset_subtasks_log_using_the_same_redis_key(self):
        source = SourceFactory(name='boo name')
        source.datasets.add(DatasetFactory(
            name='wow name'
        ))

        loggy = MagicMock()
        with patch('webui.scheduler.tasks.get_redis_logger',
                   return_value=loggy) as get_redis_logger:
            task = process_source.delay(source)

            #TODO[vad]: this is broken! assert_calls is not a magick method
            get_redis_logger.assert_calls([task.id, task.id])

    def _assert_archive_item(self, archive_item, header, n_tuples,
                             conditions=None):
        data_iter = archive_item.data()
        actual_header = data_iter.next()
        data = list(data_iter)

        self.assertEqual(actual_header, header)
        if conditions:
            for row in data:
                for field, fun in conditions.iteritems():
                    self.assertTrue(
                        fun(row[actual_header.index(field)])
                    )
        self.assertEqual(len(data), n_tuples)

    def _assert_triple(self, the_repr, prop, val, val_type='literal'):
        """ @param the_repr: a dict returned by the sparql end-point in
        response to a SELECT query
        """
        obj = the_repr[str(prop)]

        self.assertEqual(obj.value, str(val))
        obj_datatype = type(obj).__name__.lower()
        self.assertEqual(obj_datatype, val_type)

    def _assert_description(self, virtuoso, resource_id, assertions):
        """ given a virtuoso instance and a resource_id, execute a
        SELECT query and checks @assertions on it """
        result = virtuoso.client_query(
            'SELECT * WHERE {{<{}> ?b ?c}}'.format(resource_id)
        )
        res = {
            elem[0].value: elem[1] for elem in result.fetchall()
        }

        for assertion in assertions:
            self._assert_triple(res, *assertion)

    def test_source_scraperwiki(self):
        Scheduler.objects.all().delete()
        ArchiveItem.objects.all().delete()
        source = Source.objects.get(name='trentinocultura')
        process_source.delay(source)

        dataset = source.datasets.get()
        archive_item = source.datasets.get().archive_items.get()
        self._assert_archive_item(
            archive_item,
            (u'category', u'city', u'title', u'url', u'price',
             u'hours', u'website', u'phone', u'location', u'address', u'date',
             u'notes', u'email', u'organizer', u'other_info', u'fax'),
            49
        )

        from webui.cnmain.utils import get_virtuoso
        virtuoso = get_virtuoso()
        source_meta_id = source.metagraph_resource_id
        dataset_meta_id = dataset.metagraph_resource_id

        from rdflib import Namespace
        METAPROP = Namespace(settings.TRIPLE_DATABASE['PREFIXES']['meta'])
        SDOWL = Namespace(settings.TRIPLE_DATABASE['PREFIXES']['sdowl'])
        RDF_TYPE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'

        self._assert_description(virtuoso, source_meta_id, [
            (METAPROP['description'], source.description),
            (RDF_TYPE, SDOWL['Source'], 'iri'),
        ])
        self._assert_description(virtuoso, dataset_meta_id, [
            (METAPROP['download'], dataset.download),
            (RDF_TYPE, SDOWL['Dataset'], 'iri'),
            (SDOWL['belongs_to_source'], source_meta_id, 'iri'),
        ])
        # self._assert_description(virtuoso, archive_item_meta_id, [
        #     (METAPROP['rule'], archive_item.get_refine_rule(False)),
        #     (RDF_TYPE, SDOWL['ArchiveItem'], 'uri'),
        #     (SDOWL['belongs_to_dataset'], dataset_meta_id, 'uri'),
        # ])

    def test_source_csv_with_tab_delimiter(self):
        Scheduler.objects.all().delete()
        ArchiveItem.objects.all().delete()
        source = Source.objects.get(name='in-giro (locale)')
        dataset = source.datasets.get()
        dataset.csv_delimiter = '\\t'
        dataset.download = 'http://testserver/csv_with_tab_delimiter.csv'
        dataset.save()

        process_source.delay(source)

        archive_item = dataset.archive_items.get()

        self._assert_archive_item(archive_item, (u'col1', u'col2', u'col3'), 4)

    def test_source_csv_with_different_delimiter(self):
        Scheduler.objects.all().delete()
        ArchiveItem.objects.all().delete()
        source = Source.objects.get(name='in-giro (locale)')
        dataset = source.datasets.get()
        dataset.csv_delimiter = '$'
        dataset.download = 'http://testserver/csv_with_different_delimiter.csv'
        dataset.save()
        process_source.delay(source)

        archive_item = dataset.archive_items.get()

        self._assert_archive_item(archive_item, (u'col1', u'col2', u'col3'), 4)

    def test_source_csv_with_single_quotes(self):
        Scheduler.objects.all().delete()
        ArchiveItem.objects.all().delete()
        source = Source.objects.get(name='in-giro (locale)')
        dataset = source.datasets.get()
        dataset.csv_quotechar = "'"
        dataset.download = 'http://testserver/csv_with_single_quotes.csv'
        dataset.save()

        process_source.delay(source)

        archive_item = dataset.archive_items.get()

        self._assert_archive_item(archive_item, (u'col1', u'col2', u'col3'), 3)
        data = list(archive_item.data())
        self.assertEqual(data[1][0], 'testo lungo e bello')
        self.assertEqual(
            data[1][1], """guarda posso mettere sia " che \"\"\""""
        )

    def test_source_csv_with_weird_quotes(self):
        Scheduler.objects.all().delete()
        ArchiveItem.objects.all().delete()
        source = Source.objects.get(name='in-giro (locale)')
        dataset = source.datasets.get()
        dataset.csv_quotechar = "&"
        dataset.download = 'http://testserver/csv_with_weird_quotes.csv'
        dataset.save()
        process_source.delay(source)

        archive_item = dataset.archive_items.get()

        self._assert_archive_item(archive_item, (u'col1', u'col2', u'col3'), 3)
        data = list(archive_item.data())
        self.assertEqual(data[1][0], 'testo lungo e bello')
        self.assertEqual(data[1][1], """guarda posso mettere sia " che '""")

    def test_source_archive(self):
        Scheduler.objects.all().delete()
        ArchiveItem.objects.all().delete()
        source = Source.objects.get(name='in-giro (locale)')
        dataset = source.datasets.get()
        process_source.delay(source)

        events_item, poi_event = dataset.archive_items.all().\
            order_by("file_hash")

        self._assert_archive_item(
            poi_event,
            (u'website', u'city', u'name', u'url', u'phone', u'address',
             u'location_type', u'description', u'province'),
            158
        )

        self._assert_archive_item(
            events_item,
            (u'city', u'description', u'url', u'date', u'location',
             u'genre', u'location_url'),
            497
        )

        from webui.cnmain.utils import get_virtuoso
        virtuoso = get_virtuoso()
        source_meta_id = source.metagraph_resource_id
        dataset_meta_id = dataset.metagraph_resource_id

        from rdflib import Namespace
        METAPROP = Namespace(settings.TRIPLE_DATABASE['PREFIXES']['meta'])
        SDOWL = Namespace(settings.TRIPLE_DATABASE['PREFIXES']['sdowl'])
        RDF_TYPE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'

        self._assert_description(virtuoso, source_meta_id, [
            (METAPROP['description'], source.description),
            (RDF_TYPE, SDOWL['Source'], 'iri'),
        ])
        self._assert_description(virtuoso, dataset_meta_id, [
            (METAPROP['download'], dataset.download),
            (RDF_TYPE, SDOWL['Dataset'], 'iri'),
            (SDOWL['belongs_to_source'], source_meta_id, 'iri'),
        ])

    @skip("Now the refined data is not saved in the db")
    def test_source_with_refine_rule(self):
        Scheduler.objects.all().delete()
        ArchiveItem.objects.all().delete()
        source = Source.objects.get(name='trentinocultura')
        process_source.delay(source)

        rule = r"""[
          {
            "operation": {
              "repeat": false,
              "description": "Text transform on cells in column phone",
              "onError": "keep-original",
              "repeatCount": 10,
              "columnName": "phone",
              "engineConfig": {
                "facets": [],
                "mode": "row-based"
              },
              "expression": "jython:return value.replace(\"0\", \"x\") """ + \
            """if value else None",
                  "op": "core/text-transform"
                }
              }
            ]"""

        archive_item = source.datasets.get().archive_items.get()
        archive_item.rule = RuleFactory(
            rule=rule,
            hash=archive_item.file_hash
        )
        archive_item.save(force_update=True)

        process_source.delay(source)

        self._assert_archive_item(
            archive_item,
            (u'__sd_hash__', u'category', u'city', u'title', u'url', u'price',
             u'hours', u'website', u'phone', u'location', u'address', u'date',
             u'notes', u'email', u'organizer', u'other_info', u'fax'),
            49,
            {
                'phone': lambda x: not x or x.find('0') == -1
            }
        )

    def test_source_with_refine_rdf_rule(self):
        source = Source.objects.get(name='BoardGameTournament (test)')
        process_source.delay(source)

        path = self._get_test_file(
            "boardgametournament_refine_rules.json", "cnmain"
        )
        with open(path) as f:
            rule = f.read()

        dataset = source.datasets.get(name="boardgametournament-games")
        archive_item = dataset.archive_items.get()
        archive_item.rule = RuleFactory(
            rule=rule,
            hash=archive_item.file_hash
        )
        archive_item.save(force_update=True)

        process_source.delay(source)

        from webui.cnmain.utils import get_virtuoso
        virtuoso = get_virtuoso()
        row_id = archive_item.datagraph_mapped_row_id("0")

        self._assert_description(virtuoso, row_id, [
            ("http://ontologies.venturi.eu/v1#name",
             "Dominion"),
        ])

        row_id = archive_item.datagraph_mapped_row_id("1")

        self._assert_description(virtuoso, row_id, [
            ("http://ontologies.venturi.eu/v1#name",
             "Carcassonne"),
        ])


class ProcessDatasetTestCase(TestCase):
    def test_it_logs_using_redis_logger(self):
        obj = DatasetFactory()

        loggy = MagicMock()
        with patch('webui.scheduler.tasks.get_redis_logger',
                   return_value=loggy):
            process_dataset.delay(obj)

            self.assert_(loggy.info.called)

    def test_shp_ingestion(self):
        obj = Dataset.objects.get(name="Aeroporti")
        process_dataset.delay(obj)

        self.assertEqual(len(obj.archive_items.all()), 1)

        archiveitem = obj.archive_items.all()[0]
        self.assertEqual(len(list(archiveitem.data())), 5)

    def test_shp_ingestion_encoding(self):
        obj = Dataset.objects.get(name="Aeroporti")
        obj.download = 'http://testserver/poiGenerici.zip'
        obj.encoding = 'latin1'
        obj.save()

        process_dataset.delay(obj)

        # test it does not crash
        self.assertEqual(len(obj.archive_items.all()), 1)
        archiveitem = obj.archive_items.all()[0]
        self.assertEqual(len(list(archiveitem.data())), 2322)

    def test_shp_ingestion_without_projection(self):
        from sqlalchemy.exc import NoSuchTableError

        obj = Dataset.objects.get(name="osm-dataset")
        obj.download = 'http://testserver/aeroporti_tn_no_prj.zip'
        obj.save()
        obj.archive_items.all().delete()
        process_dataset.delay(obj)

        self.assertEqual(len(obj.archive_items.all()), 1)
        archiveitem = obj.archive_items.all()[0]

        with self.assertRaises(NoSuchTableError):
            list(archiveitem.data())

    def test_shp_ingestion_with_given_projection(self):
        import re

        obj = Dataset.objects.get(name="Aeroporti")
        obj.download = 'http://testserver/aeroporti_tn_no_prj.zip'
        obj.projection = 'epsg:3064'
        obj.save()
        process_dataset.delay(obj)

        self.assertEqual(len(obj.archive_items.all()), 1)
        archiveitem = obj.archive_items.all()[0]
        data = list(archiveitem.data())
        self.assertEqual(len(data), 5)
        match = re.search(r'POLYGON \(\(([0-9\.]+) ([0-9\.]+)', data[1][5])
        lon, lat = match.groups()
        self.assertEqual(int(float(lon)), 11)
        self.assertEqual(int(float(lat)), 46)

    def test_xls_ingestion(self):
        obj = Dataset.objects.get(name="boardgametournament-games-xls")
        process_dataset.delay(obj)

        self.assertEqual(len(obj.archive_items.all()), 1)

        archiveitem = obj.archive_items.all()[0]
        self.assertEqual(len(list(archiveitem.data())), 5)

    def test_xlsx_ingestion(self):
        obj = Dataset.objects.get(name="boardgametournament-games-xlsx")
        process_dataset.delay(obj)

        self.assertEqual(len(obj.archive_items.all()), 1)

        archiveitem = obj.archive_items.all()[0]
        self.assertEqual(len(list(archiveitem.data())), 5)

    def test_csvkit_no_inference(self):
        obj = Dataset.objects.get(name="strange symbols")
        process_dataset.delay(obj)

        self.assertEqual(len(obj.archive_items.all()), 1)
        archiveitem = obj.archive_items.all()[0]
        data = archiveitem.data()
        data.next()
        for row in data:
            row = list(row)
            self.assertIn(u"None", row)
            self.assertIn(u"0", row[-1])
            self.assertIn(u"+", row[-2])

    def test_dataset_encoding(self):
        from sqlalchemy.exc import NoSuchTableError

        obj = Dataset.objects.get(name="looks like ascii")
        obj.encoding = "us-ascii"
        obj.save()
        process_dataset.delay(obj)
        with self.assertRaises(NoSuchTableError):
            obj.archive_items.all()[0].data().next()

        obj.encoding = "UTF-8"
        obj.save()
        process_dataset.delay(obj)
        self.assertEqual(len(obj.archive_items.all()), 1)

    def test_zip_extraction_and_deletion(self):
        import os.path
        import shutil
        from webui.scheduler.test_helpers import _get_downloaded_file

        obj = Dataset.objects.get(name="Aeroporti")
        process_dataset.delay(obj)
        self.assertEqual(len(obj.archive_items.all()), 1)

        # copy another test file into the zip extraction dir
        data = _get_downloaded_file("aeroporti_tn.zip")
        zip_dir = data['out_file'] + "__exp"
        bgg_file = _get_downloaded_file("boardgamegeek.csv")
        new_file = os.path.join(zip_dir, "im_a_new_file.csv")
        shutil.copy(bgg_file['out_file'], new_file)

        # run again the workflow and check that the zip extraction dir is
        # cleaned and no archiveitem is created for im_a_new_file.csv
        process_dataset.delay(obj)

        self.assertFalse(os.path.exists(new_file))
        self.assertEqual(len(obj.archive_items.all()), 1)


class SilkRuleXMLTestCase(TestCase):
    def setUp(self):
        self.aggregator = AggregatorFactory()

    def test_can_silk_rules_file_is_valid(self):
        import xml.etree.ElementTree as ET
        from django.template.loader import render_to_string

        archive_item = ArchiveItemFactory()
        AggregatorArchiveItem.objects.create(
            aggregator=self.aggregator,
            archiveitem=archive_item
        )

        self.aggregator.silk_rule = \
            '<LinkageRule><smart data="now" /></LinkageRule>'
        self.aggregator.save()
        output_filename = 'a_really_cool_filename.thm'

        context = {
            'aggregator': self.aggregator,
            'sd_prefix': settings.TRIPLE_DATABASE['PREFIXES']['sdv1'],
            'sparql_endpoint': get_virtuoso_endpoint(),
            'archive_item': archive_item,
            'output_filename': output_filename,
            'mastergraph_host': settings.TRIPLE_DATABASE_MASTER['HOST'],
            'mastergraph_port':
            settings.TRIPLE_DATABASE_MASTER['KWARGS']['rexpro_port'],
            'mastergraph_graphname':
            settings.TRIPLE_DATABASE_MASTER['KWARGS']['graph'],
            'resource_namespace':
            settings.TRIPLE_DATABASE_MASTER['PREFIXES']['sdres'],
        }

        tree = ET.fromstring(render_to_string(
            'controller/aggregator/silk_rules.xml', context
        ))

        self.assertIn(
            (settings.TRIPLE_DATABASE['PREFIXES']['sdv1'], 'sd'),
            [(x.get('namespace'), x.get('id'))
             for x in tree.findall('.//Prefix')]
        )

        # check datasources
        datasources_dom = tree.findall('.//DataSource')
        self.assertEqual(len(datasources_dom), 2)
        self.assertEqual(datasources_dom[0].get('id'), 'master-graph')

        mastergraph, datasource = datasources_dom

        # check datasource endpoints
        self.assertEqual(
            get_virtuoso_endpoint(),
            datasource.find('Param[@name="endpointURI"]').get("value"),
        )

        # check datasources graph names
        self.assertEqual(
            mastergraph.find('Param[@name="graph"]').get('value'),
            settings.TRIPLE_DATABASE_MASTER["KWARGS"]["graph"]
        )
        self.assertEqual(
            archive_item.datagraph_mapped_name,
            datasource.find('Param[@name="graph"]').get("value")
        )

        # check tasks
        datasource_id = datasource.get('id')
        rules = tree.findall('.//Interlink')
        self.assertEqual(len(rules), 1)
        self.assertEqual(datasource_id, rules[0].get('id'))

        # check rules parameters
        rule = rules[0]
        self.assertEqual(
            rule.find('.//SourceDataset').get('dataSource'),
            datasource_id
        )
        self.assertEqual(
            rule.find('.//TargetDataset').get('dataSource'),
            'master-graph'
        )
        self.assertEqual(
            ET.tostring(rule.find('.//LinkageRule')).strip(),
            self.aggregator.silk_rule
        )
        self.assertEqual(
            rule.find('.//SourceDataset').find('RestrictTo').text.strip(),
            '?a rdf:type <{}> .'.format(self.aggregator.entity_type)
        )
        self.assertEqual(
            rule.find('.//TargetDataset').find('RestrictTo').text.strip(),
            'b -> {}'.format(self.aggregator.vertex_selector)
        )
        self.assertIsNone(rule.find('.//Filter').text)

        output = rule.find('.//Outputs').find('Output')
        self.assertEqual(output.get('type'), 'file')
        self.assertEqual(output.findall('Param')[0].get('name'), 'file')
        self.assertEqual(
            output.findall('Param')[0].get('value'), output_filename)
        self.assertEqual(output.findall('Param')[1].get('name'), 'format')
        self.assertEqual(output.findall('Param')[1].get('value'), 'ntriples')


class ProcessAggregatorTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        from webui.cnmain.utils import get_virtuoso
        cls.virtuoso = get_virtuoso()
        cls.virtuoso_master = get_virtuoso('master')

    @classmethod
    def tearDownClass(cls):
        cls.virtuoso.clear_regex(
            settings.TRIPLE_DATABASE['PREFIXES']['graph']
        )
        cls.virtuoso_master.clear_regex(
            settings.TRIPLE_DATABASE['PREFIXES']['data_graph_mapped']
        )

    def setUp(self):
        self.virtuoso.clear_regex(
            settings.TRIPLE_DATABASE['PREFIXES']['graph']
        )
        self.virtuoso_master.clear_regex(
            settings.TRIPLE_DATABASE['PREFIXES']['data_graph_mapped']
        )
        self.aggregator = Aggregator.objects.get(name='BoardGames')

        self.bgg_archiveitem = ArchiveItem.objects.get(
            file_target='boardgamegeek.csv')
        self.virtuoso.ingest(
            self._get_test_file('boardgamegeek-games-mapped.nt', 'scheduler'),
            graph=self.bgg_archiveitem.datagraph_mapped_name
        )

        self.bgt_archiveitem = ArchiveItem.objects.get(
            file_target='boardgametournament.csv')
        self.virtuoso.ingest(
            self._get_test_file(
                'boardgametournament-games-mapped.nt', 'scheduler'),
            graph=self.bgt_archiveitem.datagraph_mapped_name
        )

    @staticmethod
    def _contract_from_namespaces(uri):
        prefixes = settings.TRIPLE_DATABASE_MASTER["KWARGS"]["prefixes"]
        for prefix, val in prefixes.iteritems():
            if uri.startswith(val):
                return prefix + ":" + uri[len(val):]
        return uri

    @staticmethod
    def _assertTitanTriple(sparql_triple, titan_vertices):
        from sparql import Literal
        subj = ProcessAggregatorTestCase._contract_from_namespaces(
            sparql_triple[0].value
        )
        pred = ProcessAggregatorTestCase._contract_from_namespaces(
            sparql_triple[1].value
        )
        obj = sparql_triple[2]
        for vert in titan_vertices:
            if vert.get('sd:acheneID') == subj:
                if isinstance(obj, Literal) and vert.get(pred) == obj.value:
                    return
                obj = ProcessAggregatorTestCase._contract_from_namespaces(obj)
                if vert.outV(pred).name == obj:
                    return

                assert False, "Could not find {}.{} = {} on any vertex".format(
                    subj, pred, obj
                )
        assert "Could not find any vertex like ", subj

    def test_data_copied_if_rule_missing(self):
        Scheduler.objects.all().delete()
        self.aggregator.silk_rule = ''
        self.aggregator.save()

        process_aggregator.delay(self.aggregator, force=True)
        self.assertEqual(Scheduler.objects.count(), 1)
        scheduler = Scheduler.objects.get()
        self.assertEqual(
            scheduler.status, Scheduler.INCOMPLETE, scheduler.error)

        for archive_item in self.aggregator.archiveitems.all():
            graph_name = archive_item.datagraph_mapped_name
            query_a = "SELECT * WHERE {GRAPH <%s> {?a ?b ?c}}" \
                      "ORDER BY ?a ?b ?c" % graph_name
            query_b = "g.V('name', 'gt:{}').in('source')".format(
                archive_item.tablename
            )

            result_a = list(self.virtuoso.client_query(query_a).fetchall())
            result_b = list(self.virtuoso_master.client_query(query_b))

            self.assertEqual(len(result_a), 20)
            self.assertEqual(len(result_b), 4)
            for elem_a in result_a:
                self._assertTitanTriple(elem_a, result_b)

    @skip("We're not dropping the mastergraph anymore...")
    def test_master_namedgraph_is_dropped_before_add(self):
        self.virtuoso.clear(self.bgg_archiveitem.datagraph_mapped_name)
        self.virtuoso_master.ingest(
            self._get_test_file('boardgamegeek-games-mapped.nt', 'scheduler'),
            graph=self.bgg_archiveitem.datagraph_mapped_name
        )
        self.virtuoso.ingest(
            self._get_test_file('boardgamegeek-games-mapped-cropped.nt',
                                'scheduler'),
            graph=self.bgg_archiveitem.datagraph_mapped_name
        )

        Scheduler.objects.all().delete()
        self.aggregator.silk_rule = ''
        self.aggregator.save()

        process_aggregator.delay(self.aggregator, force=True)
        self.assertEqual(Scheduler.objects.count(), 1)
        scheduler = Scheduler.objects.get()
        self.assertEqual(
            scheduler.status, Scheduler.INCOMPLETE, scheduler.error)

        archive_item = self.bgg_archiveitem
        graph_name = archive_item.datagraph_mapped_name
        query_a = "SELECT * WHERE {GRAPH <%s> {?a ?b ?c}}" \
                  "ORDER BY ?a ?b ?c" % graph_name
        query_b = "g.V('name', 'gt:{}').in('source')".format(
            archive_item.tablename
        )

        result_a = list(self.virtuoso.client_query(query_a).fetchall())
        result_b = list(self.virtuoso_master.client_query(query_b))

        self.assertEqual(len(result_a), 10)
        self.assertEqual(len(result_b), 2)
        for elem_a in result_a:
            self._assertTitanTriple(elem_a, result_b)

    def test_silk_executed_correctly(self):
        Scheduler.objects.all().delete()

        self.assertEqual(
            self.virtuoso_master.graph.gremlin.command(
                "g.V('type', '{0}').out('bristle').count() "
                "- g.V('type', '{0}').count()".format("sd:BoardGame")
            ), 0
        )

        process_aggregator.delay(self.aggregator, force=True)
        self.assertEqual(Scheduler.objects.count(), 1)
        scheduler = Scheduler.objects.get()
        self.assertEqual(scheduler.status, Scheduler.SUCCESS, scheduler.error)

        for archive_item in self.aggregator.archiveitems.all():
            graph_name = archive_item.datagraph_mapped_name
            query_a = "SELECT * WHERE {GRAPH <%s> {?a ?b ?c}}" \
                      "ORDER BY ?a ?b ?c" % graph_name
            query_b = "g.V('name', 'gt:{}').in('source')".format(
                archive_item.tablename
            )

            result_a = list(self.virtuoso.client_query(query_a).fetchall())
            result_b = list(self.virtuoso_master.client_query(query_b))

            self.assertEqual(len(result_a), 20)
            self.assertEqual(len(result_b), 4)
            for elem_a in result_a:
                self._assertTitanTriple(elem_a, result_b)

        self.assertEqual(
            self.virtuoso_master.graph.gremlin.command(
                "g.V('type', '{0}').out('bristle').count() "
                "- g.V('type', '{0}').count()".format("sd:BoardGame")
            ), 2
        )

        self.assertEqual(
            len({
                x.eid for x in self.virtuoso_master.client_query(
                    "g.V('sd:name', 'Dominion').in('bristle')"
                )
                }), 1
        )


class ProcessAggregatorArchiveItemExecutionTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        from webui.cnmain.utils import get_virtuoso
        cls.virtuoso = get_virtuoso()
        cls.virtuoso_master = get_virtuoso('master')

    @classmethod
    def tearDownClass(cls):
        cls.virtuoso.clear_regex(
            settings.TRIPLE_DATABASE['PREFIXES']['graph']
        )
        cls.virtuoso_master.clear_regex(
            settings.TRIPLE_DATABASE['PREFIXES']['data_graph_mapped']
        )

    def setUp(self):
        self.virtuoso.clear_regex(
            settings.TRIPLE_DATABASE['PREFIXES']['graph']
        )
        self.virtuoso_master.clear_regex(
            settings.TRIPLE_DATABASE['PREFIXES']['data_graph_mapped']
        )
        self.aggregator = Aggregator.objects.get(name='BoardGames')

        # remove the silk rule, to speed things up
        self.aggregator.silk_rule = ''
        self.aggregator.save()

        # create fake Dataset Schedulers (needed by aggregators)
        for archiveitem in self.aggregator.archiveitems.all():
            dataset = archiveitem.dataset
            SchedulerFactory(
                content_object=dataset
            )

    def test_archiveitems_are_not_executed_again_if_not_forced(self):
        process_aggregator.delay(self.aggregator)

        with patch('webui.scheduler.tasks._aggregator_process_archiveitems') \
                as process_archiveitems:
            process_aggregator.delay(self.aggregator, force=False)
            archiveitems = tuple(process_archiveitems.call_args[0][0])

        self.assertEqual(len(archiveitems), 0)

    def test_archiveitems_are_executed_again_if_forced(self):
        process_aggregator.delay(self.aggregator)

        with patch('webui.scheduler.tasks._aggregator_process_archiveitems') \
                as process_archiveitems:
            process_aggregator.delay(self.aggregator, force=True)
            archiveitems = tuple(process_archiveitems.call_args[0][0])

        self.assertEqual(len(archiveitems), 2)

    def test_archiveitems_are_executed_again_if_they_change(self):
        process_aggregator.delay(self.aggregator)

        # create fake Schedulers (needed by aggregators)
        for archiveitem in self.aggregator.archiveitems.all()[:1]:
            dataset = archiveitem.dataset
            SchedulerFactory(
                content_object=dataset
            )

        with patch('webui.scheduler.tasks._aggregator_process_archiveitems') \
                as process_archiveitems:
            process_aggregator.delay(self.aggregator, force=False)
            archiveitems = tuple(process_archiveitems.call_args[0][0])

        self.assertEqual(len(archiveitems), 1)
        self.assertEqual(archiveitems[0].pk, archiveitem.pk)

    def test_archiveitems_are_executed_in_right_order(self):
        from datetime import datetime, timedelta

        aai1, aai2 = self.aggregator.aggregatorarchiveitem_set.all()
        aai1.first_workflow_success = datetime.utcnow() - timedelta(hours=1)
        aai2.first_workflow_success = datetime.utcnow()
        aai1.save()
        aai2.save()

        with patch('webui.scheduler.tasks._aggregator_process_archiveitems') \
                as process_archiveitems:
            process_aggregator.delay(self.aggregator, force=False)
            archiveitems = tuple(process_archiveitems.call_args[0][0])

        self.assertEqual(len(archiveitems), 2)
        self.assertEqual(archiveitems[0].pk, aai1.archiveitem.pk)
        self.assertEqual(archiveitems[1].pk, aai2.archiveitem.pk)

        # double check this: execute again in reverse order

        aai1.first_workflow_success = datetime.utcnow()
        aai2.first_workflow_success = datetime.utcnow() - timedelta(hours=1)
        aai1.save()
        aai2.save()

        with patch('webui.scheduler.tasks._aggregator_process_archiveitems') \
                as process_archiveitems:
            process_aggregator.delay(self.aggregator, force=False)
            archiveitems = tuple(process_archiveitems.call_args[0][0])

        self.assertEqual(len(archiveitems), 2)
        self.assertEqual(archiveitems[0].pk, aai2.archiveitem.pk)
        self.assertEqual(archiveitems[1].pk, aai1.archiveitem.pk)
