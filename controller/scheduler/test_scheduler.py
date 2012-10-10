import os
import sys
from nose.plugins.attrib import attr

sys.path.append(os.path.dirname(__file__) + '/../' )
os.environ['DJANGO_SETTINGS_MODULE'] = 'webui.settings'

from webui.settings import TMP_DIR, DATABASES

import scheduler
import unittest
import tempfile

from util import AttrDict
from webui.controller.models import Dataset, Rule, Source
from mock import MagicMock, patch


class TestScheduler(unittest.TestCase):
	"""Test suite for scheduler.py ."""
	def __init__(self, *s, **k):
		super(TestScheduler, self).__init__(*s, **k)
		self.testtmp = tempfile.mkdtemp(prefix= __file__)
	
	def __del__(self):
		os.rmdir(self.testtmp)
		super(TestScheduler, self).__del__()

	@attr('online')
	def test_download_url_1(self):
		out = None
		for msg in scheduler._download_url(
			'http://www.dati.piemonte.it/index.php?option=com_rd&view=scarica&urlscarico=http%3A%2F%2Fwin.comune.corio.to.it%2FOrarioBus.pdf&idallegato=427', self.testtmp
		):
			if type(msg) == dict: out = msg
			print msg
		self.assertEqual(
				{
				'file_name'   : 'OrarioBus.pdf',
				'magic_type'  : 'application/pdf',
				'md5sum'      : '2f07397a9f9a0c80458f7ba297c255b5',
				'out_file'    : self.testtmp + '/OrarioBus.pdf',
				'content_type': 'application/pdf',
				'file_size'   : 558529
			},
			out
		)

	@attr('online')
	def test_download_url_2(self):
		out = None
		for msg in scheduler._download_url(
			'http://www.territorio.provincia.tn.it/geodati/847_Aree_di_pertinenza_dei_fiumi_principali_12_12_2011.zip', self.testtmp
		):
			if type(msg) == dict: out = msg
			print msg
		self.assertEqual(
			{
				'file_name'   : '847_Aree_di_pertinenza_dei_fiumi_principali_12_12_2011.zip',
				'out_file'    : self.testtmp + '/847_Aree_di_pertinenza_dei_fiumi_principali_12_12_2011.zip',
				'content_type': 'application/zip',
				'file_size'   : 911127,
				'magic_type'  : 'archive/zip',
				'md5sum'      : '22a0669fef775932c5c16f29cab9afcd',
			},
			out
		)

	def test_evaluate_init_handler(self):
		source = AttrDict()
		source.name            = 'source name'
		source.description     = 'source desc'
		source.tags            = 't1,t2,t3'
		source.user            = 'user1'
		source.scraper_name    = 'a_fake_scraper'
		source.init_handler    = 'return ("init-wf", {"k1" : "v1"})'
		source.dispose_handler = None

		scheduler._run_workflow_from_handler = MagicMock()

		scheduler._process_init_handler(source)

		scheduler._run_workflow_from_handler.assert_called_once_with( ("init-wf", {"k1" : "v1"}) )

	def test_evaluate_dispose_handler(self):
		source = AttrDict()
		source.name            = 'source name'
		source.description     = 'source desc'
		source.tags            = 't1,t2,t3'
		source.user            = 'user1'
		source.scraper_name    = 'a_fake_scraper'
		source.init_handler    = None
		source.dispose_handler = 'return ("dispose-wf", {"k1" : "v1"})'

		scheduler._run_workflow_from_handler = MagicMock()

		scheduler._process_dispose_handler(
			source,
			{'processed_dataset_count' : 1, 'failed_dataset_count' : 2}
		)

		scheduler._run_workflow_from_handler.assert_called_once_with( ("dispose-wf", {"k1" : "v1"}) )

	def test_evaluate_dispatcher(self):
		source = AttrDict()
		source.name         = 'source name'
		source.description  = 'source desc'
		source.tags         = 't1,t2,t3'
		source.user         = 'user1'
		source.scraper_name = 'a_fake_scraper'
		source.dispatcher   = " return ( 'conf', { 'source_name' : source.name, 'source_description' : source.description, 'dataset_url' : dataset.url, 'dataset_name' : dataset.name, 'dataset_file' : dataset.file, 'dataset_license' : dataset.license } ) "

		dataset = AttrDict()
		dataset.download = 'http://path/to/download'
		dataset.url      = 'http://dataset/url'
		dataset.name     = 'dataset a'
		dataset.curator  = 'curator x'
		dataset.license  = 'license 0'

		evaluation = scheduler._evaluate_dispatcher(
			source, dataset,
			{
				'file_name'    : 'target.csv',
				'file_size'    : 1234,
				'out_file'     : '/path/to/target.csv',
				'content_type' : 'text/css'
			}
		)
		print repr(evaluation)
		self.assertEqual(
			('conf', {'dataset_url': 'http://dataset/url', 'dataset_file': '/path/to/target.csv', 'source_description': 'source desc', 'dataset_license': 'license 0', 'source_name': 'source name', 'dataset_name': 'dataset a'}),
			evaluation
		)

	@attr('online')
	def test_download_and_run_workflow(self):
		source = AttrDict()
		source.name            = 'Portale Piemonte'
		source.description     = 'Portale Piemonte Open Data'
		source.tags            = 'portale,piemonte'
		source.user            = 'youruser'
		source.scraper_name    = 'portale_piemonte_scraper'
		source.scraper_api_key = 'yourkey'
		source.dispatcher      = """raise UnsupportedDatasetException('')"""

		dataset = AttrDict()
		dataset.url      = 'http://www.dati.piemonte.it/component/rd/item/100244-pubblicazioni-urp-entrate-e-uscite-mensili.html'
		dataset.download = 'http://www.dati.piemonte.it/media/k2/attachments/URP_entrate_uscite_pubblicazioni.csv'
		dataset.name     = 'Pubblicazioni URP - Entrate e uscite mensili'
		dataset.curator  = 'Regione Piemonte'
		dataset.license  = 'cc0'

		out = None
		try:
			for msg in scheduler._download_and_run_workflow(source, dataset):
				print msg
				if type(msg) == dict: out = msg
		except scheduler.UnsupportedDatasetException:
			pass
		if out is None: raise Exception()

		self.assertEquals(
			{
			'content_type': 'text/csv',
			'file_name'   : 'URP_entrate_uscite_pubblicazioni.csv',
			'file_size'   : 9181,
			'magic_type'  : 'text/plain',
			'md5sum'      : '2aebd545b1ba63862e84b5f307e05016',
			'out_file'    : TMP_DIR + '/Portale+Piemonte/http%3A%2F%2Fwww.dati.piemonte.it%2Fcomponent%2Frd%2Fitem%2F100244-pubblicazioni-urp-entrate-e-uscite-mensili.html/URP_entrate_uscite_pubblicazioni.csv'
			},
			out
		)

	@attr('online')
	def test_download_and_run_workflow_with_recursion(self):
		source = AttrDict()
		source.name            = 'Portale Piemonte'
		source.description     = 'Portale Piemonte Open Data'
		source.tags            = 'portale,piemonte'
		source.user            = 'youruser'
		source.scraper_name    = 'portale_piemonte_scraper'
		source.scraper_api_key = 'yourkey'
		source.dispatcher      = """
		if dataset.ext() == '.7z':
			return recurse()
		elif dataset.ext() == '.txt':
			raise UnsupportedDatasetException('Unsupported .txt extension')
		else:
			return ('tab-configuration', {'database' : DATABASES[default].NAME, 'schema' : 'test', 'data' : dataset.file})
		"""

		dataset = AttrDict()
		dataset.url      = 'http://www.dati.piemonte.it/dato/item/1232-anagrafica-esercizi-ricettivita-2009-.html'
		dataset.download = 'http://www.dati.piemonte.it/index.php?option=com_rd&view=scarica&urlscarico=http%3A%2F%2Fwww.dati.piemonte.it%2Fmedia%2Fk2%2Fattachments%2FSICEE_ace_classe_energetica_comune.7z&idallegato=338'
		dataset.name     = 'Anagrafica esercizi - Ricettivita 2009'
		dataset.curator  = 'Regione Piemonte'
		dataset.license  = 'cc0'

		rule             = AttrDict()
		rule.dataset_url = dataset
		rule.file_path   = '/ace_comune_classe.csv'
		rule.rule        = '[]'
		rule.hash        = '784e9f46467500ad6a3d31c42cb83c58'

		with patch.object(Dataset.objects, 'get', return_value=dataset) as datasets_get:
			def side_effect(*args, **kwargs):
				if(kwargs['file_path'] == rule.file_path):
					return rule
				else:
					raise Exception('Not found')
			with patch.object(Rule.objects, 'get', side_effect=side_effect) as rules_get:
				out = []
				for msg in scheduler._download_and_run_workflow(source, dataset):
					print msg
					out.append(str(msg))

				out_str = '\n'.join(out)
				print 'OUT STR: ', out_str
				self.assertTrue( "Found rule <pre>'[]'</pre> for dataset ['%s'] and file name [u'ace_comune_classe.csv']" %(dataset.name) in out_str)
				self.assertTrue( "Found rule <pre>None</pre> for dataset ['%s'] and file name [u'creative commons CC0.txt']" %(dataset.name) in out_str)

	def test_process_source(self):
		source = AttrDict()
		source.name            = 'Prodotti Protetti Trentino'
		source.description     = 'Prodotti Protetti Trentino'
		source.tags            = 'portale,trentino,prodotti'
		source.user            = 'youruser'
		source.scraper_name    = 'prodottiprotettitrentino'
		source.scraper_api_key = 'yourkey'
		source.init_handler    = None
		source.dispatcher      = """return ("test-wf", {"k1" : "v1"})"""
		source.dispose_handler = None

		dataset = AttrDict()
		dataset.url      = 'http://www.dati.piemonte.it/dato/item/1232-anagrafica-esercizi-ricettivita-2009-.html'
		dataset.download = 'http://www.dati.piemonte.it/index.php?option=com_rd&view=scarica&urlscarico=http%3A%2F%2Fwww.dati.piemonte.it%2Fmedia%2Fk2%2Fattachments%2FSICEE_ace_classe_energetica_comune.7z&idallegato=338'
		dataset.name     = 'Anagrafica esercizi - Ricettivita 2009'
		dataset.curator  = 'Regione Piemonte'
		dataset.license  = 'cc0'

		def source_side(*args, **kwargs):
			if kwargs['name'] == 'target-source': return source
			raise Exception
		with patch.object(Source.objects, 'get', side_effect=source_side) as sources_get:
			def dataset_side(*args, **kwargs):
				if len(args) == 1: return [dataset]
				raise Exception
			with patch.object(Dataset.objects, 'raw', side_effect=dataset_side) as datasets_raw:
				scheduler._download_and_run_workflow = MagicMock()

				for msg in scheduler.process_source('target-source', 0, False):
					print msg

				scheduler._download_and_run_workflow.assert_called_with(
					AttrDict({
					'name': 'Prodotti Protetti Trentino',
					'tags': 'portale,trentino,prodotti',
					'scraper_name': 'prodottiprotettitrentino',
					'init_handler': None,
					'scraper_api_key': 'yourkey',
					'user': 'youruser',
					'dispose_handler': None,
					'dispatcher': 'return ("test-wf", {"k1" : "v1"})',
					'description': 'Prodotti Protetti Trentino'
					}),
					AttrDict({
					'url': 'http://www.dati.piemonte.it/dato/item/1232-anagrafica-esercizi-ricettivita-2009-.html',
					'download': 'http://www.dati.piemonte.it/index.php?option=com_rd&view=scarica&urlscarico=http%3A%2F%2Fwww.dati.piemonte.it%2Fmedia%2Fk2%2Fattachments%2FSICEE_ace_classe_energetica_comune.7z&idallegato=338',
					'name': 'Anagrafica esercizi - Ricettivita 2009',
					'license': 'cc0',
					'curator': 'Regione Piemonte'
					})
				)

	def test_download_csv(self):
		scheduler._download_csv('prodottiprotettitrentino', '61f623f3-04ba-4c71-ba8e-acc5e88b8202', 'data', tempfile.mkdtemp())

	def test_download_url(self):
		scheduler._download_url('http://google.com', tempfile.mkdtemp())

	def test_main(self):
		self.assertEqual(1, scheduler.main(['run']) )
