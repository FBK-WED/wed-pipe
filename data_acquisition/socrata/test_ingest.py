from socrata.ingest import SocrataPostGresImporter

__author__ = 'micmos'

import unittest
import json

class SocrataImporterTestCase(unittest.TestCase):

	def setUp(self):
		conf = {
			'api' : {
				'host'   : 'https://dati.lombardia.it',
				'user'   : 'mostarda@fbk.eu',
				'passwd' : 'socratasimplepassword',
				'token'  : 'UKlVPco0dv3ik0NDhpLsP7NsY'
			},
			'database' : {'db' : 'venturi.fbk-test', 'schema' : 'plo'}
		}
		self.socrata_importer = SocrataPostGresImporter(conf)

	def test_describe(self):
		self.socrata_importer.describe()

	def test_describe_json(self):
		json_meta = self.socrata_importer.describe_json()
		self.assertTrue( len(json_meta) >= 50 )

	def test_import_views(self):
		self.socrata_importer.ingest_views(limit=2)

	def test_ingest_view_from_url(self):
		self.socrata_importer.ingest_view_from_url('https://dati.lombardia.it/api/views/xy9p-k9bj.json')

if __name__ == '__main__':
	unittest.main()
