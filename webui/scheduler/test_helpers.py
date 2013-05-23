""" utilities for testing the workflow
"""
import os
from mock import patch
import util

from webui.scheduler.tasks import md5_for_file


def _get_downloaded_file(filename):
    """ given a test filename, return the file_meta dictionary needed by
      the workflow. Used for tests.
    """
    if filename:
        from util import get_test_file
        csv_file = get_test_file(
            filename, 'scheduler'
        )

        magic_type = util.MS.file(csv_file)
        return {
            'out_file': csv_file,
            'file_name': filename,
            'file_size': os.path.getsize(csv_file),
            'content_type': 'text/csv',
            'md5sum': md5_for_file(csv_file),
            'magic_type': util.magic_to_mime(magic_type),
        }

    print
    print '*' * 80
    print "WARNING"
    print '*' * 80
    print "When testing the workflow, you should set what to do with " \
          "each source you're dealing with. Check " \
          "webui.scheduler.test_helpers.py"
    print '*' * 80
    print
    return {}


def mocked_download_csv_from_scraperwiki(api_url, table, save_dir):
    """ mock of _download_csv_from_scraperwiki
    """
    filename = None
    if table == 'trentinocultura':
        filename = 'trentinocultura.csv'
    # elif table == 'something-else':
    #     filename = 'somethingelse.csv'
    return _get_downloaded_file(filename)


def mocked_download_url(url, save_dir):
    """ mock of webui.scheduler.tasks._download_url
    """
    filename = url.rsplit('/', 1)[-1]
    return _get_downloaded_file(filename)


class WorkflowTestRunner(object):
    @patch('webui.scheduler.tasks._download_url', mocked_download_url)
    @patch('webui.scheduler.tasks._download_csv_from_scraperwiki',
           mocked_download_csv_from_scraperwiki)
    def _loaddevdata(self, *args, **kwargs):
        super(WorkflowTestRunner, self)._loaddevdata(*args, **kwargs)

    @patch('webui.scheduler.tasks._download_url', mocked_download_url)
    @patch('webui.scheduler.tasks._download_csv_from_scraperwiki',
           mocked_download_csv_from_scraperwiki)
    def run_tests(self, *args, **kwargs):
        super(WorkflowTestRunner, self).run_tests(*args, **kwargs)
