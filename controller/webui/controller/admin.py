"""
Defines custom ModelAdmin implementations for models.
"""

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect

from webui.controller.models import Source, Dataset, Scheduler, Rule
from importer.importer       import MetadataImporter
from scheduler.scheduler     import SchedulerRunner

import urllib
import sys, traceback

# See https://docs.djangoproject.com/en/1.2/ref/contrib/admin/actions/

def update_metadata(modeladmin, request, queryset):
	importer = MetadataImporter()
	source_reports = []
	try:
		for source in queryset:
			if source.scraper_name is None: raise Exception('A scraper name must be specified.')
			if source.scraper_api_key is None: raise Exception('A scraper API Key must be specified.')
			api_key = source.scraper_api_key.strip()
			report  = importer.read_metadata(source.name, source.scraper_name, api_key if len(api_key) > 0 else None)
			source_reports.append(report)
		messages.info(request, 'Report: ' + repr(source_reports))
	except Exception as e:
		traceback.print_exc(file=sys.stderr)
		messages.error(request, "Error while updating metadata: " + repr(e))
update_metadata.short_description = "Import selected source metadata"

def run_acquisition_live(modeladmin, request, queryset):
	"""Runs the acquisition live of the selected source via console."""
	if len(queryset) > 1: raise Exception('You can select just one source per time.')
	source = queryset[0]
	return HttpResponseRedirect( '/console?acquisitionlive=%s' % urllib.quote_plus(source.name) )
run_acquisition_live.short_description = "Run acquisition live for selected source"

def run_acquisition_job(modeladmin, request, queryset):
	"""Runs the acquisition live of the selected source via console."""
	if len(queryset) > 1: raise Exception('You can select just one source per time.')
	source = queryset[0]
	return HttpResponseRedirect( '/console?acquisitionjob=%s' % urllib.quote_plus(source.name) )
run_acquisition_live.short_description = "Run acquisition job for selected source"

def perform_acquisition(modeladmin, request, queryset):
	for dataset in queryset:
		try:
			runner = SchedulerRunner()
			out = []
			for msg in runner.process_dataset(dataset):
				out.append(msg)
			messages.info(request, 'Acquisition completed.' + u''.join(out))
		except Exception:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			formatted_exc = u'\n'.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
			messages.error(
				request,
				"Error while performing selective acquisition:<br/><pre>%s</pre> <strong>Full output was</strong>: <pre>%s</pre>" %
				(formatted_exc, u''.join(out)),
				extra_tags='safe'
			)

def reprocess_scheduler(model, request, queryset):
	for scheduler in queryset:
		try:
			runner = SchedulerRunner()
			out = []
			dataset = Dataset.objects.get( download=scheduler.url.download ) # TODO: this must become download = scheduler.download
			source  = Source.objects.get( name=dataset.source.name )
			for msg in runner.process_dataset(dataset, source):
				out.append(msg)
			messages.info(request, u'Reprocess completed.<br/><pre>%s</pre>' % u'\n'.join(out))
		except Exception:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			formatted_exc = u'\n'.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
			messages.error(
				request,
				"Error while reprocessing scheduler:<br/><pre>%s</pre>" % formatted_exc, extra_tags='safe'
			)

def manage_Refine_rules(model, request, queryset):
	if len(queryset) > 1:
		messages.error(request, 'You can open in Refine just one dataset per time.')
	else:
		for dataset in queryset:
			return HttpResponseRedirect( '/refine/inspect/%s' % urllib.quote_plus(dataset.download) )

def ext_renderer(ext):
	return '<b>%s</b>' % ext if ext is not None else '<font color="grey">No Ext</font>'

def tags_renderer(tags):
	result = []
	for tag in tags: result.append('<b>' + tag + '</b>')
	return ', '.join(sorted(result))

class SourceAdmin(admin.ModelAdmin):
	actions   = [update_metadata, run_acquisition_live, run_acquisition_job]
	fieldsets = [
		(None     , {'fields' : ['name', 'description', 'tags', 'user', 'dispatcher', 'init_handler', 'dispose_handler']}),
		('Scraper', {'fields' : ['scraper_name', 'scraper_api_key']})
	]
	list_display = ('name', 'description', 'tags_renderer', 'user')

	def tags_renderer(self, source):
		return tags_renderer(source.tag_list())
	tags_renderer.allow_tags = True
	tags_renderer.short_description = 'Tags'

class DatasetAdmin(admin.ModelAdmin):
	actions   = [perform_acquisition, manage_Refine_rules]
	fieldsets = [
		(None      , {'fields': ['source', 'url', 'update_rule']}),
		('Metadata', {'fields': ['download', 'name', 'description', 'tags' ,'curator', 'license', 'bounding_box', 'other_meta']}),
	]
	list_display = ('name', 'source', 'tags_renderer', 'license', 'ext_renderer')
	list_filter    = ['source', 'license']

	def ext_renderer(self, dataset):
		return ext_renderer( dataset.ext() )
	ext_renderer.allow_tags = True
	ext_renderer.short_description = 'Ext'

	def tags_renderer(self, dataset):
		return tags_renderer(dataset.tag_list())
	tags_renderer.allow_tags = True
	tags_renderer.short_description = 'Tags'

class SchedulerAdmin(admin.ModelAdmin):
	actions   = [reprocess_scheduler]
	list_display   = ('dataset', 'source', 'ext_renderer', 'last_execution', 'status_renderer')
	list_filter    = ['last_execution', 'status']
	date_hierarchy = 'last_execution'

	def ext_renderer(self, scheduler):
		return ext_renderer( scheduler.ext() )
	ext_renderer.allow_tags = True
	ext_renderer.short_description = 'Ext'

	def status_renderer(self, scheduler):
		if scheduler.status == 'S':
			return """<font color="green">Success</font>"""
		elif scheduler.status == 'F':
			return """<font color="red">Fail</font>"""
		elif scheduler.status == 'I':
			return """<font color="yellow">Invalid</font>"""
		elif scheduler.status == 'R':
			return """<font color="orange">Running</font>"""
		else:
			return """<pre>%s ?</pre>""" % scheduler.status
	status_renderer.allow_tags = True
	status_renderer.short_description = 'Status'

class RuleAdmin(admin.ModelAdmin):
	list_display = ('dataset_url', 'file_path', 'hash' )

admin.site.register(Source   , SourceAdmin)
admin.site.register(Dataset  , DatasetAdmin)
admin.site.register(Scheduler, SchedulerAdmin)
admin.site.register(Rule     , RuleAdmin)
