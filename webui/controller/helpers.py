"""
Helpers
"""


class Scraperwiki(object):
    """
    This class helps creating scraperwiki urls. Can be created from SW url,
    scraper name and api key or from a source.
    """
    def __init__(self, scraperwiki_url, name, api_key=None):
        self.scraperwiki_url = scraperwiki_url.strip(' /')
        self.name = name
        if api_key:
            api_key = api_key.strip()
        self.api_key = api_key

    @classmethod
    def from_source(cls, source):
        """
        Alternative constructor
        """
        return cls(source.scraperwiki_url, source.scraper_name,
                   source.scraper_api_key)

    def scraper_url(self):
        return '{}/scrapers/{}'.format(
            self.scraperwiki_url, self.name
        )

    def scraper_api(self):
        return '{}/api/1.0/'.format(self.scraperwiki_url)

    def scraper_csv_api(self, table):
        from urllib import urlencode
        url = self.scraper_api() + '/datastore/sqlite?'

        args = {
            'format': 'csv',
            'query': 'select * from "{}"'.format(table),
            'name': self.name
        }

        if self.api_key:
            args['apikey'] = self.api_key

        url += urlencode(args)

        return url
