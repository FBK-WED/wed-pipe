__author__ = 'hardest'

import os, sys

_candidate_insert = os.path.dirname(os.path.realpath(__file__)) + '/../'
if not _candidate_insert in sys.path:
	sys.path.insert(0, _candidate_insert)