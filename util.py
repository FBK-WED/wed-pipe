"""
Utility functions module.
"""
from django.conf import settings

__author__ = 'mostarda'

import magic
import os
import zipfile
import shutil

from django.core.exceptions import ValidationError

MS = magic.open(magic.MAGIC_NONE)
MS.load()


def magic_to_mime(magic):
    magic_lower = magic.lower()
    print 'MAGIC: ', magic_lower
    if magic is None:
        return None
    if '7-zip archive' in magic_lower:
        return 'archive/7zip'
    elif 'zip archive' in magic_lower:
        return 'archive/zip'
    elif 'pdf document' in magic_lower:
        return 'application/pdf'
    elif 'application: microsoft excel' in magic_lower:
        return 'application/excel'
    elif 'dbase 3 data file' in magic_lower:
        return 'application/dbf'
    elif 'utf-8 unicode text' in magic_lower or 'ascii text' in magic_lower:
        return 'text/plain'
    else:
        return None


def to_handler_function(handler_code, func_name):
    return 'def __{funname}():\n{body}'.format(
        funname=func_name,
        body='\n'.join('\t' + line for line in handler_code.split('\n'))
    )


def validate_handler(handler, func_name):
    try:
        compile(to_handler_function(handler, func_name), '<string>', 'exec')
    except Exception as e:
        raise ValidationError(
            'Error while validating dispatcher code'.format(handler), e
        )


def decompress(file_meta):
    archive = file_meta['out_file']
    expanded_archive = archive + '__exp'
    file_name = os.path.basename(archive)
    dest_file = os.path.join(expanded_archive, file_name)
    magic_type = file_meta['magic_type']

    # try to delete the extraction directory
    shutil.rmtree(expanded_archive, ignore_errors=True)
    # ... and then recreate the directory
    os.mkdir(expanded_archive)

    if magic_type == 'archive/zip':
        zip_ = zipfile.ZipFile(archive)
        zip_.extractall(expanded_archive)
        return expanded_archive
    elif magic_type == 'archive/7zip':
        shutil.move(archive, expanded_archive)
        cmd = os.system(
            "cd '%s' && 7zr e '%s'" % (expanded_archive, dest_file)
        )
        if cmd != 0:
            raise Exception('Error while decompressing archive')
        os.remove(dest_file)
        return expanded_archive
    else:
        raise Exception('Unsupported archive magic type: ' + magic_type)


def delete_file_silently(file):
    try:
        os.remove(file)
    except:
        pass


class AttrDict(dict):
    """A dictionary with attribute-style access. It maps attribute access to
    the real dictionary."""

    def __init__(self, init={}):
        dict.__init__(self, init)

    def __getstate__(self):
        return self.__dict__.items()

    def __setstate__(self, items):
        for key, val in items:
            self.__dict__[key] = val

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, dict.__repr__(self))

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def copy(self):
        ch = AttrDict(self)
        return ch


def get_test_file(filename, app_name='cnmain'):
    """ return a test data file, assuming it's located in
    /webui/<app_name>/tests/data/<filename>
    """
    return os.path.join(
        settings.PROJECT_ROOT, app_name, 'tests', 'data', filename
    )


def rreplace(a_str, old, new, maxreplace=None):
    """ same as str.replace, but reversed
    (makes sense only if maxreplace != None)
    """
    tokens = a_str.rsplit(old, maxreplace)
    return new.join(tokens)
