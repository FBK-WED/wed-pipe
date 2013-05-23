"""
Tests for slice utils
"""

# pylint: disable=E1103,R0904,C0111,C0103,E1101,C0302,W0232,R0201,W0212
import unittest
from django.conf import settings

import simplejson as json

from webui.cnmain.utils import get_virtuoso
from webui.slice.utils import dicts2geojson, get_sliced_data, \
    clean_sliced_data, get_cleaned_sliced_data
from webui.tests import TestCase


THE_QUERY = """
def nodes() {
    m = []
    g.V('type', 'sd:BoardGame').filter{!!it['sd:acheneID']}[0..100].id.fill(m)
    return m
}

def slice(nodes_id) {
    m = []

    nodes_id.each{node_id ->
        g.v(node_id).transform({ poi ->
            data = [acheneID: poi['sd:acheneID']]
            tmp = []
            poi.out('bristle').map.fill(tmp)

            data.name = tmp.collect{it['sd:name']}.findResults{it}[0]
            data.provenance = poi.out('bristle').out('source').name.collect{
                it}.join(',')

            return data
        }).filter{it != null}.fill(m)
    }

    return m
}
"""


class Dicts2GeoJsonTestCase(TestCase):
    def setUp(self):
        self.dicts = [
            {'foo': 'bar', 'goo': 2, 'latitude': 10.31, 'longitude': 40.42},
            {'foo': 'bar', 'goo': 2, 'geometry': 'POINT (7.42 45.123)'},
            {'foo': 'bar', 'goo': 2, 'geometry':
             'POLYGON ((7.4 45, 13 42.42, 14 42.42, 7.4 45))'},
        ]

    def _get_test_data(self):
        return ''.join(dicts2geojson(self.dicts))

    def test_contains_crs(self):
        geojson = self._get_test_data()

        data = json.loads(geojson)
        crs = data['crs']
        self.assertEqual(crs['type'], 'name')
        self.assertEqual(crs['properties']['name'],
                         'urn:ogc:def:crs:EPSG::4326')

    def test_contains_features(self):
        geojson = self._get_test_data()

        data = json.loads(geojson)
        features = data['features']
        self.assertEqual(len(features), 3)

    def test_features_are_in_good_format(self):
        geojson = self._get_test_data()

        data = json.loads(geojson)
        feature = data['features'][0]
        self.assertEqual(
            feature['properties'],
            {
                'foo': 'bar',
                'goo': 2,
            }
        )

    def test_geometries_are_in_good_format(self):
        geojson = self._get_test_data()

        data = json.loads(geojson)
        features = data['features']

        for feature in features:
            self.assertIsInstance(feature['geometry'], dict)
            self.assertIn("type", feature['geometry'])
            self.assertIn("coordinates", feature['geometry'])
            self.assertIsInstance(feature['geometry']['coordinates'], list)
            self.assertEqual(len(feature['geometry']), 2)

        self.assertIsInstance(features[0]['geometry']['coordinates'][0], float)
        self.assertEqual(features[0]['geometry']['type'], "Point")
        self.assertIsInstance(features[2]['geometry']['coordinates'][0], list)
        self.assertEqual(features[2]['geometry']['type'], "Polygon")


class GetSlicedDataTestCase(TestCase):
    def test_query_malformed(self):
        with self.assertRaises(ValueError):
            next(get_sliced_data(
                "this is a terribly wrong query",
                fields='acheneID,provenance',
            ))

    @unittest.skip('Does not fail, we have data in graphs')
    def test_query_no_resource(self):
        with self.assertRaises(ValueError):
            next(get_sliced_data(
                "SELECT DISTINCT ?g WHERE {GRAPH ?g {?a ?b ?c}}",
                fields='acheneID,provenance',
            ))

    def test_query_ok(self):
        graph_pref = settings.TRIPLE_DATABASE['PREFIXES']['data_graph_mapped']
        get_virtuoso('master').ingest(
            self._get_test_file('boardgamegeek-games-mapped.nt', 'scheduler'),
            graph=graph_pref + 'test_graph'
        )

        results = get_cleaned_sliced_data(
            query=THE_QUERY,
            fields='acheneID,provenance',
            with_header=True
        )
        header = next(results)
        self.assertIsInstance(header, list)
        self.assertGreater(len(list(results)), 0)

        results = get_sliced_data(
            query=THE_QUERY,
            fields='acheneID,provenance',
            with_header=False
        )
        results = list(results)
        self.assertIsInstance(results[0], dict)


class CleanSlicedDataTestCase(TestCase):
    def assertGeneratorDictEqual(self, gen1, gen2):
        for i, dict1 in enumerate(gen1):
            dict2 = next(gen2)

            self.assertEqual(sorted(dict1.keys()), sorted(dict2.keys()),
                             'Dictionaries with index {} differ'.format(i))

            for k in dict1:
                self.assertEqual(dict1[k], dict2[k])
        with self.assertRaises(StopIteration):
            next(gen2)

    def test_clean_replaces_resource(self):
        data = [{
            'acheneID': 'blahblah',
            'name': "I'm a resource!",
            'provenance': 'Venturi Partner',
        }]
        result = list(clean_sliced_data(data, data[0].keys()))[0]

        self.assertEqual(
            result['acheneID'],
            'http://dandelion.eu/resource/blahblah'
        )
        self.assertEqual(result['name'], data[0]['name'])

    def test_clean_sets_category(self):
        from django.conf import settings
        data = [{
            'acheneID': 'blahblah',
            'category': None,
            'provenance': 'Venturi Partner',
        }]
        result = list(clean_sliced_data(data, data[0].keys()))[0]

        self.assertEqual(
            result['category'],
            settings.DM_CATEGORY_BASE_PREFIX + 'POI/v1#POI'
        )

    @unittest.skip('Does not splits data anymore...')
    def test_clean_separates_results(self):
        data = [{
            'acheneID': 'blahblah',
            'description': 'description one~|~description two',
            'provenance': 'Venturi Partner',
        }]
        result = list(clean_sliced_data(data, data[0].keys()))[0]
        self.assertEqual(
            result['description'],
            'description one'
        )
