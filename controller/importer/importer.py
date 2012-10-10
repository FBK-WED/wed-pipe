#!/usr/bin/env python

import sys, os
import traceback

_candidate_insert = os.path.dirname(os.path.realpath(__file__)) + '/../'
if not _candidate_insert in sys.path:
    sys.path.insert(0, _candidate_insert)

from webui.controller.models import Source, Dataset
from django.conf import settings

import json
import urllib2
import csv

class MetadataImporter:
    """
    Loads datasets from ScraperWiki or CSV dump.
    """

    BOUNDED = ('url', 'download', 'name', 'curator', 'license', 'description', 'tags', 'bounding_box')

    def read_metadata(self, source_name, scraper_name, api_key=None):
        """
        Reads metadata from a scraper for a specified source.
        """

        request_url = settings.SCRAPERWIKI_API + 'datastore/sqlite?format=jsondict&name={0}&query=select%20*%20from%20%60{1}%60'.format(
            scraper_name, settings.METADATA_TABLE
        )
        if api_key: request_url = request_url + '&apikey=' + api_key
        print 'REQUEST URL', request_url
        data_list = json.load( urllib2.urlopen(request_url) )
        if type(data_list) == dict: 
            raise Exception('Obtained error', repr(data_list))
        source = Source.objects.get(name=source_name)
        errors = []
        total  = 0
        for list_elem in data_list:
            try:
                total += 1
                dataset = Dataset()
                dataset.source       = source
                dataset.url          = list_elem[ self.BOUNDED[0] ].strip()
                dataset.download     = list_elem[ self.BOUNDED[1] ].strip()
                if dataset.download is None:
                    raise Exception('Dataset %s does not define a valid download URL' % dataset.url )
                dataset.name         = list_elem[ self.BOUNDED[2] ].strip()
                dataset.curator      = list_elem[ self.BOUNDED[3] ].strip()
                dataset.license      = list_elem[ self.BOUNDED[4] ].strip()
                dataset.description  = list_elem[ self.BOUNDED[5] ].strip() if list_elem.has_key(self.BOUNDED[5]) else None
                dataset.tags         = list_elem[ self.BOUNDED[6] ].strip() if list_elem.has_key(self.BOUNDED[6]) else None
                dataset.bounding_box = list_elem[ self.BOUNDED[7] ].strip() if list_elem.has_key(self.BOUNDED[7]) else None
                dataset.other_meta   = json.dumps( self._get_unbounded(list_elem) )
                dataset.save()
            except Exception as e:
                traceback.print_exc(file=sys.stderr)
                errors.append(repr(e))
        return { 'total' : total, 'errors' : len(errors), 'report' : errors }

    def read_csv(self, source_name, csv_stream):
        """
        Reads metadata from a CSV for a specified source name.
        """

        reader = csv.reader(csv_stream, delimiter='\t', quotechar='"')
        source = Source.objects.get(name=source_name)
        errors = []
        total  = 0

        for row in reader:
            if len(row) == 0: continue
            try:
                total += 1
                dataset = Dataset()
                dataset.source       = source
                print 'ROW: ', repr(row)
                dataset.url          = row[0].strip()
                dataset.download     = row[1].strip()
                dataset.name         = row[2].strip()
                dataset.description  = row[3].strip()
                dataset.tags         = row[4].strip()
                dataset.curator      = row[5].strip()
                dataset.license      = row[6].strip()
                dataset.bounding_box = row[7].strip()
                dataset.other_meta   = row[8].strip()
                dataset.save()
            except Exception as e:
                traceback.print_exc(file=sys.stderr)
                errors.append(repr(e))
        return { 'total' : total, 'errors' : len(errors), 'report' : errors }

    def _get_unbounded(self, list_elem):
        unbounded = {}
        for key in list_elem:
            if not key in self.BOUNDED:
                unbounded[key] = list_elem[key]
        return unbounded

def help():
    """
    Module CLI help.
    """

    print 'Usage:', sys.argv[0], '<source-name>', '<scraper-name>'

if __name__ == "__main__":
    if( len(sys.argv) != 3):
        help()
        sys.exit(1)
    try:
        importer = MetadataImporter()
        report = importer.read_metadata(sys.argv[1], sys.argv[2])
        print repr(report)
    except Exception as e:
        print 'Error while running importer:', e
        help()
        sys.exit(1)
