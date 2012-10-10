#!/usr/bin/python

#
# This script takes the PAT Geo Catalog index page and downloads all the declared resources.
#

import os, sys
import lxml.html
import urllib2
import argparse
import re

GATEWAY = 'http://www.territorio.provincia.tn.it/portal/server.pt/gateway/PTARGS_0_18720_2521_862_0_43/http%3B/172.20.3.95%3B8380/geoportlet/'

from multiprocessing import Process

def download_url(url, save_dir):
    file_name = url.split('/')[-1]
    data_stream = urllib2.urlopen(url)
    output = open(save_dir + '/' + file_name, 'wb')
    meta = data_stream.info()
    file_size = int( meta.getheaders("Content-Length")[0] )
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
        status = status + chr(8)*(len(status)+1)
        print status,
    output.close()

def extract_page_metadata(page_content):
    dom = lxml.html.fromstring(page_content)
    link_re = re.compile('getGatewayedAction\(\'([^\']+)\'\)')
    result = []
    for tr in dom.cssselect('tr'):
        h1_list = tr.cssselect('h1')
        if not h1_list: continue
        title       = h1_list[0].text.strip().replace('\n', '')
        description = tr.cssselect('h2')[0].text.strip().replace('\n', '')
        meta_clk    = tr.cssselect('.button' )[0].get('onclick')
        xml_url     = tr.cssselect('.button1')[0].get('href').strip()
        zip_url     = tr.cssselect('.button1')[1].get('href').strip()
        rdf_url     = tr.cssselect('.button1')[2].get('href').strip()
        curator     = tr.cssselect('span')[0].text.strip()
        tags        = tr.cssselect('span')[1].text.strip()
        license_src = tr.cssselect('img')[1].get('src')
        if tags : tags = ','.join( map(lambda(tag): tag.strip(), tags.split(',') ) )
        meta_url = GATEWAY + link_re.findall(meta_clk)[0]
        license  = license_src[ license_src.rfind('/') + 1: license_src.rfind('.') ]
        result.append({
            'title'       : title,
            'description' : description,
            'meta_clk'    : meta_clk,
            'xml_url' : xml_url, 'zip_url' : zip_url, 'rdf_url' : rdf_url,
            'curator' : curator,
            'tags'    : tags.split(','),
            'meta_url': meta_url,
            'license' : license
        })
    return result

def process_index(index_content, save_dir, csv):
    processes = []
    if(csv): print '# ' + '\t'.join(['url', 'download', 'name', 'description', 'tags', 'curator', 'license', 'bounding_box', 'other_meta'])
    for record in extract_page_metadata(index_content):
        if csv:
            tags = ','.join(record['tags'])
            try:
                print u'\t'.join(map(lambda(e): u'"%s"' % e, [record['meta_url'], record['zip_url'], record['title'], record['description'], tags, record['curator'], record['license'], '1,2,3,4', '{}']))
                print u'\t'.join(map(lambda(e): u'"%s"' % e, [record['meta_url'], record['xml_url'], record['title'], record['description'], tags, record['curator'], record['license'], '1,2,3,4', '{}']))
                print u'\t'.join(map(lambda(e): u'"%s"' % e, [record['meta_url'], record['rdf_url'], record['title'], record['description'], tags, record['curator'], record['license'], '1,2,3,4', '{}']))
            except:
                print >> sys.stderr, 'Error while printing line: ', meta_url, rdf_url.strip(), title.strip(), description, tags, curator, license
        else:
            for url in [zip_url, xml_url, rdf_url]:
                p = Process(target=download_url, args=(url,save_dir,))
                p.start()
                processes.append(p)
                for proc in processes:
                    proc.join()

def main():
    parser = argparse.ArgumentParser(description='Downloads the territorial data from PAT.')
    parser.add_argument('-i', '--index_file', action='store'     , help='The input index file', required=True)
    parser.add_argument('-s', '--save_dir'  , action='store'     , help='The output archive dir')
    parser.add_argument('-c', '--csv'       , action='store_true', help='If specified produces a CSV of the parsed data')
    args = parser.parse_args()

    if args.save_dir == None and args.csv == None:
        raise Exception('Either save_dir or csv must be specified.')

    index = open(args.index_file)
    index_str = index.read()
    index.close()

    if not args.csv: os.mkdir(args.save_dir)
    process_index(index_str, args.save_dir, args.csv)

if __name__ == '__main__':
    main()