""" Download, convert compression and ingest a single RDF file into Virtuoso
"""
import os
import sys
import shutil
import urllib2
from tempfile import mkdtemp

import envoy

webuidir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, webuidir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'webui.settings'

from data_acquisition.utils import print_error_result
from webui.cnmain.utils import get_virtuoso


def main(args):
    """ the body of the script
    """
    tmpdir = mkdtemp()

    if args.file.startswith(('http://', 'https://')):
        print "The file is in the net, downloading it..."
        file_basename = os.path.basename(
            urllib2.urlparse.urlsplit(args.file).path
        )

        result = envoy.run('wget "{}" -O {}'.format(args.file, file_basename))

        if result.status_code:
            print_error_result(
                result, "Error while downloading RDF data {}. Aborting".format(
                    args.file
                )
            )
            exit(1)

        filename = os.path.join(
            tmpdir, file_basename
        )
    else:
        print "The file is  local, moving it..."
        shutil.copy(args.file, tmpdir)
        filename = os.path.join(tmpdir, os.path.basename(args.file))

    print "handling file", filename

    filename_cropped, extension = os.path.splitext(filename)
    if extension == '.bz2':
        print "Got a bz2 file, need to convert it with gzip"
        gzip_filename = filename_cropped + '.gz'

        result = envoy.run('bunzip2 "{}" -c | gzip > "{}'.format(
            filename, gzip_filename
        ))

        if result.status_code:
            print_error_result(result, "Error while converting file, aborting")
            exit(2)

        filename = gzip_filename
        print "File converted successfully, now handling", filename

    print "Ingesting file in virtuoso"
    virtuoso = get_virtuoso()
    virtuoso.clear(args.graph)
    print "Ingestion completed", virtuoso.ingest(filename, graph=args.graph)
