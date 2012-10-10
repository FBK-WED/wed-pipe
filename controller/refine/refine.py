import hashlib
import util
import json

from google.refine import refine
from webui.controller.models import Dataset, Rule
from csvkit import convert
from django.conf import settings

CSV_SEPARATOR = ','

RDF_SCHEMA_MAPPING_OPERATION = 'rdf-extension/save-rdf-schema'

def get_refine_ws():
	"""Returns a new Google Refine workspace."""
	return refine.Refine(None)

def normalize_csv(in_file_path):
	"""Given an input tabular file (csv,xls, dbf) produces a normalized CSV."""
	mimetype = util.magic_to_mime( util.MS.file(in_file_path) )
	if    mimetype == 'text/plain'        : format = 'csv'
	elif  mimetype == 'application/excel' : format = 'xls'
	elif  mimetype == 'application/dbf'   : format = 'dbf'
	else: raise Exception('Unsupported mimetype ' + repr(mimetype))

	kvargs = {}
	out_file_path = in_file_path + '.normalized'
	with open(out_file_path, 'w') as output_file, open(in_file_path, 'r') as in_csv_file:
		output_file.write(convert.convert(in_csv_file, format, **kvargs))
	print 'Normalized CSV:', out_file_path
	return out_file_path

def get_refine_rule(dataset, file_meta):
	"""Retrieves the GRefine refining JSON rule from database for the specified file metadata."""
	file_target = file_meta['file_path'] if file_meta.has_key('file_path') else file_meta['file_name']
	try:
		dataset = Dataset.objects.get(download=dataset.download)
		rule    = Rule.objects.get(dataset_url=dataset, file_path=file_target)
	except Exception as e:
		print 'Error while looking up rule:', repr(e)
		return None
	if rule.hash != file_meta['md5sum']:
		raise IllegalRuleCheckSum('Expected [%s] found [%s]' % (rule.hash, file_meta['md5sum']))
	return rule.rule

def change_base_uri(operation, download_url, file_path):
	"""Changes the base URI of the RDF mapping operation with one depending on the dataset source."""
	operation['schema']['baseUri'] = \
		settings.REFINE_RDF_MAPPING_BASE_URI + '/' + \
		hashlib.sha1(download_url + file_path if file_path else '').hexdigest() + '/'

def strip_rules(rules_str, download_url, file_path):
	"""Strips out non operation entries from a given GRefine history JSON export."""
	rules_json = json.loads(rules_str)
	rules = []
	for rule_json in rules_json:
		operation = rule_json['operation']
		if operation.get('op') == RDF_SCHEMA_MAPPING_OPERATION:
			change_base_uri(operation, download_url, file_path)
		rules.append(operation)
	return json.dumps(rules)

def open_project_on_file_with_rules(dataset_download_url, file_path, file):
	"""Opens a GRefine project over a dataset file with given metadata (used to lookup rules)."""
	dataset = Dataset.objects.get(download=dataset_download_url)
	rule = None
	try:
		rule = Rule.objects.get(dataset_url=dataset, file_path=file_path)
	except : pass
	refine_prj = get_refine_ws().new_project( project_file=normalize_csv(file), separator=CSV_SEPARATOR )
	if rule and len(rule.rule) > 0:
		refine_prj.apply_operations_json( strip_rules(rule.rule, dataset_download_url, file_path) )
	return refine_prj

def apply_refine_on_file(in_file, dataset_download_url, file_path, rules, out_file):
	"""Applies a set of rules over an input file and produces an output file."""
	refine_prj = get_refine_ws().new_project(project_file=normalize_csv(in_file), separator=CSV_SEPARATOR )
	if rules and len(rules) > 0:
		refine_prj.apply_operations_json( strip_rules(rules, dataset_download_url, file_path) )
	file_handler = refine_prj.export(export_format='csv')
	out_file_turtle = out_file + '.turtle'
	util.delete_file_silently(out_file)
	util.delete_file_silently(out_file_turtle)
	with open(out_file, 'w') as out_file_handler:
		out_file_handler.write( file_handler.read() )
	export_rdf_file(refine_prj, out_file_turtle)
	return { 'out_file_turtle' : out_file_turtle }

def contain_rdf_mapping(operations):
	"""Checks whether a set of operations and """
	for operation in operations:
		try:
			if operation['operation']['op'] == u'rdf-extension/save-rdf-schema': return True
		except Exception: pass
	return False

def export_rdf_file(refine_prj, out_file):
	"""Exports content of a GRefine project to an output file."""
	if contain_rdf_mapping( refine_prj.get_operations() ):
		sock = refine_prj.export('turtle')
		with open(out_file, 'w') as out_file_handler:
			while True:
				line = sock.readline()
				if line == '': break
				out_file_handler.write(line)

class IllegalRuleCheckSum(Exception):
	"""
	A Dataset file declares a rule which checksum is different from the one
	generated during the definition of that rule.
	"""

	def __init__(self, msg):
		Exception.__init__(self, msg)