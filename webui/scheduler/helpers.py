"""
scheduler helpers
"""
import time
from datetime import datetime

from webui.scheduler.errors import UnknownMIMETypeException


def timestamp_now():
    return time.mktime(datetime.now().timetuple())


def _shorten_path_string(path):
    """Given a path if it is longer than 255 chars it is replaced with an
    MD5 of the same path."""
    import urllib
    from hashlib import md5

    candidate = urllib.quote_plus(path)
    if len(candidate) > 255:
        return md5(path).hexdigest()
    else:
        return candidate


def ext_to_mime(ext):
    import mimetypes
    ext = ext.lower()

    if ext == '.gz' or ext == '.gzip' or ext == '.zip' or ext == '.7z':
        return 'application/archive'
    if not mimetypes.inited:
        mimetypes.init()
    try:
        return mimetypes.types_map[ext]
    except KeyError:
        raise UnknownMIMETypeException('Unknown extension [%s]' % ext)
