"""
Custom views and Platform API definition.
"""

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django import forms
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ValidationError
from util import decompress
from webui import settings

from webui.controller.models import Source, Dataset, Rule, CONFIG_CHOICES, get_configuration
from scheduler.scheduler import process_source, active_finalizers, download_dataset_per_source, file_meta_from_file, active_live_tasks
from importer.importer   import MetadataImporter
from google.refine       import refine
from refine.refine       import get_refine_ws, open_project_on_file_with_rules

import traceback
import json
import os


def console(request,run_scheduler_form=None, csv_upload_form=None):
	"""Returns the Controller Console UI."""
	if run_scheduler_form is None:
		run_scheduler_form = RunSchedulerForm()
	if csv_upload_form    is None: csv_upload_form    = CSVUploadForm()
	if request.user.is_authenticated():
		return render_to_response(
			'console/console.html',
				{'run_scheduler_form' : run_scheduler_form,
				 'csv_upload_form' : csv_upload_form},
			context_instance=RequestContext(request)
		)
	else:
		return HttpResponseRedirect('/admin/?next=%s' % request.path)

def fun_import(request, method):
	"""Imports Source metadata as CSV and provides an import report."""
	if 'datasets' == method:
		csv_upload_form = CSVUploadForm(request.POST,request.FILES)
		csv_import_status = False
		csv_import_err    = None
		report = None
		if csv_upload_form.is_valid():
			try:
				metadata_importer = MetadataImporter()
				report = metadata_importer.read_csv( 
					csv_upload_form.cleaned_data['upload_source'],
					request.FILES['upload_csv_file'] 
				)
				csv_upload_form   = CSVUploadForm()
			except Exception as e:
				csv_import_err = 'Exception while importing CSV:\n' + traceback.format_exc()
			csv_import_status  = report['errors'] == 0
			if not csv_import_status: csv_import_err = repr(report)
		return render_to_response(
			'console/console.html',
			{'run_scheduler_form' : RunSchedulerForm(),
			 'csv_upload_form'    : csv_upload_form,
			 'csv_import_status'  : csv_import_status,
			 'csv_import_err'     : csv_import_err},
			context_instance=RequestContext(request)
		)
	else: raise Http404

def scheduler(request, method):
	"""Activates a scheduling for a specified source."""
	run_scheduler_form = RunSchedulerForm(request.GET, request.POST)
	if not run_scheduler_form.is_valid():
		return console(request,run_scheduler_form=run_scheduler_form)
	source_name    = run_scheduler_form.cleaned_data['source']
	time_back = run_scheduler_form.cleaned_data['time_back']
	if   'run' == method: multithread = False
	elif 'job' == method: multithread = True
	else: raise Http404
	return HttpResponse( process_source(source_name, int(time_back), multithread=multithread) )

def scheduler_status(request):
	"""Returns a list of all active finalizers."""
	finalizers = {}
	for k,v in active_finalizers().items():
		finalizers[k] = str(v)
	return HttpResponse( json.dumps({'finalizers' : finalizers, 'live_tasks' : active_live_tasks()}) )

def wf_configuration_html(request, conf_name):
	"""Returns the content of configuration given its name."""
	if conf_name == 'html':
		fields = {}
		fields['configurations'] = forms.ChoiceField(label='Configurations', choices=CONFIG_CHOICES)
		wf_description_form = DynaForm()
		wf_description_form.setFields(fields)
		return HttpResponse( wf_description_form.as_table() )
	else:
		return HttpResponse( json.dumps(get_configuration(conf_name)) )

def scraperwiki_config(request):
	"""Returns the current ScraperWiki Configuration."""
	return HttpResponse( settings.SCRAPERWIKI_NEW_SCRAPER )

# BEGIN: Refine Specific API

def inspect_dataset(request, dataset_download_url):
	"""Allows to inspect a dataset with Google Refine"""
	dataset   = Dataset.objects.get(download=dataset_download_url)
	source    = Source.objects.get(name=dataset.source.name)
	file_meta = download_dataset_per_source(source, dataset)
	magic_type = file_meta.get('magic_type')
	if magic_type and magic_type.startswith('archive/'):
		expanded_archive = decompress(file_meta)
		archive_data_content = {}
		for path, subdirs, files in os.walk(expanded_archive):
			for name in files:
				file = os.path.join(path, name)
				if not os.path.isfile(file): continue
				archive_file = file[len(expanded_archive):]
				archive_data_content[archive_file] = { 'file' : file, 'meta' : file_meta_from_file(file) }
	else:
		out_file = file_meta['out_file']
		archive_data_content = { os.path.basename(out_file)  : { 'file' : out_file, 'meta' : file_meta_from_file(out_file) } }
	files_with_rule         = []
	desync_files_with_rules = []
	try:
		dataset = Dataset.objects.get(download=dataset_download_url)
		rules   = Rule.objects.filter( dataset_url=dataset )
		for rule in rules:
			files_with_rule.append(rule.file_path)
			if archive_data_content[rule.file_path]['meta']['md5sum'] != rule.hash:
				desync_files_with_rules.append(rule.file_path)
	except Exception:
		pass
	archive_data = {
		'refine_url'              : _to_external_refine_url( refine.RefineServer.url() ),
		'download_url'            : dataset_download_url,
		'meta'                    : file_meta,
		'content'                 : archive_data_content,
		'files_with_rule'         : files_with_rule,
		'desync_files_with_rules' : desync_files_with_rules
	}
	return render_to_response('refine/manage-rules.html', {'archive_data' : archive_data} )

def open_in_refine(request):
	"""Opens a file or archive entry with Google Refine."""
	dataset_download = request.POST['dataset']
	file             = request.POST['file']
	file_data        = request.POST['file_data']
	refine_prj     = open_project_on_file_with_rules(dataset_download, file, file_data)
	refine_prj_url = refine_prj.project_url()
	refine_prj_id  = refine_prj.project_id
	out_prj_url    = _to_external_refine_url(refine_prj_url)
	return HttpResponse( json.dumps( {'prj_url' : out_prj_url, 'prj_id' : refine_prj_id} ) )

def get_refine_rules(request, prj_id):
	"""Returns the refine rule for an existing project id."""
	refine_prj = get_refine_ws().open_project( int(prj_id) )
	return HttpResponse( json.dumps(refine_prj.get_operations()) )

def delete_refine_prj(request, prj_id):
	"""Deletes a Refine project by id."""
	refine_prj = get_refine_ws().open_project( int(prj_id) )
	return HttpResponse( json.dumps( refine_prj.delete() ) )

def store_refine_rules(request):
	"""Stores a set of refine rules for a given file with other metadata."""
	dataset_url  = request.POST['dataset_url']
	dataset_file = request.POST['file']
	hash         = request.POST['hash']
	refine_rule  = request.POST['rules']
	dataset = Dataset.objects.get(download=dataset_url)
	rule = Rule()
	rule.dataset_url_path = dataset_url + '!' + dataset_file
	rule.dataset_url      = dataset
	rule.file_path        = dataset_file
	rule.hash             = hash
	rule.rule             = refine_rule
	rule.save()
	return _success()

def retrieve_refine_rules(request):
	"""Retrieves the Google Refine rule for a given file at a specified entry path."""
	dataset = Dataset.objects.get(download=request.POST['download_url'])
	rule = Rule.objects.get(dataset_url=dataset, file_path=request.POST['file'])
	return HttpResponse( rule.rule )

def _get_source_choices():
	"""Returns a list of all available Sources."""
	result = []
	for source in Source.objects.all():
		result.append( (source.name, source.name) )
	return result

def _to_external_refine_url(url):
	return url.replace('127.0.0.1', settings.REFINE_EXTERNAL_HOST).replace(':3333', settings.REFINE_EXTERNAL_PORT)

def _success():
	return HttpResponse( json.dumps({'success' : True}) )

# END: Refine Specific API


class RunSchedulerForm(forms.Form):
	source    = forms.ChoiceField (required=True, label='Dataset Source', choices=_get_source_choices())
	time_back = forms.IntegerField(required=True, label='Time back (in secs)', initial=0)

	def __init__(self, *args, **kwargs):
		super(forms.Form, self).__init__(*args, **kwargs)
		self.fields['source'].choices = _get_source_choices()

class CSVUploadForm(forms.Form):
	upload_source   = forms.ChoiceField(required=True, label='Dataset Source', choices=_get_source_choices())
	upload_csv_file = forms.FileField  (required=True, label='CSV File')

class DynaForm(forms.Form):
	""" See: http://djangosnippets.org/snippets/714/ """
	def setFields(self, kwds):
		keys = kwds.keys()
		keys.sort()
		for k in keys:
			self.fields[k] = kwds[k]

	def setData(self, kwds):
		keys = kwds.keys()
		keys.sort()
		for k in keys:
			self.data[k] = kwds[k]

	def validate(self, post):
		for name,field in self.fields.items():
			try:
				field.clean(post[name])
			except ValidationError as e:
				self.errors[name] = e.messages
