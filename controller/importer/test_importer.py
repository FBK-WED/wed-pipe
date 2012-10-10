import unittest
import cStringIO

from importer import MetadataImporter

from mock import MagicMock, patch
from webui.controller.models import Dataset, Source

class TestImporter(unittest.TestCase):
	"""Test suite for importer.py module."""

	def test_read_metadata(self):
		importer = MetadataImporter()
		with patch.object(Dataset, 'save') as fake_save:
			def side_fun(*args, **kwargs):
				return Source()
			with patch.object(Source.objects, 'get', side_effect=side_fun) as fake_source_get:
				self.assertEqual(
					{ 'total' : 1, 'errors' : 0, 'report' : [] },
					importer.read_metadata('fake_source', 'prodottiprotettitrentino', '61f623f3-04ba-4c71-ba8e-acc5e88b8202')
				)

	def test_read_csv(self):
		importer = MetadataImporter()
		with patch.object(Dataset, 'save') as fake_save:
			def side_fun(*args, **kwargs):
				return Source()
			with patch.object(Source.objects, 'get', side_effect=side_fun) as fake_source_get:
				csv_stream = cStringIO.StringIO(
"""
http://path.to/url/1\thttp://path.to/download/1\tName 1\tDesc 1\tt11,t12\tCurator Name 1\tLic 1\t1,2,3,4\t{"k11":"v11"}\n
http://path.to/url/2\thttp://path.to/download/2\tName 2\tDesc 2\tt21,t22\tCurator Name 2\tLic 2\t5,6,7,8\t{"k12":"v12"}\n
"""
				)
				self.assertEqual(
					{ 'total' : 2, 'errors' : 0, 'report' : [] },
					importer.read_csv('fake_source', csv_stream)
				)