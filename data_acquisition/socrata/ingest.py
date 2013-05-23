#!/usr/bin/env python

from urllib import urlencode
from urlparse import urljoin

import sys
import argparse
import urllib2
import subprocess
import datetime
import re
import json


WGET = 'wget'
PSQL = 'psql'

URL_ID_EXTRACTOR_RE = re.compile(
    '^.+/views/([0-9a-z]{4}-[0-9a-z]{4})(/rows)?\.json$'
)
ID_PATTERN = re.compile('^[0-9a-z]{4}-[0-9a-z]{4}$')


class SocrataPostGresImporter():
    def __init__(self, conf):
        self._api_conf = conf['api']
        self._db_conf = conf['database']
        self._dataset_api = self.__new_dataset()
        self._datasets = None
        self._schema_created = False

    def describe(self, out=sys.stdout):
        datasets = self.__get_datasets()
        for result in datasets['results']:
            view = result['view']
            out.write('ID: %s NAME: %s PUBLISHED: %s\n' % (view['id'], view['name'], datetime.datetime.fromtimestamp(int(view['publicationDate'])).strftime('%Y-%m-%d %H:%M:%S')))
            out.write('LICENSE: %s\n' % view['license'])
            out.write('DOWNLOAD: %s\n' % self.__download_url(view))
            out.write('ATTRIBUTION: %s %s\n' % (view['attribution'], view['attributionLink'] if 'attributionLink' in view else ''))
            out.write('DESCRIPTION: %s\n' % view[
                      'description'] if 'description' in view else '')
            out.write('TAGS: %s\n' % view['tags']
                      if 'tags' in view else '')
            for col in view['columns']:
                out.write('\t\t %s (%s) - %s\n' % (
                    col['fieldName'], col['dataTypeName'], col['name']))

    # 'url', 'download', 'name', 'curator', 'license', 'description', 'tags',
    # 'bouding_box'
    def describe_json(self):
        datasets = self.__get_datasets()
        json_meta_list = []
        for result in datasets['results']:
            view = result['view']
            json_meta = {
                'url': '{}/api/views/{}.json'.format(
                    self._dataset_api.host, view['id']),
                'download': self.__download_url(view, 'json'),
                'name': view['name'],
                'curator': view['attribution'],
                'license': view['license']['termsLink'],
                'description': view[
                    'description'] if 'description' in view else '',
                'tags': view['tags'] if 'tags' in view else ''
            }

            json_meta_list.append(json_meta)
        return json_meta_list

    def get_views(self):
        views = []
        datasets = self.__get_datasets()
        for result in datasets['results']:
            views.append(result['view'])
        return views

    def get_sql_create_table(self, view):
        sql = 'CREATE TABLE {} ('.format(self.__table_name(view))
        fields = []
        for col in view['columns']:
            fields.append(
                '{} {}'.format(
                    self.__rewrite_name(col['fieldName']),
                    self.__rewrite_datatype(col['dataTypeName'])
                )
            )
        sql += ', '.join(fields) + ')'
        return sql

    def create_table(self, view):
        table_name = self.__table_name(view)
        sql_drop = 'DROP TABLE ' + table_name
        self.__execute_sql_command(sql_drop, False)
        sql_create = self.get_sql_create_table(view)
        self.__execute_sql_command(sql_create)
        print "WFOUT <tables> : <%s>" % self.__table_name_without_schema(view)
        return table_name

    def load_table(self, view):
        table_name = self.__table_name(view)
        print 'Loading table ' + table_name
        api = self.__download_url(view)
        command = '%s "%s" -O - | %s -d %s -c \'COPY %s FROM STDIN WITH CSV HEADER\'' %\
            (WGET, api, PSQL, self._db_conf['db'], table_name)
        print 'Executing command: [', command, ']'
        exit_code = subprocess.call(command, shell=True)
        if exit_code != 0:
            raise Exception(
                'Error while ingesting CSV with command [' + command + ']')
        print 'Loading completed'

    def ingest_view(self, view):
        self.__create_schema_once()
        print '=' * 15 + 'Processing view:', view['id'] + '=' * 15
        self.create_table(view)
        self.load_table(view)
        print 'Process completed'

    # rows_url like https://dati.lombardia.it/api/views/xy9p-k9bj.json
    def ingest_view_from_url(self, view_url):
        dataset_api = self.__new_dataset()
        id_match = URL_ID_EXTRACTOR_RE.match(view_url)
        if not id_match:
            raise Exception('Invalid view_url: ' + view_url)
        dataset_api.use_existing(id_match.group(1))
        view = dataset_api.metadata()
        self.ingest_view(view)

    def ingest_views(self, limit=None):
        views = self.get_views()
        views_count = 0
        for view in views:
            self.ingest_view(view)
            views_count += 1
            if limit is not None and views_count == limit:
                break
        print 'Ingestion of ', views_count, 'views completed.'
        print

    def __new_dataset(self):
        api_conf = self._api_conf

        return Dataset(
            api_conf['host'], api_conf['user'], api_conf['passwd'],
            api_conf['token']
        )

    # https://dati.lombardia.it/api/search/views.json
    def __get_datasets(self):
        if self._datasets == None:
            print 'Querying dataset API ...'
            self._datasets = self._dataset_api.find_datasets()
            print 'Done'
        return self._datasets

    def __execute_sql_command(self, sql, verify=True):
        print 'Executing command:', '[', sql, ']'
        command = '%s -d %s -c \'%s\'' % (PSQL, self._db_conf['db'], sql)
        exit_code = subprocess.call(command, shell=True)
        if verify and exit_code != 0:
            raise Exception(
                'Error while executing SQL command [' + command + ']')
        print 'Command completed'

    def __table_name_without_schema(self, view):
        return self.__rewrite_name(view['name'])

    def __table_name(self, view):
        schema = self._db_conf['schema']
        return ('' if schema is None else '"' + schema + '".') + '"' + self.__table_name_without_schema(view) + '"'

    def __download_url(self, view, format='csv'):
        return '%s/api/views/%s/rows.%s' % (self._dataset_api.host, view['id'], format)

    def __rewrite_name(self, name):
        return name.replace('"', '').replace('\'', '')

    def __rewrite_datatype(self, datatype):
        if 'number' == datatype:
            return 'numeric'
        if 'location' == datatype or 'percent' == datatype:
            return 'text'
        return datatype

    def __create_schema_once(self):
        if not self._schema_created:
            sql_schema_create = 'CREATE SCHEMA ' + self._db_conf['schema']
            print 'WFOUT <schema> : <%s>' % self._db_conf['schema']
            self.__execute_sql_command(sql_schema_create, False)
            self._schema_created = True



# Taken from https://raw.github.com/socrata/socrata-python/master/Socrata.py
class Dataset(object):
    def __init__(self, host=None, user=None, passwd=None, token=None):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.token = token

    # Call the search service with optional params
    def find_datasets(self, params=None):
        if params is None:
            params = {}
        sets = self._request("/api/search/views.json?%s" % urlencode(params))
        return sets

    def metadata(self):
        return self._request("/views/{0}.json".format(self.id))

    def is_id(self, id):
        return ID_PATTERN.match(id) is not None

    def use_existing(self, id):
        if self.is_id(id):
            self.id = id
        else:
            raise Exception('Invalid id [%s]' % id)

    def _request(self, service, content_type='application/json'):
        uri = urljoin(self.host, service)
        headers = {'Content-type': content_type, 'X-App-Token': self.token}
        http_handler = urllib2.HTTPBasicAuthHandler()
        http_handler.add_password(None, uri, self.user, self.passwd)
        opener = urllib2.build_opener(http_handler)
        opener.addheaders.append(headers)
        urllib2.install_opener(opener)
        handler = urllib2.urlopen(uri)
        content = handler.read()
        if content is not None and len(content) > 0:
            response_parsed = json.loads(content)
            if hasattr(response_parsed, 'has_key') and 'error' in \
                    response_parsed and response_parsed['error'] is True:
                raise Exception("Error: %s" % response_parsed['message'])
            else:
                return response_parsed
        raise Exception('Request returned empty response')

if __name__ == '__main__':
    import json

    parser = argparse.ArgumentParser(description='Handle Socrata API.')
    parser.add_argument(
        'conf', type=str, help='Tool JSON configuration')
    parser.add_argument('--describe', action='store_true',
                        help='Show human readable description for the API.')
    parser.add_argument(
        '--describejson',
        action='store_true',
        help='Show JSON metadata for the API compatible with the SW Meta '
             'table.'
    )
    parser.add_argument('--importer', action='store_true',
                        help='Import all portal data into PostGres.')
    parser.add_argument('--urlimporter', action='store_true',
                        help='Import specified dataset URL into PostGres.')
    parser.add_argument('--url', type=str,
                        help='The urlimporter target URL')
    args = parser.parse_args()

    conf = json.loads(args.conf)
    importer = SocrataPostGresImporter(conf)
    if args.describe:
        importer.describe()
    elif args.describejson:
        print json.dumps(importer.describe_json())
    elif args.importer:
        importer.ingest_views()
    elif args.urlimporter:
        if not args.url:
            raise Exception('--urlimporter requires --url option')
        importer.ingest_view_from_url(args.url)
    else:
        parser.print_help()
    sys.exit(0)
