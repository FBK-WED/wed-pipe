#!/usr/bin/env python

"""
Main access point.
"""

from django.core.management import execute_manager
import imp

# PyCharm remote debugging
# from pydev import pydevd
# pydevd.settrace('127.0.0.1', port=8124, stdoutToServer=True, stderrToServer=True, suspend=False)

try:
    imp.find_module('settings')
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n" % __file__)
    sys.exit(1)

import settings

if __name__ == "__main__":
    execute_manager(settings)
