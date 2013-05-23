""" celery tasks for the data workflow
"""
import os
import errno
import shutil
import re
import datetime
import urllib
import urllib2
import hashlib
from collections import namedtuple
from contextlib import closing

import redis
import simplejson as json

from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from celery import task, group
from celery.utils.log import get_task_logger
from celery.utils.threads import Local, LocalManager

from webui.scheduler.helpers import timestamp_now, _shorten_path_string, \
    ext_to_mime
from webui.scheduler.log import get_redis_logger, get_redis_key, END
import util
from webui.scheduler.errors import UnsupportedDatasetException, \
    UnknownMIMETypeException
from webui.importer.importer import SCRAPER_PROTOCOL, get_table_name
from .models import Scheduler
from webui.controller.models import Dataset, config_name_to_file, \
    ArchiveItem
from webui.cnmain.helpers import get_extension
from workflow.workflow import Workflow
from util import to_handler_function, decompress
from refine.refine import IllegalRuleCheckSum
from webui.controller.conf import settings as cnsettings

# Content Disposition Filename extraction RE.
CONTENT_DISPOSITION_FILE = re.compile('filename="([^"]+)"')

# Object returned to force recursion from source handler.
RECURSE_MARKER = {}

# pylint: disable=C0103
logger = get_task_logger(__name__)

local = Local()
local_manager = LocalManager()

FileMeta = namedtuple('FileMeta', 'path mime_by_ext mime_by_origin')
# pylint: enable=C0103


def get_dataset_dir(source_name, dataset_url):
    """Given a source name and a dataset decides which is the temporary
    dataset dir.
    """
    return os.path.join(
        settings.TMP_DIR,
        urllib.quote_plus(source_name),
        _shorten_path_string(dataset_url)
    )


def download_dataset(dataset):
    """Downloads dataset per source."""
    loggy = local.logger
    source = dataset.source

    dataset_dir = get_dataset_dir(source.name, dataset.url)
    dataset_download = dataset.download

    # Download Scraperwiki table content.
    if dataset_download.startswith(SCRAPER_PROTOCOL):
        table = get_table_name(dataset_download).strip()
        if not table:
            raise Exception(
                'Invalid table name in URL [%s]' % dataset_download)
        loggy.info('Downloading CSV %s', dataset_download)
        file_meta = _download_csv_from_scraperwiki(
            source.scraper_csv_api(table), table, dataset_dir
        )
        loggy.info('File metadata: %r', file_meta)
    # Download dataset resource.
    else:
        loggy.info('Downloading URL %s', dataset_download)
        file_meta = _download_url(dataset_download, dataset_dir)
    loggy.info('Download completed')

    return file_meta


def file_meta_from_file(file_):
    """Computes the file metadata for a file."""

    # TODO: decoding to prevent invalid chars within archive.
    file_ = file_.decode('utf8')
    try:
        ext = ext_to_mime(get_extension(file_))
    except:  # pylint: disable=W0702
        ext = None
    return {
        'file_name': os.path.basename(file_),
        'content_type': ext,
        'file_size': os.path.getsize(file_),
        'out_file': file_,
        'md5sum': md5_for_file(file_)
    }


def _run_workflow_from_handler(couple):
    """Runs a workflow from Celery."""
    try:
        configuration, parameters = couple
    except ValueError:
        raise Exception(
            'Invalid workflow configuration from handler. Expected '
            'couple( "<conf-name>", { <conf-input params> } ) . '
            'Found: ' + couple
        )
    return Workflow(
        config_name_to_file(configuration),
        parameters,
        store_output=True,
    ).run_module()


def evaluate_dispatcher_and_run_workflow(scheduler, file_meta):
    """ Evaluates the dispatcher of the given source for the given dataset
    and runs the corresponding workflow.
    """
    loggy = local.logger
    dataset = scheduler.content_object

    file_target = file_meta.get('file_path', file_meta['file_name'])
    archive_item, dummy = ArchiveItem.objects.get_or_create(
        dataset=dataset,
        file_target=file_target
    )

    archive_item.file_hash = file_meta['md5sum']
    archive_item.save(force_update=True)

    wf_input_params = []
    wf_exec_results = []

    # Run dispatcher to configure dataset.
    result = _evaluate_dispatcher(archive_item, file_meta)

    if result == RECURSE_MARKER:
        archive_item.delete()  # archive_item cleanup
        return _handle_recursion(scheduler, file_meta)
    else:
        # if any of the ArchiveItems have no rules attached, mark the
        # scheduler as incomplete
        if not archive_item.get_refine_rule():
            scheduler.status = Scheduler.INCOMPLETE

        if not type(result) == list:
            result = [result]
        for result_elem in result:
            if not len(result_elem) == 2:
                raise Exception(
                    'Invalid workflow configuration from dispatcher. '
                    'Expected couple( "<conf-name>", { <conf-input params> } '
                    ') . Found: ' + result_elem
                )

            configuration, parameters = result_elem

            wf_input_params.append({
                'workflow': configuration,
                'parameters': parameters
            })

            loggy.info('Running workflow: %s', result_elem)
            wf_exec_results.append(Workflow(
                config_name_to_file(configuration),
                __expand_parameters(dataset, parameters),
                store_output=True
            ).run_module())
            loggy.info('Workflow completed')

    return wf_input_params, wf_exec_results


def _handle_recursion(scheduler, file_meta):
    """Handle archive dataset recursion."""
    loggy = local.logger
    wf_input_params = []
    wf_exec_results = []

    # Decompress archive
    archive = file_meta['out_file']
    loggy.info('Handing recursion on archive [%s]', archive)
    expanded_archive = decompress(file_meta)
    loggy.info('Archive expanded into [%s] dir', expanded_archive)

    # Iterate archive content
    for path, dummy, files in os.walk(expanded_archive):
        for name in files:
            file_ = os.path.join(path, name)
            if not os.path.isfile(file_):
                continue

            # skip hidden (or weird) files
            if name.startswith(('.', '__')):
                continue

            # Apply dispatcher for every content file
            new_file_meta = file_meta_from_file(file_)
            new_file_meta.update(
                {'file_path': file_[len(expanded_archive):]})
            loggy.info(
                'Processing archive file [%s] with metadata %s',
                file_, new_file_meta
            )
            try:
                wfin, wfout = evaluate_dispatcher_and_run_workflow(
                    scheduler, new_file_meta
                )
            except:
                loggy.exception('Error while processing file [%s]', file_)
                raise
            else:
                wf_input_params += wfin
                wf_exec_results += wfout
                loggy.info('File [%s] completed', file_)

    return wf_input_params, wf_exec_results


def _download_url(url, save_dir):
    """Downloads a URL into a file and save HTTP metadata."""
    loggy = local.logger

    request = urllib2.Request(url)
    opener = urllib2.build_opener(CustomRedirectHandler())
    url_handler = opener.open(request)

    file_meta = __file_meta_from_headers(
        url,
        url_handler.headers,
        url_handler.redirect_headers
        if hasattr(url_handler, 'redirect_headers') else None
    )
    file_name = file_meta['file_name']

    # do not remove directory here, download may be in parallel with other
    # tasks using the same URL
    # shutil.rmtree(save_dir, True)
    __mkdir_p(save_dir)
    if file_name[-1] == '/':
        file_name = file_name[0:-1]

    out_file = save_dir + '/' + file_name

    output = open(out_file, 'wb')
    file_size = file_meta['file_size']
    if file_size == 0:
        file_size = 1
    loggy.info("Downloading: %s KBytes: %s", file_name, file_size / 1024)
    file_size_dl = 0
    block_sz = 8192
    emit_status_count = 0
    while True:
        data_buffer = url_handler.read(block_sz)
        if not data_buffer:
            break
        file_size_dl += len(data_buffer)
        output.write(data_buffer)
        if emit_status_count >= 100:
            loggy.info("%10d [%3.2f%%]", file_size_dl,
                       file_size_dl * 100. / file_size)
            emit_status_count = 0
        else:
            emit_status_count += 1
    output.close()

    # http://www.gavinj.net/2007/05/python-file-magic.html
    magic_type = util.MS.file(out_file)
    file_meta.update({
        'out_file': out_file,
        'magic_type': util.magic_to_mime(magic_type),
        'md5sum': md5_for_file(out_file)
    })
    if file_meta['file_size'] == -1:
        file_meta['file_size'] = os.path.getsize(file_meta['out_file'])
    return file_meta


def _process_init_handler(source):
    """Processes the source init handler."""
    loggy = local.logger

    init_handler_code = source.init_handler
    if not init_handler_code or not init_handler_code.strip():
        return
    try:
        _locals = {'source': source}
        _globals = {}
        function_name = 'init'
        exec to_handler_function(init_handler_code, function_name) \
            in _locals, _globals
        result = _globals['__' + function_name]()
        return _run_workflow_from_handler(result)
    except:
        loggy.exception('Error while processing init handler.')
        raise


def _process_dispose_handler(source, process_stats):
    """Processes the source dispose handler."""
    loggy = local.logger

    dispose_handler_code = source.dispose_handler
    if not dispose_handler_code or not dispose_handler_code.strip():
        return
    try:
        _locals = {'source': source, 'process_stats': process_stats}
        _globals = {}
        function_name = 'dispose'
        exec to_handler_function(
            dispose_handler_code, function_name) in _locals, _globals
        result = _globals['__' + function_name]()
        return _run_workflow_from_handler(result)
    except:
        loggy.exception('Error while processing dispose handler.')
        raise


def _evaluate_dispatcher(archive_item, file_meta):
    """Evaluate the dispatcher for a source and dataset couple."""
    loggy = local.logger

    try:
        ext = ext_to_mime(get_extension(file_meta['out_file']))
    except UnknownMIMETypeException:
        loggy.warning("Unknown file type for %s", file_meta['out_file'])
        archive_item.delete()  # this is to not have useless archiveitems
        return []

    _file = FileMeta(
        path=file_meta['out_file'],
        mime_by_ext=ext,
        mime_by_origin=file_meta['content_type'],
    )
    dispatcher_code = archive_item.dataset.source.dispatcher \
        or cnsettings.CONTROLLER_DISPATCHER_DEFAULT

    try:
        _locals = {
            'UnsupportedDatasetException': UnsupportedDatasetException,
            'source': archive_item.dataset.source,
            'dataset': archive_item.dataset,
            'archive_item': archive_item,
            'file': _file,
            'recurse': __recurse
        }
        _globals = {}
        function_name = 'dispatch'
        exec to_handler_function(
            dispatcher_code, function_name) in _locals, _globals

        try:
            result = _globals['__' + function_name]()
        except UnsupportedDatasetException:
            loggy.warning("Can't process file %s", file_meta['out_file'])
            archive_item.delete()  # this is to not have useless archiveitems
            return []
        else:
            return result
    except Exception:
        loggy.exception('Error while configuring workflow')
        raise


def __mkdir_p(path):
    """Creates a FS path if not exists."""
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise exc


def __filename_from_url(url):
    """Given a URL extracts the resource file name if any."""
    return url.split('/')[-1]


def __file_meta_from_headers(url, headers, redirect_headers):
    """Extracts file metadata from headers."""
    # Determine file_name
    file_name = None

    content_disposition = headers.getheader('Content-Disposition')
    if not content_disposition:
        content_disposition = redirect_headers.getheader(
            'Content-Disposition') if redirect_headers is not None else None

    if content_disposition:
        file_match = CONTENT_DISPOSITION_FILE.match(content_disposition)
        if file_match is not None:
            file_name = file_match.group(1)
    else:
        if redirect_headers:
            location = redirect_headers.getheader('location')
            file_name = __filename_from_url(
                location) if location is not None else None
    if file_name is None or not file_name.strip():
        file_name = __filename_from_url(url)

    content_type = headers.getheader('Content-Type')
    content_length = headers.getheader("Content-Length")
    file_size = int(content_length) if content_length is not None else -1

    return {
        'file_name': file_name,
        'content_type': content_type,
        'file_size': file_size
    }


def _download_csv_from_scraperwiki(api_url, table, save_dir):
    """Downloads a CSV and store it into a file."""

    file_name = table + '.csv'
    csv_file = os.path.join(save_dir, file_name)
    try:
        os.makedirs(save_dir)
    except OSError:
        pass

    with closing(urllib2.urlopen(api_url)) as csv_stream:
        with open(csv_file, 'w+') as csv_file_stream:
            shutil.copyfileobj(csv_stream, csv_file_stream)

    return {
        'out_file': csv_file,
        'file_name': file_name,
        'file_size': os.path.getsize(csv_file),
        'content_type': 'text/csv',
        'md5sum': md5_for_file(csv_file)
    }


def __recurse():
    """ utility function to be passed to the source handlers, representing
     that the handler should execute a recursive call
    """
    return RECURSE_MARKER


def __expand_parameters(dataset, params):
    """
    Expand parameters within a map and it is user in the source dispatcher
    script.
    """
    result = {}
    for param, value in params.iteritems():
        match = re.search(r'\<([^\>]+)\>', value) if value else None
        if not match:
            result[param] = value
            continue
        var = match.group(1)
        if var.startswith('dataset.'):
            result[param] = params[param].replace(
                '<' + var + '>', dataset.__dict__[var[len('dataset.'):]])
        else:
            raise Exception('Invalid prefix for variable:', var)
    return result


def md5_for_file(filename, block_size=2 ** 20):  # TODO: is it safe?
    """Computes the MD5 for the first block size of the file."""

    # TODO[vad]: it's not as said in the docstring: this reads the whole file!
    with open(filename, 'rb') as f:
        md5 = hashlib.md5()
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()


@task
def dispose_sequence(results, source, task_id):
    """ execute the last step of the workflow: the dispose handler
    """
    loggy = get_redis_logger(task_id)
    local.logger = loggy

    processed_dataset_count = len(results)
    failed_dataset_count = len(
        # result could be True, False or an exception
        [result for result in results if result is not True]
    )

    loggy.info('Executing dispose handler')
    wf_output = _process_dispose_handler(source, {
        'processed_dataset_count': processed_dataset_count,
        'failed_dataset_count': failed_dataset_count
    })
    if wf_output:
        loggy.info(
            'Dispose handler executed. Output %r', wf_output
        )


@task
def process_source(source, older_than=0):
    """Processes a source"""
    red = redis.Redis()
    task_id = process_source.request.id

    local_manager.cleanup()
    loggy = get_redis_logger(task_id)
    local.logger = loggy

    red.zadd(
        'source:{}'.format(source.pk),
        get_redis_key(task_id),
        timestamp_now()
    )

    # Init Handler, if an error occurs Source will not be processed.
    loggy.info('Evaluating Init Handler')
    try:
        wf_output = _process_init_handler(source)
    except:
        loggy.exception(
            'An error occurred while processing Init Handler for source [%s]',
            unicode(source)
        )
        raise
    else:
        loggy.info(
            'Init handler executed successfully. Output %s', wf_output
        )

    # Select never scheduled datasets.
    the_date = timezone.now() - datetime.timedelta(seconds=older_than)
    dataset_ctype = ContentType.objects.get_for_model(Dataset)
    already_scheduled_datasets = Scheduler.objects.filter(
        content_type=dataset_ctype, created__gte=the_date).values('object_id')
    datasets = Dataset.objects.filter(source=source)\
                              .exclude(pk__in=already_scheduled_datasets)

    count = datasets.count()
    if count:
        loggy.info('Processing %d datasets', datasets.count())

        result = group(
            [process_dataset.s(ds, logger_name=task_id)
                for ds in datasets]
        ).apply()

        if result.successful():
            dispose_sequence.delay(result.join(), source, task_id).get()
        else:
            loggy.info('An error occurred in a process_dataset')
    else:
        loggy.info('No datasets to process')

    loggy.info(END)


@task
def process_dataset(dataset, logger_name=None):
    """ process a single dataset in the workflow
    """
    indipendent = not logger_name
    if indipendent:
        logger_name = process_dataset.request.id
    loggy = get_redis_logger(logger_name)
    local_manager.cleanup()
    local.logger = loggy

    scheduler = Scheduler.objects.create(
        content_type=ContentType.objects.get_for_model(dataset),
        object_id=dataset.pk,
        status=Scheduler.RUNNING,
        logger_name=logger_name,
    )

    wf_input_params = []
    wf_exec_results = []

    loggy.info("Processing dataset %s", unicode(dataset))

    try:
        file_meta = download_dataset(dataset)
        wf_input_params, wf_exec_results = \
            evaluate_dispatcher_and_run_workflow(scheduler, file_meta)
    except Exception, e:
        scheduler.status = Scheduler.FAIL
        scheduler.error = e.message

        loggy.exception('Process failure: %s', scheduler.error)
        if isinstance(e, IllegalRuleCheckSum):
            scheduler.status = Scheduler.INVALID
        else:
            raise
    else:
        # someone may have changed this status, write success only if not
        if scheduler.status == Scheduler.RUNNING:
            scheduler.status = Scheduler.SUCCESS
    finally:
        scheduler.in_params = json.dumps(wf_input_params)
        scheduler.out_params = json.dumps(wf_exec_results)
        scheduler.save()

    loggy.info('Workflow success')
    if indipendent:
        loggy.info(END)
    return True


LEVEL_LIST = ("WARNING", "ERROR", "INFO", "WARN", "DEBUG")
LEVEL_OUT = ("WARNING", "WARN", "ERROR")
SILK_LIB_PATH = os.path.join(
    settings.REPO_ROOT, 'data_acquisition', 'silk', 'lib')
SILK_JAR_PATH = os.path.join(
    settings.REPO_ROOT, 'data_acquisition', 'silk', 'silk.jar')


def __aggregator_process_archiveitem(
        aggregator_archive_item, scheduler, tmpdir, context):
    import envoy
    from django.template.loader import render_to_string
    from webui.cnmain.utils import get_virtuoso

    virtuoso_simple = get_virtuoso()
    virtuoso_master = get_virtuoso('master')
    loggy = local.logger

    aggregator = aggregator_archive_item.aggregator
    archive_item = aggregator_archive_item.archiveitem

    #
    # PART 1: generate XML file
    #

    loggy.debug("Processing " + unicode(archive_item))

    output_filename = None
    if not aggregator.silk_rule:
        loggy.warning('No silk rule found, skipping')
        scheduler.status = Scheduler.INCOMPLETE
    else:
        output_filename = os.path.join(
            tmpdir, archive_item.file_hash + '.nt'
        )
        conf_filename = os.path.join(
            tmpdir, archive_item.file_hash + '_conf.xml'
        )

        silk_conf_xml = render_to_string(
            'controller/aggregator/silk_rules.xml',
            dict(context, archive_item=archive_item,
                 output_filename=output_filename)
        )

        with open(conf_filename, 'w') as fconf:
            fconf.write(silk_conf_xml)

        #
        # PART 2: execute SILK
        #
        loggy.info("Executing SILK on %s", unicode(archive_item))
        result = envoy.connect(
            'java -Xmx{} -DconfigFile={} -Dthreads={} '
            '-cp "{}:{}/*" de.fuberlin.wiwiss.silk.Silk'.format(
                settings.SILK_SINGLE_MACHINE_HEAP,
                conf_filename,
                settings.SILK_SINGLE_MACHINE_THREADS,
                SILK_JAR_PATH,
                SILK_LIB_PATH,
            )
        )

        level = None
        status = 0
        titan_log_cnt = 0
        # pylint: disable=W0212
        while result._process.poll() is None:
            line = result._process.stderr.readline()\
                         .strip().replace('%', '%%')

            if not line:
                continue

            tmplevel = line.split(":", 1)[0]
            if tmplevel in LEVEL_LIST:
                level = tmplevel
            if line.startswith("Exception in thread"):
                level = "EXCEPTION"

            if level == "EXCEPTION":
                status = 2
                loggy.error("S> " + line)
            elif level in LEVEL_OUT:
                status = 1
                loggy.warn("S> " + line)
            elif re.search(r"Finished writing \d+ entities", line) or \
                    re.search(r"Got \d+ vertices", line) or \
                    re.search(r"Wrote \d+ links", line):
                loggy.info("S> " + line)
            elif re.search(r"Getting data for vertices", line):
                if titan_log_cnt % 200 == 0:
                    loggy.info("S> " + line)
                titan_log_cnt += 1
            # pylint: enable=W0212

        if status:
            loggy.error("SILK failed on %s", unicode(archive_item))
            scheduler.status = Scheduler.FAIL
            if status == 2:
                return
        else:
            loggy.info("SILK executed successfully")
            # loggy.debug("Generated file: %s", output_filename)

    #
    # PART 3: dump graph data
    #
    dump_dir = '{}/'.format(archive_item.file_hash)
    loggy.info("Creating a dump of the namedgraph {}".format(
        archive_item.datagraph_mapped_name))

    error = virtuoso_simple.dump_graph(
        archive_item.datagraph_mapped_name, dump_dir, create_dir=True)

    if error:
        loggy.error("Dump failed:")
        for line in error:
            loggy.error(line)
        raise Exception("Dump of the namedgraph failed: {}".format(
            error
        ))

    #
    # PART 4: load graph data in the master virtuoso instance
    #
    # we are assuming that the two virtuoso are on the same machine
    loggy.info("Loading dump in the master graph as {}".format(
        archive_item.datagraph_mapped_name))

    # clear the entire named database before ingesting the data
    # since we're on titan we don't want this anymore
    # virtuoso_master.clear(archive_item.datagraph_mapped_name)

    # loggy.warning("Leaving data dump available for testing purposes")
    # error = virtuoso_master.load_graphs(dump_dir, remove_dir=False)
    error = virtuoso_master.load_graphs(dump_dir, remove_dir=True)

    if error:
        loggy.error("Load failed:")
        if isinstance(error, basestring):
            loggy.error(error)
        else:
            for line in error:
                loggy.error(line)
        raise Exception("Load of the namedgraph failed: {}".format(
            error
        ))

    if aggregator.silk_rule:
        #
        # PART 5: load SILK generated tuples
        #
        loggy.info("Loading SILK generated tuples")
        virtuoso_master.ingest(
            output_filename,
            settings.TRIPLE_DATABASE['PREFIXES']['silk_graph'],
        )

    now = timezone.now()
    aggregator_archive_item.last_workflow_success = now
    if aggregator_archive_item.first_workflow_success is None:
        aggregator_archive_item.first_workflow_success = now
    aggregator_archive_item.save()


def _aggregator_process_archiveitems(
        aggregator_archiveitems, scheduler, tmpdir, context):
    for aggregator_archiveitem in aggregator_archiveitems:
        __aggregator_process_archiveitem(
            aggregator_archiveitem, scheduler, tmpdir, context
        )

# pylint: disable=R0912,R0914,R0915


@task
def process_aggregator(aggregator, force=False):
    """ execute the aggregator workflow: run silk on every archive item
     associated to the aggregator.
    """
    from tempfile import mkdtemp
    from webui.cnmain.utils import get_virtuoso_endpoint

    logger_name = process_aggregator.request.id
    loggy = get_redis_logger(logger_name)
    local_manager.cleanup()
    local.logger = loggy
    tmpdir = mkdtemp()
    scheduler = Scheduler.objects.create(
        content_type=ContentType.objects.get_for_model(aggregator),
        object_id=aggregator.pk,
        status=Scheduler.RUNNING,
        logger_name=logger_name,
    )

    try:
        loggy.info("Processing aggregator %s", unicode(aggregator))
        loggy.debug("Working dir: %s", tmpdir)

        context = {
            'aggregator': aggregator,
            'sd_prefix': settings.TRIPLE_DATABASE['PREFIXES']['sdv1'],
            'sparql_endpoint': get_virtuoso_endpoint(),
            'mastergraph_host': settings.TRIPLE_DATABASE_MASTER['HOST'],
            'mastergraph_port':
            settings.TRIPLE_DATABASE_MASTER['KWARGS']['rexpro_port'],
            'mastergraph_graphname':
            settings.TRIPLE_DATABASE_MASTER['KWARGS']['graph'],
            'resource_namespace':
            settings.TRIPLE_DATABASE_MASTER['PREFIXES']['sdres'],
        }

        loggy.info("Connecting to virtuoso")

        aggregator_archiveitems = aggregator.aggregatorarchiveitem_set\
            .all().order_by('first_workflow_success')

        if not force:
            res = []
            for aggregator_archiveitem in aggregator_archiveitems:
                if aggregator_archiveitem.needs_update():
                    res.append(aggregator_archiveitem)
                else:
                    loggy.info('Skipped archiveitem %s',
                               unicode(aggregator_archiveitem.archiveitem))

            aggregator_archiveitems = res

        _aggregator_process_archiveitems(
            aggregator_archiveitems, scheduler, tmpdir, context
        )

        loggy.info('Workflow completed')
    except Exception, e:
        loggy.exception('Generic exception in the workflow')
        scheduler.status = Scheduler.FAIL
        scheduler.error = e.message or str(e)
        # send the exception to sentry
        raise
    else:
        # someone may have changed this status, write success only if not
        if scheduler.status == Scheduler.RUNNING:
            scheduler.status = Scheduler.SUCCESS
    finally:
        # loggy.warning("Leaving the tempdir available for testing purposes")
        shutil.rmtree(tmpdir)
        scheduler.save()
        loggy.info(END)
# pylint: enable=R0912,R0914,R0915


class CustomRedirectHandler(urllib2.HTTPRedirectHandler):
    """
    Custom redirect to keep the original HTTP handler.

    http://stackoverflow.com/questions/4953487/how-do-i-access-the-original-
    response-headers-that-contain-a-redirect-when-using
    """

    def http_error_301(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.status = code
        result.redirect_headers = headers
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
        result.redirect_headers = headers
        return result

    def http_error_303(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_303(
            self, req, fp, code, msg, headers)
        result.status = code
        result.redirect_headers = headers
        return result
