"""
WED Pipe WebUI Data Model.

Source   : list of available dataset sources.
           Every source has a scraper which provide a metadata table and
           optionally one or more data tables.
Dataset  : list of scraped datasets.
           Every dataset is associated to single Source and represents a
           downloadable resource.
Rule     : list of optional transformation and mapping rules associated to a
           dataset or an entry
           (an entry refers to sub content of a dataset when the dataset is
           an archive).
           Currently such rules are based on Google Refine.
"""
import webui.controller.conf  # custom conf, do not remove

import os
import json
from urllib import urlencode

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, MinLengthValidator
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import permalink
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.generic import GenericRelation

from jsonfield import JSONField
from django_extensions.db.models import TimeStampedModel

from taggit.managers import TaggableManager

from util import validate_handler
from webui.controller.helpers import Scraperwiki
from webui.cnmain.helpers import get_extension
from webui.scheduler.models import Scheduler


CONFIG_DIR = settings.REPO_ROOT + '/configurations/'
CONFIG_EXT = '.json'


def get_connection_string():
    """ Reads TABULAR_DATABASE django settings and returns a sqlalchemy
    connection string.
    """
    args = dict(settings.TABULAR_DATABASE)
    args['PORT'] = args.get('PORT') or 5432

    return "postgresql://{USER}:{PASSWORD}@{HOST}:" \
        "{PORT}/{NAME}".format(**args)


def validate_json(candidate_json):
    """Validates the JSON string trying to parse it."""
    try:
        json.loads(candidate_json)
    except Exception:
        raise ValidationError('Invalid JSON')


def validate_bbox(candidate_bbox):
    """Validates a string representing a bounding box."""
    try:
        parts = candidate_bbox.split(',')
        if len(parts) != 4:
            raise Exception("Invalid number of elements, expected 4.")
        for i in (0, 2):
            if float(parts[i]) < -180 or float(parts[i]) > + 180:
                raise Exception("Invalid value in bounding box.")
        for i in (1, 3):
            if float(parts[i]) < -90 or float(parts[i]) > + 90:
                raise Exception("Invalid value in bounding box.")
    except Exception as e:
        raise ValidationError('Invalid Bounding Box: ' + repr(e))


def validate_parameters(config_params, params):
    """Validates a configuration parameter."""
    for config_param in config_params:
        if not config_param in params:
            raise ValidationError(
                "Parameters must define field '{0}'".format(config_param)
            )


def validate_dispatcher(dispatcher):
    """Dispatcher python code validation."""
    validate_handler(dispatcher, 'dispatcher')


def validate_init_handler(handler):
    """Initialization handler python code validation."""
    validate_handler(handler, 'init')


def validate_dispose_handler(handler):
    """Disposition handler python code validation."""
    validate_handler(handler, 'dispose')


def validate_hash_handler(handler):
    """Hashcode handler python code validation."""
    validate_handler(handler, 'hash')


def read_configurations():
    """
    Loads the list of all available configurations. A configuration is a file
    with extension '.json'
    stored under the 'controller/configurations' dir.
    """
    result = []
    for conf in os.listdir(CONFIG_DIR):
        ext_index = conf.rfind(CONFIG_EXT)
        if ext_index == -1:
            continue
        conf_name = conf[0:ext_index]
        result.append((conf_name, conf_name))
    return result


def get_configuration(config_name):
    """Returns a configuration content (as Dict object) by name."""
    with open(config_name_to_file(config_name), 'r') as config:
        return json.loads(config.read())


def config_name_to_file(config_name):
    """Given a config name returns the absolute config file."""
    config_file = CONFIG_DIR + config_name + CONFIG_EXT
    if not os.path.exists(config_file):
        raise Exception(
            'Cannot find configuration file [%s] for configuration name [%s]' %
            (config_file, config_name)
        )
    return config_file


CONFIG_CHOICES = read_configurations()


class Source(models.Model):
    """ A source of data, possibly containing more datasources
    """
    # Name of the data source.
    name = models.CharField(
        unique=True,
        max_length=1024,
        blank=False,
        validators=[MinLengthValidator(3)]
    )
    # Data source description.
    description = models.TextField()
    # User responsible for this scraper.
    user = models.ForeignKey(
        to=User,
    )
    scraperwiki_url = models.URLField(
        null=True,
        blank=True,
        max_length=1024,
        default=settings.SCRAPERWIKI_APP,
    )
    # Scraper unique identifier.
    scraper_name = models.CharField(
        null=True,
        blank=True,
        max_length=256,
    )
    # Scraper API Key for private access.
    scraper_api_key = models.CharField(
        blank=True,
        null=True,
        max_length=50,
    )
    # Python code responsible to dispatch a specific dataset to a workflow.
    dispatcher = models.TextField(
        null=True,
        blank=True,
        validators=[validate_dispatcher],
        help_text='Source Dispatcher code in Python'
    )
    # Initializes the processing for a Source.
    init_handler = models.TextField(
        blank=True,
        validators=[validate_init_handler],
        help_text='Source Init Handler code in Python'
    )
    # Finalizes the processing for a Source.
    dispose_handler = models.TextField(
        blank=True, default=settings.CONTROLLER_DISPOSE_HANDER_DEFAULT,
        validators=[validate_dispose_handler],
        help_text='Source Dispose Handler code in Python'
    )
    # Allows to generate a hash for dataset records which need to be
    # processed as stream.
    hash_handler = models.TextField(
        blank=True,
        null=True,
        validators=[validate_hash_handler],
        help_text='Source Hash generator code in Grel'
    )

    tags = TaggableManager(
        blank=True,
        help_text=None,  # NB[tia]: do not remove: crispy shows this help
    )

    is_public = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    @permalink
    def get_absolute_url(self):
        return 'source_detail', (self.pk, )

    @property
    def public_name(self):
        return self.name if self.is_public else "Venturi Partner"

    def has_scraper(self):
        """ True iff this source is handled by a scraper
        """
        return self.scraperwiki_url and self.scraper_name

    @property
    def scraperwiki(self):
        """ return the scraperwiki instance of this source
        """
        return Scraperwiki.from_source(self)

    def scraper_url(self):
        """ return the url of the scraper of this source
        """
        return self.scraperwiki.scraper_url()

    def scraper_csv_api(self, table):
        """ return the url of the CSV api of the scraper of this source
        """
        return self.scraperwiki.scraper_csv_api(table)

    def get_scheduler(self, size):
        """ return the last :size schedulers of this source
        """
        # pylint: disable=E1101
        dataset_ctype = ContentType.objects.get_for_model(Dataset)
        return Scheduler.objects.filter(
            content_type=dataset_ctype,
            object_id__in=self.datasets.all(),
        )[:size]

    @property
    def archiveitems_refine_status(self):
        """ check whether each archiveitem in this source has a refine rule.
        -1: some archiveitems have no rule
         0: no archiveitems in this source
         1: all the archiveitems have a rule
        """
        if self.archiveitems.filter(rule__isnull=True).count():
            return -1
        if self.archiveitems.count():
            return 1
        return 0

    @property
    def archiveitems_aggregator_status(self):
        """ check whether each archiveitem in this source is associated
        to at least one aggregator.
        -1: some archiveitems have no aggregators
         0: no archiveitems in this source
         1: all the archiveitems have at lease one aggregator
        """
        if self.archiveitems.filter(aggregators__isnull=True).count():
            return -1
        if self.archiveitems.count():
            return 1
        return 0

    @property
    def archiveitems(self):
        """ a queryset of the archiveitems associated to this source
        """
        return ArchiveItem.objects.filter(dataset__source=self)

    @property
    def metagraph_resource_id(self):
        """ return the resource identification to be used in a RDF graph
        """
        return '{}source-{}'.format(
            settings.TRIPLE_DATABASE['PREFIXES']['sdres'], self.pk
        )

    @property
    def metagraph_sparql_query_url(self):
        """ return the url for querying the metagraph on this source
        """
        from webui.cnmain.utils import get_sparql_query_metagraph_info
        query = get_sparql_query_metagraph_info(self)
        return reverse('sparql') + '?' + urlencode(dict(query=query))


class Dataset(models.Model):
    """ a dataset coming from a source, possibly containing more files
    """
    # Belonging source.
    source = models.ForeignKey(
        Source,
        related_name='datasets',
    )
    # Contains the URL to access the dataset data.
    download = models.CharField(
        max_length=1024,
        validators=[URLValidator]
    )

    # Contains the URL to access the dataset metadata.
    url = models.URLField(
        blank=False,
        max_length=1024,
    )

    # Update frequency rule provided by the dataset source (Unused).
    update_rule = models.CharField(
        blank=True,
        null=True,
        max_length=64
    )

    # TODO: add some help text around specific input fields.
    # Updatable
    # Specific dataset name.
    name = models.CharField(
        blank=False,
        max_length=1024,
    )

    # Specific dataset curator.
    curator = models.CharField(
        blank=False,
        max_length=1024,
        default='Venturi',
    )

    license = models.CharField(
        blank=False,
        max_length=1024,
    )

    # Specific dataset description
    description = models.TextField(
        null=True,
    )

    encoding = models.CharField(
        blank=True,
        max_length=32,
    )

    projection = models.CharField(
        blank=True,
        max_length=32,
    )

    csv_delimiter = models.CharField(
        default=',',
        max_length=5,
    )

    csv_quotechar = models.CharField(
        default='"',
        max_length=5,
    )

    tags = TaggableManager(
        blank=True,
        help_text=None,  # NB[tia]: do not remove: crispy shows this help
    )

    # Dataset bounding box in form <minlon,minlat,maxlon,maxlat>
    # expressed in EPSG 900913.
    bounding_box = models.CharField(
        blank=True,
        null=True,
        max_length=256,
        validators=[validate_bbox],
    )

    # Other metadata expressed in JSON.
    other_meta = models.TextField(  # TODO: JSON field
        null=True,
        validators=[validate_json],
        help_text='Other metadata expressed as JSON',
    )

    # reverse Generic FK
    schedulers = GenericRelation(
        Scheduler
    )

    class Meta:
        ordering = ['source', 'name']

    def __unicode__(self):
        return u"{0} ({1}) [{2}]".format(
            self.name,
            self.source.name,
            self.ext() or 'No Ext'
        )

    @permalink
    def get_absolute_url(self):
        return 'dataset_detail', (self.pk, )

    def get_scheduler(self, size):
        """ return the last :size schedulers associated to this dataset
        """
        return self.schedulers.all()[:size]

    def ext(self):
        """ the extension of the file associated to this dataset (which could
         be an archive file)
        """
        return get_extension(self.download)

    @property
    def metagraph_resource_id(self):
        """ return the resource identification to be used in a RDF graph
        """
        return '{}/dataset-{}'.format(
            self.source.metagraph_resource_id,
            self.pk
        )

    @property
    def metagraph_sparql_query_url(self):
        """ return the url for querying the metagraph on this source
        """
        from webui.cnmain.utils import get_sparql_query_metagraph_info
        query = get_sparql_query_metagraph_info(self)
        return reverse('sparql') + '?' + urlencode(dict(query=query))


class Rule(models.Model):
    """Rule associated to a dataset file."""
    # HASH code of the file used to create the rule.
    hash = models.CharField(
        max_length=40, blank=False, null=False, unique=False,
        help_text="Hash sum of the file for which the rule has been generated"
    )
    # Rule content.
    rule = JSONField(
        blank=False, null=False, help_text="Google Refine rule export as JSON"
    )


class ArchiveItem(models.Model):
    """ an archiveItem, the simplest and more specific of our data-related
    structures, 1-to-many with Dataset
    """
    dataset = models.ForeignKey(Dataset, related_name='archive_items')
    file_target = models.CharField(max_length=256)
    file_hash = models.CharField(
        max_length=40,
        help_text='This is the hash of the file in the WF last execution',
        blank=False, null=False
    )

    rule = models.OneToOneField(
        Rule,
        null=True,
        blank=True,
        on_delete=models.SET(None)
    )

    refine_projectid = models.CharField(max_length=32, null=True, blank=True)
    refine_url = models.URLField(null=True, blank=True)

    _tablename = None

    class Meta:
        ordering = ('pk', )

    def __unicode__(self):
        return u"{} > {}".format(self.dataset.name, self.file_target)

    @permalink
    def get_absolute_url(self):
        return 'archiveitem_detail', (self.pk, )

    @property
    def tablename(self):
        """
        Returns the name of the table where the ArchiveItem data is stored
        """
        if not self._tablename:
            from hashlib import md5
            self._tablename = md5('{}-{}-{}'.format(
                self.dataset.source.pk,
                self.dataset.pk,
                self.file_target
            )).hexdigest()
        return self._tablename

    def data(self):
        """
        Returns a generator with the ArchiveItem data
        The first line is always the header
        """
        from contextlib import closing
        from sqlalchemy import Table, create_engine, MetaData
        engine = create_engine(get_connection_string(), encoding='utf-8')
        metadata = MetaData(bind=engine)
        table = Table(self.tablename, metadata, autoload=True)

        # Return header first
        yield tuple((c.name for c in table.columns))

        # then all the rows
        with closing(engine.connect()) as conn:
            for row in conn.execute(table.select()):
                yield row

    def data_csv(self):
        """
        Returns the ArchiveItem data as CSV
        """
        import csv
        from cStringIO import StringIO
        from sqlalchemy.exc import NoSuchTableError

        output = StringIO()
        writer = csv.writer(output)
        try:
            for row in self.data():
                enc_row = [
                    x.encode("utf-8") if isinstance(x, basestring) else x
                    for x in row
                ]
                writer.writerow(enc_row)
        except NoSuchTableError:
            return None
        csv_data = output.getvalue()
        output.close()
        return csv_data

    @property
    def metagraph_resource_id(self):
        """ return the resource identification to be used in a RDF graph
        """
        return '{}/archive-item-{}'.format(
            self.dataset.metagraph_resource_id,
            self.pk
        )

    @property
    def metagraph_sparql_query_url(self):
        """ return the url for querying the metagraph on this source
        """
        from webui.cnmain.utils import get_sparql_query_metagraph_info
        query = get_sparql_query_metagraph_info(self)
        return reverse('sparql') + '?' + urlencode(dict(query=query))

    def datagraph_raw_row_id(self, row_id_or_hash):
        """ return the resource identification to be used in the
        raw RDF datagraph, specifying the row id or hash.
        """
        return '{}/r/{}'.format(
            self.metagraph_resource_id,
            row_id_or_hash
        )

    @property
    def datagraph_raw_name(self):
        """ the name of the eaw graph stored in virtuoso
        """
        return settings.TRIPLE_DATABASE['PREFIXES']["data_graph_raw"] + \
            self.tablename

    @property
    def datagraph_sparql_raw_url(self):
        """ the URL to GET for executing a SPARQL query that returns the
         raw graph data
        """
        from webui.cnmain.utils import get_sparql_query_graph
        query = get_sparql_query_graph(self.datagraph_raw_name)
        return reverse('sparql') + '?' + urlencode(dict(query=query))

    def datagraph_mapped_row_id(self, row_id_or_hash):
        """ return the resource identification to be used in the
        mapped RDF datagraph, specifying the row id or hash.
        """
        return '{}/m/{}'.format(
            self.metagraph_resource_id,
            row_id_or_hash
        )

    @property
    def datagraph_mapped_name(self):
        """ the name of the mapped graph stored in virtuoso
        """
        return settings.TRIPLE_DATABASE['PREFIXES']["data_graph_mapped"] + \
            self.tablename

    @property
    def datagraph_sparql_mapped_url(self):
        """ the URL to GET for executing a SPARQL query that returns
         the mapped graph data
        """
        from webui.cnmain.utils import get_sparql_query_graph
        query = get_sparql_query_graph(self.datagraph_mapped_name)
        return reverse('sparql') + '?' + urlencode(dict(query=query))

    @property
    def refine_project(self):
        """
        Returns the Refine project object associated with the ArchiveItem
        Note: This performs a request to the Refine server
        """

        from refine.refine import get_refine_server_url
        from google.refine.refine import RefineProject
        if self.refine_projectid:
            try:
                prj = RefineProject(
                    get_refine_server_url(), self.refine_projectid
                )
            except ValueError:
                self.refine_projectid = self.refine_url = None
                self.save(force_update=True)
            else:
                return prj
        return None

    def create_refine_project(self, limit=None, save=True):
        """
        Creates a project on Refine

        limit: Max number of rows of the project
        save: Store the project data in the ArchiveItem

        Returns the Refine project
        """
        from tempfile import mkstemp
        from refine.refine import get_refine_ws

        csv_data = self.data_csv()

        _, csv_path = mkstemp(suffix='.csv')
        with open(csv_path, "w") as f:
            f.write(csv_data)

        project = get_refine_ws().new_project(
            project_file=csv_path, project_name=self.tablename, limit=limit,
            separator=',',
        )

        os.remove(csv_path)

        if save:
            self.refine_projectid = project.project_id
            self.refine_url = project.project_url()
            self.save(force_update=True)

        return project

    def delete_refine_project(self):
        """
        Deletes a project on Refine
        """
        prj = self.refine_project
        if prj:
            prj.delete()

    def get_refine_rule(self, check_hash=True):
        """ return the refine rule iff it's still valid
        ( refine rule means self.rule.rule, NOT the Rule model instance )
        """
        from refine.refine import IllegalRuleCheckSum
        if self.rule is None:
            return None

        # Is dataset streaming?
        hash_handler = self.dataset.source.hash_handler
        if hash_handler and hash_handler.strip():
            # Inapplicable checksum on dataset stream.
            return self.rule.rule

        if check_hash and self.rule.hash != self.file_hash:
            # rule may be invalid
            raise IllegalRuleCheckSum

        return self.rule.rule

    def sync_refine_rule(self):
        """
        Sets the rule hash equal to the file_hash
        """
        self.rule.hash = self.file_hash
        self.rule.save()

    def fetch_refine_rule(self):
        """
        Fetches the rule from Refine and creates a new Rule associated
        with the ArchiveItem
        """
        prj = self.refine_project
        rule = prj.get_operations()

        if self.rule:
            self.rule.delete()

        self.rule = Rule.objects.create(
            rule=json.dumps(rule),
            hash=self.file_hash,
        )
        self.save()

    def push_refine_rule(self):
        """
        Pushes the ArchiveItem rule to Refine
        """
        from refine.refine import strip_rules
        rules = strip_rules(self.rule.rule, self)
        prj = self.refine_project
        prj.undo_redo("0")
        prj.apply_operations_json(json.dumps(rules))


class Aggregator(models.Model):
    """ an aggregator of different ArchiveItems
    """
    name = models.CharField(
        unique=True,
        max_length=1024,
        blank=False,
        validators=[MinLengthValidator(3)]
    )
    description = models.TextField(blank=True)
    archiveitems = models.ManyToManyField(
        ArchiveItem,
        null=True,
        blank=True,
        related_name="aggregators",
        through="AggregatorArchiveItem",

    )
    entity_type = models.URLField(
        default=settings.TRIPLE_DATABASE['PREFIXES']['sdv1']
    )
    vertex_selector = models.TextField(
        default="g.V('type', 'sd$Something')%limit.id.fill(m)"
    )
    silk_rule = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    @permalink
    def get_absolute_url(self):
        return 'aggregator_detail', (self.pk, )

    def get_scheduler(self, size):
        """ return the last :size schedulers associated to this aggregator
        """
        aggregator_ctype = ContentType.objects.get_for_model(self)
        return Scheduler.objects.filter(
            content_type=aggregator_ctype,
            object_id=self.pk,
        )[:size]


class AggregatorArchiveItem(TimeStampedModel):
    """
    M2M between Aggregator and ArchiveItems. Remember which ArchiveItems are
    in which aggregator.
    """
    aggregator = models.ForeignKey(
        Aggregator
    )
    archiveitem = models.ForeignKey(
        ArchiveItem
    )

    first_workflow_success = models.DateTimeField(
        null=True,
        help_text='This is set to the first time the workflow ran successfully'
    )

    last_workflow_success = models.DateTimeField(
        null=True,
        help_text='This is set to the last time the workflow ran successfully'
    )

    deleted = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = 'controller_aggregator_archiveitems'

    def needs_update(self):
        """
        Returns True if the archiveitem has changed since last workflow
        execution.
        """
        if self.last_workflow_success is None:
            return True
        else:
            dataset = self.archiveitem.dataset

            try:
                last_scheduler = dataset.schedulers \
                    .order_by('-created').all()[0]
            except IndexError:
                return False

            if self.last_workflow_success < last_scheduler.created:
                return True
