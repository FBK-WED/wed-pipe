"""
Controller WebUI Data Model.

Source   : list of available dataset sources.
           Every source has a scraper which provide a metadata table and optionally one or more data tables.
Dataset  : list of scraped datasets.
           Every dataset is associated to single Source and represents a downloadable resource.
Scheduler: list of scheduled Datasets, every Schedule is associated to the latest execution of a  Dataset.
Rule     : list of optional transformation and mapping rules associated to a dataset or an entry
           (an entry refers to sub content of a dataset when the dataset is an archive).
           Currently such rules are based on Google Refine.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from util import validate_handler

import os
import json
import string

CONFIG_DIR = '/../../configurations/'
CONFIG_EXT = '.json'

DISPATCHER_DEFAULT = """
mime = dataset.mime_by_ext()
ext  = dataset.ext()
if mime == 'text/csv' or dataset.mime():
    if dataset.filerdf is not None:
        return ("rdf-configuration", {  "data" : dataset.filerdf ,  "graph" : u'http://mapped.example.org/graph/' + dataset.url})
    else:
        return ('tab-configuration', { 'database' : 'wedpipe-test', 'schema' : '<DATASET SCHEMA>', 'data' : dataset.file })
else:
    raise UnsupportedDatasetException('Unknown MIMEType')
"""

DISPOSE_HANDER_DEFAULT = """
return ( '2rdf-configuration', { 'source' : source.name } )
"""

def validate_json(candidate_json):
    """Validates the JSON string trying to parse it."""
    try:
        json.loads(candidate_json)
    except Exception as e:
        raise ValidationError('Invalid JSON')

def validate_bbox(candidate_bbox):
    """Validates a string representing a bounding box."""
    try:
        parts = candidate_bbox.split(',')
        if len(parts) != 4: raise Exception("Invalid number of elements, expected 4.")
        for i in (0,2):
            if float(parts[i]) < -180 or float(parts[i]) > + 180:
                raise Exception("Invalid value in bounding box.")
        for i in (1,3):
            if float(parts[i]) < -90 or float(parts[i]) > + 90:
                raise Exception("Invalid value in bounding box.")
    except Exception as e:
        raise ValidationError('Invalid Bounding Box: ' + repr(e))

def validate_parameters(config_params, params):
    """Validates a configuration parameter."""
    for config_param in config_params:
        if not config_param in params:
            raise ValidationError("Parameters must define field '{0}'".format(config_param))

def validate_dispatcher(dispatcher):
    """Dispatcher python code validation."""
    validate_handler(dispatcher, 'dispatcher')

def validate_init_handler(handler):
    """Initialization handler python code validation."""
    validate_handler(handler, 'init')

def validate_dispose_handler(handler):
    """Disposition handler python code validation."""
    validate_handler(handler, 'dispose')

def read_configurations():
    """
    Loads the list of all available configurations. A configuration is a file with extension '.json'
    stored under the 'controller/configurations' dir.
    """
    config_dir = os.path.dirname(os.path.realpath(__file__)) + CONFIG_DIR
    result = []
    for conf in os.listdir(config_dir):
        ext_index = string.rfind(conf, CONFIG_EXT)
        if ext_index == -1: continue
        conf_name = conf[0:ext_index]
        result.append((conf_name, conf_name))
    return result

def get_configuration(config_name):
    """Returns a configuration content (as Dict object) by name."""
    config = open(config_name_to_file(config_name))
    return json.loads(config.read())

def config_name_to_file(config_name):
    """Given a config name returns the absolute config file."""
    config_file = os.path.dirname(os.path.realpath(__file__)) + CONFIG_DIR + config_name + CONFIG_EXT
    if not os.path.exists(config_file):
        raise Exception(
            'Cannot find configuration file [%s] for configuration name [%s]' %
            (config_file, config_name)
        )
    return config_file

def get_extension(url):
    """Returns the rightmost extension of a URL resource if any."""
    NO_EXT = None
    index = url.rfind('.')
    if index == -1:
        return NO_EXT
    else:
        out = url[index:]
        amp_index = out.rfind('&')
        out = out if amp_index == -1 else out[:amp_index]
        percent_index = out.rfind('%')
        out = out if percent_index == -1 else out[percent_index:]
        return out if not '%' in out else NO_EXT

def tag_list(tags):
    """Converts a string of comma-separated values into a list."""
    return map(lambda t: t.strip(), tags.split(','))

CONFIG_CHOICES = read_configurations()

SCHEDULING_STATUS = (('S', 'Success'), ('F', 'Fail'), ('I', 'Invalid'), ('R', 'Running'))

class Source(models.Model):
    # Name of the data source.
    name = models.CharField(primary_key=True, max_length=1024)
    # Data source description.
    description = models.TextField(blank=False)
    # Comma separated list of tags.
    tags = models.CharField(blank=False, max_length=1024)
    # User responsible for this scraper.
    user = models.CharField(blank=False, max_length=1024)
    # Scraper unique identifier.
    scraper_name = models.CharField(blank=True, max_length=256)
    # Scraper API Key for private access.
    scraper_api_key = models.CharField(blank=True, null=True, max_length=50)
    # Python code responsible to dispatch a specific dataset to a workflow.
    dispatcher = models.TextField(blank=False, default=DISPATCHER_DEFAULT, validators=[validate_dispatcher])
    # Initializes the processing for a Source.
    init_handler = models.TextField(blank=True, validators=[validate_init_handler])
    # Finalizes the processing for a Source.
    dispose_handler = models.TextField(blank=True, default=DISPOSE_HANDER_DEFAULT,
        validators=[validate_dispose_handler])

    def tag_list(self):
        return tag_list(self.tags)

    def __unicode__(self):
        return self.name


class Dataset(models.Model):
    # Belonging source.
    source = models.ForeignKey(Source)
    # Contains the URL to access the dataset data.
    # PK
    download = models.CharField(primary_key=True, max_length=1024, validators=[URLValidator])
    # Contains the URL to access the dataset metadata.
    url = models.CharField(blank=False, max_length=1024, validators=[URLValidator])
    # Update frequency rule.
    update_rule = models.CharField(blank=True, null=True, max_length=64)

    # Updatable
    # Specific dataset name.
    name = models.CharField(blank=False, max_length=1024)
    # Specific dataset curator.
    curator = models.CharField(blank=False, max_length=1024)
    # Specific dataset license.
    license = models.CharField(blank=False, max_length=1024)
    # Specific dataset description
    description = models.TextField(null=True)
    # Specific dataset comma separated list of tags.
    tags = models.CharField(null=True, max_length=1024)
    # Dataset bounding box in form <minlon,minlat,maxlon,maxlat> .
    bounding_box = models.CharField(blank=True, null=True, max_length=64, validators=[validate_bbox])
    # Other metadata expressed in JSON.
    other_meta = models.TextField(null=True, validators=[validate_json])

    def ext(self):
        return get_extension(self.download)

    def tag_list(self):
        return tag_list(self.tags)

    def __unicode__(self):
        ext = get_extension(self.download)
        return u"{0} ({1}) [{2}]".format(self.name, self.source.name, ext if ext is not None else 'No Ext')


class Scheduler(models.Model):
    # Dataset URL identifier.
    url = models.ForeignKey(Dataset, primary_key=True,
        related_name='Dataset.dataset_url') # TODO: this must be dataset.download
    # Last execution time.
    last_execution = models.DateTimeField()
    # Last scheduling status.
    status = models.CharField(max_length=1, choices=SCHEDULING_STATUS)
    # Produced error if any.
    error = models.TextField(blank=False, null=True)
    # A JSON containing the workflow execution output parameters.
    out_params = models.TextField(blank=False, null=True)

    def source(self):
        return self.url.source.name

    def dataset(self):
        return self.url.name

    def ext(self):
        return self.url.ext()

    def __unicode__(self):
        return u"{0} [{1}] {2} - {3}".format(self.url.name, self.ext(), str(self.last_execution),
            'SUCCESS' if self.status == 'S' else 'FAIL')


class Rule(models.Model):
    """Rule associated to a dataset file."""
    # Full dataset URL path.
    dataset_url_path = models.TextField(primary_key=True)
    # Dataset download URL for the generated rule.
    dataset_url = models.ForeignKey(Dataset, related_name='Dataset.download')
    # HASH code of the file used to create the rule.
    hash = models.CharField(max_length=40, blank=False, null=False, unique=True)
    # Full file path to the internal archive entry if the dataset is an archive.
    file_path = models.TextField(blank=False, null=True)
    # Rule content.
    rule = models.TextField(blank=False, null=False)