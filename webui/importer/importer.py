from contextlib import closing
import logging
import simplejson as json
import urllib2

from django.conf import settings
from taggit.utils import parse_tags

from webui.controller.models import Source, Dataset


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# The Table URI is expected to be written as: scraper:<scraper-name
# >:<table-name>
SCRAPER_PROTOCOL = 'scraper:'
TABLE_PROTOCOL = 'table://'


def _get_scraper_uri_parts(table_uri):
    return table_uri[len(SCRAPER_PROTOCOL):].split(':')


def get_scraper_name(table_uri):
    return _get_scraper_uri_parts(table_uri)[0]


def get_table_name(table_uri):
    try:
        return _get_scraper_uri_parts(table_uri)[1]
    except Exception as e:
        raise Exception('Error while parsing scraper URI: ' + repr(e))


def get_table_name_from_scraper(table):
    if table.startswith(TABLE_PROTOCOL):
        return table[len(TABLE_PROTOCOL):]
    if table.startswith(SCRAPER_PROTOCOL):
        return get_table_name(table)
    raise Exception('Unsupported table protocol: ' + table)


class MetadataImporter(object):
    """
    Loads datasets from ScraperWiki or CSV dump.
    """

    BOUNDED = ('url', 'download', 'name', 'curator', 'license',
               'description', 'tags', 'bounding_box')

    @staticmethod
    def get_metadata_of_scraper(scraperwiki_url, scraper_name, api_key):
        request_url = scraperwiki_url + '/api/1.0/' +\
            'datastore/sqlite?format=jsondict&name={0}&query=select%20'\
            '*%20from%20%60{1}%60'.format(
                scraper_name, settings.METADATA_TABLE
            )

        if api_key and len(api_key) > 0:
            request_url = request_url + '&apikey=' + api_key

        with closing(urllib2.urlopen(request_url)) as page:
            return json.load(page)

    @classmethod
    def read_metadata(cls, source):
        """
        Reads metadata from a scraper for a specified source.
        """
        if not source.scraper_name or not source.scraperwiki_url:
            return

        scraper_name = source.scraper_name
        api_key = source.scraper_api_key.strip() \
            if source.scraper_api_key else ''
        scraperwiki_url = source.scraperwiki_url.rstrip('/')

        data_list = cls.get_metadata_of_scraper(
            scraperwiki_url, scraper_name, api_key
        )

        if isinstance(data_list, dict):
            raise Exception('Obtained error', repr(data_list))

        errors = []
        total = 0
        bounded = cls.BOUNDED
        for list_elem in data_list:
            stripped = lambda i: list_elem[bounded[i]].strip()
            stripped_or_none = lambda i: stripped(i)\
                if bounded[i] in list_elem else None

            try:
                total += 1
                dataset = Dataset()
                dataset.source = source
                dataset.url = stripped(0)

                download = stripped(1)
                if download is None:
                    raise Exception(
                        'Dataset %s does not define a valid download URL' %
                        dataset.url
                    )
                if download.startswith('http:'):
                    dataset.download = download
                else:
                    dataset.download = '{}{}:{}'.format(
                        SCRAPER_PROTOCOL,
                        scraper_name,
                        get_table_name_from_scraper(stripped(1))
                    )

                dataset.name = stripped(2)
                dataset.curator = stripped(3)
                dataset.license = stripped(4)
                dataset.description = stripped_or_none(5)
                dataset.tags = stripped_or_none(6)
                dataset.bounding_box = stripped_or_none(7)
                dataset.other_meta = json.dumps(cls._get_unbounded(list_elem))
                dataset.save()
            except Exception as e:
                logger.exception('Invalid dataset')
                errors.append(repr(e))
        return {'total': total, 'errors': len(errors), 'report': errors}

    @staticmethod
    def read_csv(source, csv_stream):
        """
        Reads metadata from a CSV for a specified source name.
        """
        if not isinstance(source, Source):
            source = Source.objects.get(name=source)

        from csvkit import CSVKitReader
        rows = list(CSVKitReader(csv_stream, delimiter='\t'))
        fields = dict(enumerate(rows[0]))

        errors = []
        for row in rows[1:]:
            try:
                data = {fields[idx]: value for idx, value in enumerate(row)}
                tags = data.pop('tags', None)
                dataset = Dataset(**data)
                dataset.source = source
                dataset.save()

                if tags:
                    dataset.tags.add(*parse_tags(tags))
            except Exception, e:
                logger.exception('Cannot import a dataset from CSV')
                errors.append(repr(e))

        return {
            'total': len(rows) - 1,
            'errors': len(errors),
            'report': errors
        }

    @classmethod
    def _get_unbounded(cls, list_elem):
        unbounded = {}
        for key in list_elem:
            if not key in cls.BOUNDED:
                unbounded[key] = list_elem[key]
        return unbounded
