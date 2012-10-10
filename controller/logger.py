"""
Project logging module.
"""

import os
import logging

_log_path  = os.path.dirname(os.path.realpath(__file__)) + '/controller.log'

# Import local path settings

try:
    from settings_local import _log_path
except ImportError:
    pass

_hdlr      = logging.FileHandler(_log_path)
_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
_hdlr.setFormatter(_formatter)

def get_logger(name):
	logger = logging.getLogger(name)
	logger.addHandler(_hdlr) 
	logger.setLevel(logging.INFO)
	return logger

