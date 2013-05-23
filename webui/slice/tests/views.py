"""
Tests for slice views
"""

# pylint: disable=E1103,R0904,C0111,C0103,E1101,C0302,W0232,R0201,W0212
import unittest

import simplejson as json

from django.conf import settings

from webui.slice.models import Slicer
from webui.slice.models.factories import SlicerFactory
from webui.tests import TestCase


class SlicerListViewTest(TestCase):
    def setUp(self):
        self.slicer = SlicerFactory()

    def test_get(self):
        response = self.client.get('/l/slicer/')
        self.assertContains(response, 'Slicer list')
        self.assertNotContains(
            response, settings.TEMPLATE_STRING_IF_INVALID_TEST
        )

    def test_contains_links(self):
        response = self.client.get('/l/slicer/')
        self.assertContains(response, '/l/slicer/create/')
        for slicer in Slicer.objects.all():
            self.assertContains(response, slicer.name)
            self.assertContains(response, slicer.get_absolute_url())


class SlicerCreateViewTest(TestCase):
    def setUp(self):
        self.create_url = '/l/slicer/create/'
        self.post_data = dict(SlicerFactory.attributes())

    def test_post(self):
        Slicer.objects.all().delete()
        response = self.client.post(self.create_url, data=self.post_data)

        self.assertEqual(response.status_code, 302)
        slicer = Slicer.objects.get()
        self.assertEqual(slicer.name, self.post_data['name'])
        self.assertEqual(slicer.query_string, self.post_data['query_string'])


class SlicerUpdateViewTest(TestCase):
    def setUp(self):
        self.slicer = SlicerFactory()
        self.update_url = self.slicer.get_absolute_url()
        self.post_data = dict(SlicerFactory.attributes())

    def test_get(self):
        response = self.client.get(self.update_url)
        self.assertContains(response, self.slicer.name)
        self.assertContains(response, self.slicer.query_string)
        self.assertContains(response, "Run Query")

    def test_post(self):
        response = self.client.post(self.update_url, data=self.post_data)
        self.assertRedirects(response, self.slicer.get_absolute_url())

        slicer = Slicer.objects.get(pk=self.slicer.pk)
        self.assertEqual(slicer.name, self.post_data['name'])
        self.assertEqual(slicer.query_string, self.post_data['query_string'])


class SlicerQueryViewTest(TestCase):
    def _test_query(self, query):
        url = '/l/slicer/query/'
        response = self.client.post(
            url,
            data={'query': query, 'fields': 'acheneID, provenance'})
        return response

    def test_query_malformed(self):
        response = self._test_query("this is a terribly wrong query")
        self.assertEqual(response.status_code, 400)

    def test_query_no_results(self):
        response = self._test_query(
            """
def nodes() {
    return []
}

def slice(nodes_id) {
    return []
}
            """
        )
        self.assertEqual(response.status_code, 400)

    @unittest.skip('We have data in graphs')
    def test_query_no_resource(self):
        response = self._test_query(
            "SELECT DISTINCT ?g WHERE {GRAPH ?g {?a ?b ?c}}"
        )
        self.assertEqual(response.status_code, 400)

    def test_query_ok(self):
        from webui.cnmain.utils import get_virtuoso

        graph_pref = settings.TRIPLE_DATABASE['PREFIXES']['data_graph_mapped']
        get_virtuoso('master').ingest(
            self._get_test_file('boardgamegeek-games-mapped.nt', 'scheduler'),
            graph=graph_pref + 'test_graph'
        )

        response = self._test_query("""
def nodes() {
    return g.V('type', 'sd:BoardGame').id.collect{it}
}

def slice(nodes_id) {
    m = []
    nodes_id.each{ node_id ->
        g.v(node_id).transform{ node ->
            data = [acheneID: node['sd:acheneID']]
            data.provenance = node.out('bristle').out('source').name.collect{
                it}.join(',')

            return data
        }.fill(m)
    }
    return m
}
        """)

        self.assertEqual(response.status_code, 200)


class SlicerDumpViewTestCase(TestCase):
    def setUp(self):
        self.slicer = SlicerFactory(
            query_string="""
def nodes() {
    m = []
    g.V('type', 'sd:POI').filter{!!it['sd:acheneID']}[0..100].id.fill(m)
    return m
}

def slice(nodes_id) {
    m = []

    nodes_id.each{node_id ->
        g.v(node_id).transform({ poi ->
            data = [acheneID: poi['sd:acheneID']]

            tmp = []
            poi.out('bristle').order{
                -1 * (it.a.created <=> it.b.created)
            }.map.fill(tmp)

            data.name = tmp.collect{it['sd:name']}.findResults{it}[0]
            data.latitude = tmp.collect{it['sd:latitude']}?.findResults{it}[0]
            data.longitude = tmp.collect{
                it['sd:longitude']
            }?.findResults{it}[0]
            data.provenance = poi.out('bristle').out('source').name.collect{
                it}.join(',')

            if ([data.latitude, data.longitude].any{it == null}) {
                return null
            }

            return data
        }).filter{it != null}.fill(m)
    }

    return m
}
            """
        )

    def test_does_not_crash(self):
        from webui.controller.models import Aggregator, Source
        from webui.scheduler.tasks import process_aggregator, process_source

        osm_source = Source.objects.get(name='OSM (test)')
        process_source.delay(osm_source)

        poi_aggregator = Aggregator.objects.get(name='POI')
        process_aggregator.delay(poi_aggregator)

        response = self.client.get('/l/slicer/{}/dump/'.format(self.slicer.pk))
        self.assertEqual(response.status_code, 200)

        data = json.loads(''.join(response.streaming_content))

        self.assertEqual(len(data['features']), 10)
