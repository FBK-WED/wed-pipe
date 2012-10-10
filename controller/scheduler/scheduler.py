#!/usr/bin/env python

import os, sys
import os.path
import uuid
import traceback, errno
import shutil
import re
import json
import datetime
import urllib, urllib2
import threading
import copy
import hashlib
from celery.utils.log import get_task_logger
import util

from django.conf import settings
from webui.controller.models import Scheduler, Dataset, Source, config_name_to_file, get_extension
from workflow.workflow import Workflow
from celery.exceptions import TimeoutError
from celery.states import FAILURE
from util import AttrDict, to_handler_function, decompress
from refine.refine import apply_refine_on_file, get_refine_rule, IllegalRuleCheckSum

from celerymain import celery

# The protocol indicating the container for the dataset when caming from a scraper.
TABLE_PROTOCOL = 'table://'

# Content Disposition Filename extraction RE.
CONTENT_DISPOSITION_FILE = re.compile('filename="([^"]+)"')

# Object returned to force recursion from source handler.
RECURSE_MARKER = {}

def process_source(source_name, time_back, multithread=False):
	"""Processes all datasets belonging to a given source."""
	scheduler_runner = SchedulerRunner()
	yield '<html>'
	yield """
		<head>
			<link href="http://fonts.googleapis.com/css?family=Supermercado+One" rel="stylesheet" type="text/css"></link>
			<style type="text/css">
				body {
					color: white;
					background-color: black;
				}
			</style>
		</head>
	"""
	yield '<body>'
	yield '<ul>'
	for line in scheduler_runner.process_source(time_back, source_name, multithread):
		yield ( '<li>%s</li>' % line ) if len( line.strip() ) > 0 and not '<hr/>' in line else '<hr/>'
		print 'LINE:', line
	yield '</ul>'
	yield '</body>'
	yield '</html>'

def active_finalizers():
	"""Returns the list of the active workflow finalizers."""
	return copy.copy(SchedulerRunner._active_finalizers)

def active_live_tasks():
	return copy.copy(SchedulerRunner._active_live_tasks)

def get_dataset_dir(source_name, dataset_url):
	"""Given a source name and a dataset decides which is the temporary dataset dir."""
	return os.path.join(settings.TMP_DIR, urllib.quote_plus(source_name), _shorten_path_string(dataset_url ))

def download_dataset_per_source(source, dataset):
	"""Downloads dataset per source."""
	for msg in _download_dataset(
		source.scraper_name,
		source.scraper_api_key,
		dataset.download,
		get_dataset_dir(source.name, dataset.url)
	):
		if type(msg) == dict: result = msg
	return result

def file_meta_from_file(file):
	"""Computes the file metadata for a file."""
	file = file.decode('utf8') # TODO: decoding to prevent invalid chars within archive.
	try:
		ext = __ext_to_mime( get_extension(file) )
	except :
		ext = None
	return {
		'file_name'    : os.path.basename(file),
		'content_type' : ext,
		'file_size'    : os.path.getsize(file),
		'out_file'     : file,
		'md5sum'       : __md5_for_file(file)
	}

def _shorten_path_string(path):
	"""Given a path if it is longer than 255 chars it is replaced with an MD5 of the same path."""
	candidate = urllib.quote_plus(path)
	if len(candidate) > 255:
		return  hashlib.md5(path).hexdigest()
	else:
		return candidate

def _run_workflow(configuration, parameters):
	"""Runs a workflow with a configuration and a set of parameters."""
	workflow = Workflow( configuration, parameters )
	# TODO: make it configurable
	workflow.store_out = True
	workflow.store_err = True
	wf_exec_result = workflow.run_module()
	return wf_exec_result

def _run_workflow_from_handler(couple):
	"""Runs a workflow from Celery."""
	if len(couple) != 2 : raise Exception(
		'Invalid workflow configuration from handler. Expected couple( "<conf-name>", { <conf-input params> } ) . Found: ' + couple
	)
	(configuration, parameters) = couple
	return _run_workflow(config_name_to_file(configuration), parameters)

def _download_and_run_workflow(source, dataset):
	"""Downloads a dataset file, computes the dispatcher and run a workflow over it."""
	# Download dataset.
	file_meta = None
	for msg in _download_dataset(source.scraper_name, source.scraper_api_key, dataset.download, get_dataset_dir(source.name, dataset.url) ):
		if type(msg) == dict: file_meta = msg
		yield msg
	if file_meta is None: raise Exception('Expected file metadata here.')
	# Evaluate dispatcher.
	for msg in _evaluate_dispatcher_and_run_workflow(source, dataset, file_meta): yield msg

def _evaluate_dispatcher_and_run_workflow(source, dataset, file_meta):
	"""Evaluates the dispatcher of the given source for the given dataset and runs the corresponding workflow."""
	# Apply Refine rule.
	rule = get_refine_rule(dataset, file_meta)
	yield 'Found rule <pre>%s</pre> for dataset [%s] and file name [%s]' % ( repr(rule), repr(dataset.name), repr(file_meta['file_name']) )
	if rule:
		out_file     = file_meta['out_file']
		out_file_ext = get_extension(out_file)
		refined_file = out_file[0 : -len(out_file_ext)] + '.refine' + out_file_ext
		refine_meta = apply_refine_on_file(out_file, dataset.download, file_meta.get('file_path', ''), rule, refined_file)
		_append_dataset_origin_triples(refine_meta['out_file_turtle'], dataset.url, dataset.download, file_meta.get('file_path', ''))
		yield 'Refines rule applied correctly, produced file [%s], refine meta: %s' % (refined_file, refine_meta)
		file_meta['out_file']        = refined_file
		file_meta['out_file_turtle'] = refine_meta['out_file_turtle']
	# Run dispatcher to configure dataset.
	result = _evaluate_dispatcher(source, dataset, file_meta)
	if result == RECURSE_MARKER:
		for msg in _handle_recursion(source, dataset, file_meta): yield msg
	else:
		if not len(result) == 2: raise Exception(
			'Invalid result from dispatcher. Expected couple( "<conf-name>", { <conf-input params> } ) . Found: ' + result
		)
		(configuration, parameters) = result
		yield 'Running workflow: <pre>%s</pre>' % repr(result)
		yield _run_workflow( config_name_to_file(configuration), __expand_parameters(dataset, parameters) )
		yield 'Workflow completed'

def _handle_recursion(source, dataset, file_meta):
	"""Handle archive dataset recursion."""
	# Decompress archive
	archive = file_meta['out_file']
	yield 'Handing recursion on archive [%s]' % archive
	expanded_archive = decompress(file_meta)
	yield 'Archive expanded into [%s] dir' % expanded_archive

	# Iterate archive content
	for path, subdirs, files in os.walk(expanded_archive):
		for name in files:
			file = os.path.join(path, name)
			if not os.path.isfile(file): continue
			# Apply dispatcher for every content file
			try:
				new_file_meta = file_meta_from_file(file)
				new_file_meta.update( {'file_path' : file[len(expanded_archive):]} )
				yield 'Processing archive file [%s] with metadata <pre>%s</pre>' % (file, new_file_meta)
				for msg in _evaluate_dispatcher_and_run_workflow(source, dataset, new_file_meta): yield msg
				yield 'File [%s] completed' % file
			except Exception as e:
				yield 'Error while processing file [%s]:<br/>%s' % ( file, _exception_to_string(e) )

logger = get_task_logger(__name__)
@celery.task
def _download_and_run_workflow_task(source_copy, dataset_copy):
	"""_download_and_run_workflow Celery task."""
	#logger = _download_and_run_workflow_task.get_logger()
	for msg in _download_and_run_workflow(source_copy, dataset_copy):
		logger.info(msg)

def _download_url(url, save_dir):
	"""Downloads a URL into a file and save HTTP metadata."""
	request = urllib2.Request(url)
	opener = urllib2.build_opener( CustomRedirectHandler() )
	url_handler = opener.open(request)

	file_meta = __file_meta_from_headers(
		url,
		url_handler.headers,
		url_handler.redirect_headers if url_handler.__dict__.has_key('redirect_headers') else None
	)
	file_name = file_meta['file_name']

	shutil.rmtree(save_dir, True)
	__mkdir_p(save_dir)
	if file_name[-1] == '/' : file_name = file_name[0:-1]

	out_file = save_dir + '/' + file_name

	output = open(out_file, 'wb')
	file_size = file_meta['file_size']
	if file_size == 0: file_size = 1
	yield "Downloading: %s KBytes: %s" % (file_name, file_size / 1024)
	file_size_dl = 0
	block_sz = 8192
	emit_status_count = 0
	while True:
		buffer = url_handler.read(block_sz)
		if not buffer:
			break
		file_size_dl += len(buffer)
		output.write(buffer)
		status = r"%10d	 [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
		status = status + chr(8)*(len(status)+1)
		if emit_status_count >= 100:
			yield status
			emit_status_count = 0
		else:
			emit_status_count += 1
	output.close()

	# http://www.gavinj.net/2007/05/python-file-magic.html
	magic_type =  util.MS.file(out_file)
	file_meta.update({
		'out_file'   : out_file,
		'magic_type' : util.magic_to_mime(magic_type),
		'md5sum'     : __md5_for_file(out_file)
	})
	if file_meta['file_size'] == -1: file_meta['file_size'] = os.path.getsize(file_meta['out_file'])
	yield file_meta

def _process_init_handler(source):
	"""Processes the source init handler."""
	init_handler_code = source.init_handler
	if len(init_handler_code.strip()) == 0: return
	try:
		_locals  = { 'source' : source }
		_globals = {}
		INIT = 'init'
		exec to_handler_function(init_handler_code, INIT) in _locals, _globals
		result = _globals['__' + INIT]()
		return _run_workflow_from_handler(result)
	except Exception as e:
		raise Exception('Error while processing init handler.', e)

def _process_dispose_handler(source, process_stats):
	"""Processes the source dispose handler."""
	dispose_handler_code = source.dispose_handler
	if not dispose_handler_code or len(dispose_handler_code.strip()) == 0: return
	try:
		_locals  = { 'source' : source, 'process_stats' : process_stats }
		_globals = {}
		DISPOSE = 'dispose'
		exec to_handler_function(dispose_handler_code, DISPOSE) in _locals, _globals
		result = _globals['__' + DISPOSE]()
		return _run_workflow_from_handler(result)
	except Exception as e:
		raise Exception('Error while processing dispose handler.', e)

def _evaluate_dispatcher(source, dataset, file_meta):
	"""Evaluate the dispatcher for a source and dataset couple."""
	dataset.file     = file_meta['out_file']
	dataset.filerdf  = file_meta.get('out_file_turtle')
	dataset.dir      = os.path.dirname(dataset.file)
	dataset.mimetype = file_meta['content_type']
	dataset.filesize = file_meta['file_size']
	dispatcher_code  = source.dispatcher

	# Register utility functions.
	dataset.__class__.mime        = __get_mime
	dataset.__class__.mime_by_ext = __get_mime_by_ext
	dataset.__class__.ext         = __get_ext
	try:
		_locals  = {
			'UnsupportedDatasetException' : UnsupportedDatasetException,
			'source' : source,
			'dataset' : dataset,
			'recurse' : __recurse
		}
		_globals = {}
		DISPATCH = 'dispatch'
		exec to_handler_function(dispatcher_code, DISPATCH) in _locals, _globals
		result = _globals['__' + DISPATCH]()
		return result
	except Exception as e:
		if e.__class__.__name__ == 'UnsupportedDatasetException': raise e
		if e.__class__.__name__ == 'UnknownMIMETypeException'   : raise e
		if e.__class__.__name__ == 'UnknownMagicException'      : raise e
		else: raise Exception('Error while configuring workflow', e)

def __mkdir_p(path):
	"""Creates a FS path if not exists."""
	try:
		os.makedirs(path)
	except OSError as exc:
		if exc.errno == errno.EEXIST: pass
		else: raise exc

def __filename_from_url(url):
	"""Given a URL extracts the resource file name if any."""
	return url.split('/')[-1]

def __file_meta_from_headers(url, headers, redirect_headers):
	"""Extracts file metadata from headers."""
	# Determine file_name
	file_name = None
	content_disposition = headers.getheader('Content-Disposition')
	if content_disposition is None:
		content_disposition = redirect_headers.getheader('Content-Disposition') if redirect_headers is not None else None
	if content_disposition is not None:
		file_match = CONTENT_DISPOSITION_FILE.match(content_disposition)
		if file_match is not None:
			file_name = file_match.group(1)
	else:
		if redirect_headers is not None:
			location = redirect_headers.getheader('location')
			file_name = __filename_from_url(location) if location is not None else None
	if file_name is None or len( file_name.strip() ) == 0:
		file_name = __filename_from_url(url)

	content_type   = headers.getheader('Content-Type')
	content_length = headers.getheader("Content-Length")
	file_size = int(content_length) if content_length is not None else -1
	return { 'file_name' : file_name, 'content_type' : content_type, 'file_size' : file_size }

def _download_csv(scraper_name, api_key, table, save_dir):
	"""Downloads a CSV and store it into a file."""
	api_url = settings.SCRAPERWIKI_API_CSV + '&query=select%20*%20from%20%60{0}%60&name={1}'.format(table, scraper_name)
	if len( api_key.strip() ) > 0: api_url = api_url + '&apikey=' + api_key
	csv_stream = urllib2.urlopen(api_url)
	file_name = table + '.csv'
	csv_file  = save_dir + '/' + file_name
	try:
		os.makedirs(save_dir)
	except: pass
	try:
		with open(csv_file, 'w+') as csv_file_stream:
			shutil.copyfileobj(csv_stream, csv_file_stream)
	finally:
		csv_stream.close()
	return {
		'out_file'     : csv_file,
		'file_name'    : file_name,
		'file_size'    : os.path.getsize(csv_file),
		'content_type' : 'text/csv',
		'md5sum'       : __md5_for_file(csv_file)
	}

def _download_dataset(scraper_name, api_key, dataset_url, dataset_dir):
	"""Downloads the dataset resource URL."""
	if dataset_url.startswith(TABLE_PROTOCOL): # Download Scraperwiki table content.
		table = dataset_url[len(TABLE_PROTOCOL):]
		if len(table.strip() ) == 0: 
			raise Exception('Invalid table name in URL [%s]' % dataset_url )
		yield 'Downloading CSV <a href="%s">%s</a>' % (dataset_url, dataset_url)
		file_meta = _download_csv(scraper_name, api_key, table, dataset_dir)
		yield 'File metadata: <pre>' + repr(file_meta) + '</pre>'
		yield file_meta
		yield 'Download completed'
	else:									  # Download dataset resource. 
		yield 'Downloading URL <a href="%s">%s</a>' % (dataset_url, dataset_url)
		for msg in _download_url(dataset_url, dataset_dir):
			if type(msg) == dict:
				yield 'File metadata: <pre>' + repr(msg) + '</pre>'
			yield msg
		yield 'Download completed'

def __get_mime(self):
	"""Returns the MIMEType of a dataset obtained during download."""
	if self.mimetype is not None:
		return self.mimetype
	else:
		raise UnknownMIMETypeException('Download MIMEType unavailable')

def __get_mime_by_ext(self):
	"""Returns the MIMEType of a dataset computed on the download URL extension."""
	url = self.file
	ext = get_extension(url)
	return __ext_to_mime(ext)

def __ext_to_mime(ext):
	if ext == '.csv': return 'text/csv'
	if ext == '.rdf': return 'application/rdf'
	if ext == '.shp': return 'application/shp'
	if ext == '.xml': return 'application/xml'
	if ext == '.xls' or ext == '.xlsx': return 'application/msexcel'
	if ext == '.gz'  or ext == '.gzip' or ext == '.zip' or ext == '.7z': return 'application/archive'
	if ext == '.htm' or ext == '.html': return 'text/html'
	raise UnknownMIMETypeException( 'Unknown extension [%s]' % ext )

def __get_ext(self):
	return get_extension( self.file )

def __recurse():
	return RECURSE_MARKER

def __expand_parameters(dataset, params):
	"""Expand parameters within a map and it is user in the source dispatcher script."""
	result = {}
	for param in params:
		paramValue = params[param]
		match = re.search('\<([^\>]+)\>', paramValue) if paramValue else None
		if not match:
			result[param] = paramValue
			continue
		var = match.group(1)
		if var.startswith('dataset.'):
			result[param] = params[param].replace('<' + var + '>', dataset.__dict__[ var[len('dataset.'):] ] )
		else:
			raise Exception('Invalid prefix for variable:', var)
	return result

def _exception_to_string(exc):
	"""Converts an exception to HTML renderable description."""
	exc_type, exc_value, exc_traceback = sys.exc_info()
	error  = '\n'.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
	return '<font color="red">' + exc.message + '</font><br/>' + '<pre width="80">' + error + '</pre>'

def __md5_for_file(file, block_size=2**20): # TODO: is it safe?
	"""Computes the MD5 for the first block size of the file."""
	with open(file, 'r') as f:
		md5 = hashlib.md5()
		while True:
			data = f.read(block_size)
			if not data:
				break
			md5.update(data)
		return md5.hexdigest()

def _get_dataset_entry_url(dataset_url, download_url, file_path):
	"""Given a dataset URL download URL and file path computes the dataset entry URL identifier."""
	if download_url.startswith(TABLE_PROTOCOL):
		dataset_entry_url = dataset_url + '!' + download_url[len(TABLE_PROTOCOL):]
	else:
		dataset_entry_url = download_url
	dataset_resource_url = dataset_entry_url + ('!' + file_path if file_path != '' else '')
	if not dataset_entry_url.endswith('/'): dataset_entry_url += '/'
	return {'dataset_entry_url' : dataset_entry_url, 'dataset_resource_url' : dataset_resource_url}

def _append_dataset_origin_triples(turtle_file, dataset_url, download_url, file_path):
	"""
	Given a turtle file, a dataset URL a download URL and a file Path appends to the turtle file a set
	of metadata triples associated to the container graph and identifying the origin of the data.
	"""
	dataset_urls = _get_dataset_entry_url(dataset_url, download_url, file_path)
	graph_url = settings.REFINE_RDF_MAPPING_GRAPH_PREFIX + hashlib.sha1(dataset_urls['dataset_entry_url'] + file_path).hexdigest()
	with open(turtle_file, 'a') as turtle_file_handler:
		turtle_file_handler.write('@prefix sd: <%s> .\n' % settings.SD_SCHEMA)
		turtle_file_handler.write('<%s> sd:dataset          <%s> .\n' % (graph_url, dataset_urls['dataset_entry_url']) )
		turtle_file_handler.write('<%s> sd:dataset_resource <%s> .\n' % (graph_url, dataset_urls['dataset_resource_url']))

def _dispose_sequence(source, processed_dataset_count, failed_dataset_count):
	try:
		yield 'Executing dispose handler'
		wf_output = _process_dispose_handler(
			source,
			{'processed_dataset_count' : processed_dataset_count, 'failed_dataset_count' : failed_dataset_count}
		)
		yield '<font color="green">Dispose handler executed successfully.</font> Output <pre>%s</pre>' % wf_output
	except Exception as e:
		yield _exception_to_string(e)


class SchedulerRunner:
	"""The Scheduler Runner is responsible for executing a scheduling plan."""

	#List of active TaskFinalizer(s)
	_active_finalizers = {}

	# List of active live tasks.
	_active_live_tasks = []

	def __init__(self):
		pass

	def process_source(self, older_than, source_name, multithread=False):
		"""Processes a source"""
		self.__running_tasks    = []
		processed_dataset_count = 0
		failed_dataset_count	= 0
		source = Source.objects.get(name=source_name)
		if source is None: raise Exception('Error while looking up Source with id [%s]' % source_name)

		if not multithread: SchedulerRunner._active_live_tasks.append(source_name)

		# Init Handler, if an error occurs Source will not be processed.
		try:
			yield 'Evaluating Init Handler'
			wf_output = _process_init_handler(source)
			yield '<font color="green">Init handler executed successfully.</font> Output <pre>%s</pre>' % wf_output
		except Exception as e:
			yield '<font color="red">An error occurred while processing Init Handler for source [%s]</font><br/>' % source_name
			yield _exception_to_string(e)

		# Select never scheduled datasets.
		qry = "SELECT * FROM controller_dataset WHERE source_id = '%s' AND download NOT IN ( SELECT url_id FROM controller_scheduler )" % source_name
		# Copy records to release table lock.
		never_scheduled_datasets = []
		for never_scheduled_dataset in Dataset.objects.raw(qry):
			never_scheduled_datasets.append(never_scheduled_dataset)
		yield '<strong>Found <code>%d</code> never scheduled datasets</strong>' % len(never_scheduled_datasets)
		yield '<hr/>'
		for never_scheduled_dataset in never_scheduled_datasets:
			yield 'Found never scheduled dataset ' + str(never_scheduled_dataset)
			try:
				for msg in self.process_dataset(never_scheduled_dataset, source, multithread): yield msg
			except Exception as e:
				yield 'Dataset acquisition failed'
				failed_dataset_count += 1
			finally:
				processed_dataset_count += 1
				yield '<hr/>'

		# Select obsolete datasets.
		delta = datetime.datetime.now() - datetime.timedelta(seconds=older_than)
		# datetime_condition = "controller_scheduler.last_execution < Datetime('" + str(delta) + "')" # SQLite
		datetime_condition = "controller_scheduler.last_execution < timestamp '" + str(delta) + "'" # PostGres
		qry = "SELECT * FROM controller_dataset \
		       INNER JOIN controller_scheduler ON \
		       controller_scheduler.url_id = controller_dataset.download \
		       WHERE source_id = '%s' AND %s" % (source_name, datetime_condition)
		# Copy records to release table lock.
		obsolete_datasets = []
		for obsolete_dataset in Dataset.objects.raw(qry): #Dataset.objects.filter(scheduler__last_execution__lte = delta) # TODO: doesn't work
			obsolete_datasets.append(obsolete_dataset)
		yield '<strong>Found <code>%d</code> obsolete datasets</strong>' % len(obsolete_datasets)
		yield '<hr/>'
		for obsolete_dataset in obsolete_datasets:
			yield 'Found dataset schedule %s older than %d secs' % (str(obsolete_dataset), older_than)
			try:
				for msg in self.process_dataset(obsolete_dataset, source, multithread=multithread): yield msg
			except Exception as e:
				yield 'Dataset acquisition failed' # + str(e)
				failed_dataset_count += 1
			finally:
				processed_dataset_count += 1
				yield '<hr/>'

		if processed_dataset_count == 0:
			yield 'No processed datasets.'
		else:
			yield ('Scheduled ' if multithread else 'Processed') + ' datasets: <b>%d</b>' % processed_dataset_count + (' <font color="red">(failed: %d)</font>' % failed_dataset_count) if failed_dataset_count > 0 else ''

		if multithread:
			yield 'Running TaskFinalizer'
			task_finalizer_uuid = str( uuid.uuid1() )
			task_finalizer = TaskFinalizer(task_finalizer_uuid, copy.copy(self.__running_tasks), source)
			SchedulerRunner._active_finalizers[task_finalizer_uuid] = task_finalizer
			task_finalizer.start()
			yield 'TaskFinalizer registered with <b>UUID ' + task_finalizer_uuid + '</b>'
		else:
			for msg in _dispose_sequence(source, processed_dataset_count, failed_dataset_count):
				yield msg
			SchedulerRunner._active_live_tasks.remove(source_name)

	def process_dataset(self, dataset, source=None, multithread=False):
		status = None
		error  = None
		wf_exec_results = []
		try:
			if source is None: source = Source.objects.get( name=dataset.source )
			yield "Processing dataset <b>%s</b> for source <b>%s</b>" % ( dataset, source )
			source_copy  = source.copy()  if type(source)  == AttrDict else AttrDict(source.__dict__)
			dataset_copy = dataset.copy() if type(dataset) == AttrDict else AttrDict(dataset.__dict__)
			if multithread:
				async_result = _download_and_run_workflow_task.delay(source_copy, dataset_copy)
				self.__running_tasks.append( {'async_result' : async_result, 'dataset_url' : dataset.download} )
				status = 'R'
				yield 'Workflow scheduled with TaskID' + async_result.task_id
			else:
				#for msg in _download_and_run_workflow(source.scraper_name, dataset.download, dataset.dir, workflow_config_tuple):
				for msg in _download_and_run_workflow(source_copy, dataset_copy):
					if type(msg) == dict:
						wf_exec_results.append(msg)
					else:
						yield msg
				status = 'S'
				yield '<font color="green">Workflow success</font>'
		except Exception as e:
			status = 'F'
			error = None
			if e.__class__.__name__ == 'UnsupportedDatasetException':
				error = 'Unsupported Dataset MIME Type'
			elif e.__class__.__name__ == 'HTTPError':
				error = 'Dataset no longer available. ' + repr(e)
			elif e.__class__.__name__ == 'UnknownMIMETypeException':
				error = 'Unknown MIME type: ' + repr(e)
			elif e.__class__.__name__ == 'UnknownMagicException':
				error = 'Unknown Magic Code: ' + repr(e)
			elif e.__class__ == IllegalRuleCheckSum:
				error = 'Illegal Rule CheckSum'
				status = 'I'
			else:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				error  = u'\n'.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
			yield '<font color="red">Process failure</font>'
			yield '<pre width="80">' + error + '</pre>'
			raise e
		finally:
			out_params = json.dumps( wf_exec_results )
			Scheduler(
				url=dataset,
				last_execution=datetime.datetime.now(),
				status=status,
				error=error,
				out_params=out_params
			).save(force_update=False)

class TaskFinalizer(threading.Thread):
	""" Listens for job terminations and updates the Scheduler table."""

	def __init__(self, uuid, running_tasks, source):
		threading.Thread.__init__(self)
		self.__uuid          = uuid
		self.__running_tasks = running_tasks
		self.__source        = source

	@property
	def uuid(self):
		return self.__uuid

	def run(self):
		processed_datasets_count = self.__running_tasks
		failed_dataset_count = 0
		while len(self.__running_tasks) > 0:
			for running_task in self.__running_tasks:
				try:
					async_result = running_task['async_result']
					wf_exec_results = async_result.get(timeout=1)
					self.__running_tasks.remove(running_task)
					if async_result.status == FAILURE:
						status = 'F'
						error = async_result.traceback
						out_params = None
						failed_dataset_count =+ 1
					else:
						status = 'S'
						error = None
						out_params = json.dumps( wf_exec_results )
					dataset = Dataset.objects.get(download=running_task['dataset_url'])
					Scheduler(
						url=dataset,
						last_execution=datetime.datetime.now(),
						status=status,
						error=error,
						out_params=out_params
					).save(force_update=True)
					print 'Task ' + async_result.task_id + ' finalized'
				except TimeoutError: pass
				except Exception:
					print 'Error while finalizing task [%s]: ' % async_result.task_id
					traceback.print_exc()
		del SchedulerRunner._active_finalizers[self.__uuid]
		_dispose_sequence(self.__source, processed_datasets_count, failed_dataset_count)

class UnsupportedDatasetException(Exception):
	"""The dataset is unsupported: the dispatcher returned a None configuration."""
	def __init__(self, msg):
		Exception.__init__(self, msg)

class UnknownMIMETypeException(Exception):
	"""Is not possible to establish the dataset MIME Type."""
	def __init__(self, msg):
		Exception.__init__(self, msg)

class UnknownMagicException(Exception):
	"""The magic code returned by the file is unknown"""
	def __init__(self, msg):
		Exception.__init__(self, msg)

# http://stackoverflow.com/questions/4953487/how-do-i-access-the-original-response-headers-that-contain-a-redirect-when-using
class CustomRedirectHandler(urllib2.HTTPRedirectHandler):
	"""Custom redirect to keep the original HTTP handler."""
	def http_error_301(self, req, fp, code, msg, headers):
		result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
		result.status  = code
		result.redirect_headers = headers
		return result
	def http_error_302(self, req, fp, code, msg, headers):
		result = urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
		result.status  = code
		result.redirect_headers = headers
		return result
	def http_error_303(self, req, fp, code, msg, headers):
		result = urllib2.HTTPRedirectHandler.http_error_303(self, req, fp, code, msg, headers)
		result.status  = code
		result.redirect_headers = headers
		return result

def main(argv):
	sys.path.append(os.path.dirname(__file__) + '/../' )
	os.environ['DJANGO_SETTINGS_MODULE'] = 'webui.settings'

	def help():
		print 'Usage:', argv[0], '<older-than (secs)>', '<source name>'

	if( len(argv) != 3):
		help()
		return 1
	try:
		source = Source.objects.get( name=argv[2] )
		if source is None: raise Exception('Unknown source name')
		scheduler_runner = SchedulerRunner()
		for out in scheduler_runner.process_source( int(argv[1]), source.name ):
			print out
		return 0
	except Exception as e:
		print 'Error while running scheduler:', e
		help()
		traceback.print_exc(file=sys.stderr)
		return 2

# CLI
if __name__ == "__main__":
	sys.exit( main(sys.argv) )
