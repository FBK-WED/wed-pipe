# pylint: disable=E1103,R0904,C0111,C0103,E1101,C0302,W0232,R0201,W0212,W0613

import cStringIO

from mock import patch

from django.utils import unittest

from webui.controller.models.factories import SourceFactory
from webui.importer.importer import MetadataImporter
from webui.controller.models import Dataset, Source


class TestImporter(unittest.TestCase):
    """Test suite for importer.py module."""

    def test_read_metadata(self):
        importer = MetadataImporter()
        source = SourceFactory(
            scraper_name='fake',
            scraperwiki_url='http://www.google.com/',
        )

        def side_metadata(*args):
            return [{
                'description': 'dati emergenza estratti da www.intoscana.it',
                'license': 'others',
                'tags': 'emergenza, carabinieri',
                'url': 'http://www.example.com/index.html',
                'curator': 'fondazione sistema toscana',
                'bounding_box': '42.24, 9.69, 44.47, 12.37',
                'other': None,
                'download': 'table://emergencies',
                'name': 'numeri di emergenza in toscana'
            }]

        with patch.object(Dataset, 'save'):
            with patch.object(MetadataImporter, 'get_metadata_of_scraper',
                              side_effect=side_metadata):
                self.assertEqual(
                    {'total': 1, 'errors': 0, 'report': []},
                    importer.read_metadata(source)
                )

    def test_read_csv(self):
        source = Source.objects.all()[0]
        csv_stream = cStringIO.StringIO(
            "url\tdownload\tname\tdescription\ttags\tcurator\tlicense\t"
            "bounding_box\tother_meta\n"
            "http://path.to/url/1\thttp://path.to/download/1\tName 1\tDesc 1\t"
            "t11,t12\tCurator Name 1\tLic 1\t1,2,3,4\t{\"k11\":\"v11\"}\n"
            "http://path.to/url/2\thttp://path.to/download/2\tName 2\tDesc 2\t"
            "t21,t22\tCurator Name 2\tLic 2\t5,6,7,8\t{\"k12\":\"v12\"}\n")

        self.assertEqual(
            {'total': 2, 'errors': 0, 'report': []},
            MetadataImporter.read_csv(source, csv_stream)
        )
