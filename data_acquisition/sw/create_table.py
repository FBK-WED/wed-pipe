#!/usr/bin/python

#
# Creates a table for storing the data provided by a ScraperWiki scraper.
#

SCRAPERWIKI_API = 'https://api.scraperwiki.com/api/1.0/'

import sys
import urllib
import json

def help():
	print sys.argv[0], '<scraper>', '<table>'
	sys.exit(1)

if( len(sys.argv) != 3 ): help()

scraper= sys.argv[1]
table  = sys.argv[2]

filehandle = urllib.urlopen(SCRAPERWIKI_API + 'scraper/getinfo?&name=' + scraper)
data = json.load(filehandle)
print data[0]["datasummary"]["tables"]["swdata"]["sql"].replace('`', '"').replace('text','varchar').replace('"swdata"', table)

sys.exit(0)
