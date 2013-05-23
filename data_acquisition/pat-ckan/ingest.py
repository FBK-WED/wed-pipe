#!/opt/local/bin/python
# -*- coding: utf-8 -*-

"""
@author Michele Mostarda (mostarda@fbk.eu)

This script is responsible for downloading data from the Portale Geocartografico Trentino
(http://www.territorio.provincia.tn.it) and ingest it into a CKAN instance.
"""

import os
import re
import traceback

import urllib2
import sys
import libxml2
import json
import zipfile
import requests
import time
import ckanclient

from  ogr2reclinejs import OGR2Reclinejs


_candidate_path = os.path.dirname(os.path.realpath(__file__)) + '/../pat'
if not _candidate_path in sys.path:
    sys.path.insert(0, _candidate_path)

from download_data import download_index, extract_page_metadata

WORK_DIR = 'work/'

INDEX_FILE = 'index.html'

XPATH_RULES = 'xpath_rules.lst'

# CKAN host URL
CKAN_HOST    = 'http://localhost:5000'
# CKAN API key
CKAN_API_KEY = 'c4d48e00-5689-4a5d-892a-24302519c0cb'

# patched ckanclient functions for upload
def _post_multipart(self, selector, fields, files):
    '''Post fields and files to an http host as multipart/form-data.

    :param fields: a sequence of (name, value) tuples for regular form
        fields
    :param files: a sequence of (name, filename, value) tuples for data to
        be uploaded as files

    :returns: the server's response page

    '''

    from urlparse import urljoin, urlparse

    content_type, body = self._encode_multipart_formdata(fields, files)

    headers = self._auth_headers()
    url = urljoin(self.base_location + urlparse(self.base_location).netloc, selector)
    req = requests.post(url, data=dict(fields), files={files[0][0]: files[0][1:]}, headers=headers)
    return req.status_code, req.error, req.headers, req.text

# FIXME: monkey patching
ckanclient.CkanClient._post_multipart = _post_multipart

def download_url(url, file_name):
    data_stream = urllib2.urlopen(url)
    output = open(file_name, 'wb')
    meta = data_stream.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)
    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = data_stream.read(block_sz)
        if not buffer:
            break
        file_size_dl += len(buffer)
        output.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8) * (len(status) + 1)
        print status,
    output.close()


def unzip(file, out_dir):
    zfile = zipfile.ZipFile(file)
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    for name in zfile.namelist():
        fd = open(out_dir + '/' + name, "w")
        fd.write(zfile.read(name))
        fd.close()


def ingest_dataset(title, xml_url, tags=[]):
    prefix = xml_url.replace('.xml', '')
    rdf_url = prefix + '.rdf'
    zip_url = prefix + '.zip'
    xml_resource = xml_url[xml_url.rfind('/') + 1:]
    resource = xml_resource.replace('.xml', '')
    dataset_name = re.sub('[^\w_-]', ' ', resource.lower()).replace('\'', '')[:85]
    dataset_name = dataset_name + '_' + str(time.time()).replace('.', '')
    tags = map(lambda t: re.sub('[^-_.\w]', ' ', t).decode('utf-8'), tags)

    try:
        os.mkdir(WORK_DIR)
    except: pass

    # Download XML metadata
    xml_file = WORK_DIR + xml_resource
    print 'XMLFILE', xml_file
    download_url(xml_url, xml_file)

    # Download Zip
    zip_file = WORK_DIR + resource + '.zip'
    print 'ZIPFILE', zip_file
    download_url(zip_url, zip_file)

    # Extract metadata JSON
    dom = libxml2.parseFile(xml_file)
    ctxt = dom.xpathNewContext()
    ctxt.xpathRegisterNs("gmd", "http://www.isotc211.org/2005/gmd")
    ctxt.xpathRegisterNs("gml", "http://www.opengis.net/gml/3.2")
    ctxt.xpathRegisterNs("gco", "http://www.isotc211.org/2005/gco")
    ctxt.xpathRegisterNs("xlink", "http://www.w3.org/1999/xlink")

    # Compose metadata
    metadata = {}
    with open(XPATH_RULES, 'r') as rules:
        for rule in rules:
            try:
                desc, xpath = rule.split('|')
                matches = ctxt.xpathEval(xpath)
                for match in matches:
                    #print 'DESC', desc
                    #print 'VALUE', match.content.strip()
                    metadata[desc.decode('utf-8')] = match.content.strip().decode('utf-8')
            except Exception as e:
                print 'ERROR while processing line [%s]' % rule, e

    # Decompress Zip
    decompressed_zip_dir = zip_file + '_unzip'
    unzip(zip_file, decompressed_zip_dir)

    # Convert zip/shp files to CSV
    csv_file = None # TODO: manage more than once
    for file in os.listdir(decompressed_zip_dir):
        if file.endswith(".shp"):
            shp_file = decompressed_zip_dir + '/' + file
            print 'Converting file ...', shp_file
            ogr2reclinejs = OGR2Reclinejs(shp_file, True)
            ogr2reclinejs.conversion(WORK_DIR)
            csv_file = WORK_DIR + file.replace('.shp', '.csv')
    csv_file = os.path.abspath(csv_file)
    print 'CSV FILE:', csv_file

    # Create Dataset
    # http://docs.ckan.org/en/ckan-1.7/api-v2.html#model-api
    payload = {
        u'name': dataset_name,
        u'title': title,
        u'notes': metadata['Informazioni di Identificazione: Descrizione'],
        u'notes_rendered': metadata['Informazioni di Identificazione: Descrizione'],
        u'groups' : ['geodati'],
        u'url': u'http://www.territorio.provincia.tn.it/',
        u'author': metadata['Informazioni di Identificazione: Nome dell\'Ente'],
        u'author_email': metadata['Informazioni di Identificazione: E-mail'],
        u'maintainer': metadata['Informazioni sulla Distribuzione: Distributore: Nome dell\'Ente'],
        u'maintainer_email': metadata['Informazioni sulla Distribuzione: Distributore: E-mail'],
        u'tags': tags,
        u'extras': metadata,
        u'isopen': True,
        u'license': u'Creative Commons CCZero',
        u'license_id': u'cc-zero',
        u'license_title': u'Creative Commons CCZero',
        u'license_url': u'http://creativecommons.org/publicdomain/zero/1.0/deed.it'
    }

    print 'DATASET NAME:', dataset_name
    print 'TITLE:', title

    ckan = ckanclient.CkanClient(
        base_location=CKAN_HOST + '/api',
        api_key=CKAN_API_KEY
    )

    ckan.package_register_post(payload)
    ckan.package_entity_get(payload['name'])
    print 'Metadata creation response:', ckan.last_message

    #headers = {'Authorization': CKAN_API_KEY, 'Content-Type' : 'application/json;charset=utf-8'}
    #response = requests.post(
    #    "%s/api/rest/dataset" % CKAN_HOST,
    #    data=json.dumps(payload),
    #    headers=headers
    #)
    #print 'Metadata Creation Response:', response.text
    #response_json = json.loads(response.text)
    #id = response_json['id']
    #print 'Dataset ID:', id

    # Upload file to FileStore and create resource
    upload_data = ckan.upload_file(csv_file)
    upload_url = upload_data[0].replace('http://', CKAN_HOST)
    print 'Upload URL:', upload_url
    r = ckan.add_package_resource(dataset_name, upload_url, resource_type='data', format='csv')
    print 'Add package resource response:', json.dumps(r)
    #resource_id = r['resources'][-1]['id']

    # wait_for_mapping(resource_id)

    # Upload file to DataStore
    #data_api = '%s/api/data/%s' % (CKAN_HOST, resource_id)
    #print 'DATA API:', data_api
    #client = ckanclient.datastore.DataStoreClient(data_api)
    #client.upload(filepath_or_fileobj=csv_file, filetype='csv')
    #print 'Datastore Upload complete'

    r = ckan.add_package_resource(dataset_name, xml_url, name='Metadati in formato XML', resource_type='metadata', format='xml')
    print 'Add XML resource response:', r

    r = ckan.add_package_resource(dataset_name, rdf_url, name='Dati in formato RDF', resource_type='data', format='rdf')
    print 'Add RDF resource response:', r

    r = ckan.add_package_resource(dataset_name, zip_url, name='Dati in formato Shapefile', resource_type='data', mimetype_inner='application/shp', format='zip')
    print 'Add ZIP resource response:', r

def wait_for_mapping(id):
    res = CKAN_HOST + '/elastic/ckan-patkan/%s/_mapping' % id
    print 'Waiting for mapping', res
    while(True):
        time.sleep(3)
        try:
            try:
                urllib2.urlopen(res)
                break
            except urllib2.HTTPError as e:
                print e
            #response = json.loads( request.read() )
            #print 'RESPONSE', response
            #if response['status'] == 200: break
            #content_type = request.headers['content-type']
            #if content_type == 'text/csv':
            #    break
            #else:
            #    print 'FOUND CONTENT TYPE:', content_type
        except Exception:
            print 'ERROR while waiting for content type'
            traceback.print_exc(file=sys.stderr)
    print 'Wait for resource %s completed' % res

def main():
    import os
    index = os.path.join(WORK_DIR, INDEX_FILE)
    if not os.path.exists(index):
        download_index(index)

    index_content = file(index).read()
    metadata = extract_page_metadata(index_content)
    for record in metadata:
        dataset_name = record['title']
        dataset_name = dataset_name[0].upper() + dataset_name[1:]
        try:
            print 'Ingesting Data:', dataset_name
            ingest_dataset(dataset_name, record['xml_url'], record['tags'])
            print 'Process completed'
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            print 'ERROR while processing dataset [%s] : %s' % (dataset_name, e)

if __name__ == '__main__':
    main()
