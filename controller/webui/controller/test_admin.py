import unittest
from django.contrib import messages
from mock import MagicMock, patch
from importer.importer import MetadataImporter
from scheduler.scheduler import SchedulerRunner
from webui.controller.admin import update_metadata, tags_renderer, SchedulerAdmin, perform_acquisition
from webui.controller.models import Scheduler

class TestAdmin(unittest.TestCase):

	def test_update_metadata_success(self):
		modeladmin = MagicMock()
		request    = MagicMock()
		query      = MagicMock()
		query.name = 'test-source'
		query.scraper_name    = 'prodottiprotettitrentino'
		query.scraper_api_key = '61f623f3-04ba-4c71-ba8e-acc5e88b8202'
		queryset = [query]

		MetadataImporter.read_metadata = MagicMock(return_value={'status': 'ok'})
		with patch.object(messages, 'info') as messages_info:
			update_metadata(modeladmin, request, queryset)
			MetadataImporter.read_metadata.assert_called_once_with('test-source', 'prodottiprotettitrentino', '61f623f3-04ba-4c71-ba8e-acc5e88b8202')
			messages_info.assert_called_once_with(request, "Report: [{'status': 'ok'}]")

	def test_update_metadata_fail(self):
		modeladmin = MagicMock()
		request    = MagicMock()
		query      = MagicMock()
		query.name = 'test-source'
		query.scraper_name = None
		queryset = [query]

		def side_fun(*args, **kwargs):
			raise Exception
		MetadataImporter.read_metadata = MagicMock(side_effect=side_fun)
		with patch.object(messages, 'error') as messages_error:
			update_metadata(modeladmin, request, queryset)
			messages_error.assert_called_once_with(request, "Error while updating metadata: Exception('A scraper name must be specified.',)")

	def test_perform_acquisition_success(self):
		modeladmin = MagicMock()
		request    = MagicMock()
		query      = MagicMock()
		query.name = 'test-source'
		query.scraper_name    = 'prodottiprotettitrentino'
		query.scraper_api_key = '61f623f3-04ba-4c71-ba8e-acc5e88b8202'
		queryset = [query]

		with patch.object(SchedulerRunner, 'process_dataset') as process_dataset:
			with patch.object(messages, 'info') as messages_info:
				perform_acquisition(modeladmin, request, queryset)
				process_dataset.assert_called_once_with(query)
				messages_info.assert_called_once_with(request, "Acquisition completed.")

	def test_perform_acquisition_fail(self):
		modeladmin = MagicMock()
		request    = MagicMock()
		query      = MagicMock()
		query.name = 'test-source'
		query.scraper_name = None
		queryset = [query]

		def side_fun(*args, **kwargs):
			raise Exception()
		with patch.object(SchedulerRunner, 'process_dataset',side_effect=side_fun) as process_dataset:
			with patch.object(messages, 'error') as messages_error:
				perform_acquisition(modeladmin, request, queryset)
				messages_error.assert_called_once()

	def test_tags_renderer(self):
		self.assertEqual('<b>t1</b>, <b>t2</b>', tags_renderer(['t1', 't2']))

	def test_SchedulerAdmin_status_renderer(self):
		scheduler = MagicMock()
		schedulerAdmin = SchedulerAdmin(Scheduler, MagicMock())
		scheduler.status = 'S'
		self.assertEqual('<font color="green">Success</font>' , schedulerAdmin.status_renderer(scheduler))
		scheduler.status = 'I'
		self.assertEqual('<font color="yellow">Invalid</font>', schedulerAdmin.status_renderer(scheduler))
		scheduler.status = 'F'
		self.assertEqual('<font color="red">Fail</font>'      , schedulerAdmin.status_renderer(scheduler))
		scheduler.status = 'R'
		self.assertEqual('<font color="orange">Running</font>', schedulerAdmin.status_renderer(scheduler))