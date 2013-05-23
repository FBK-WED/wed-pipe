import util

__author__ = 'mostarda'

import unittest


class TestUtil(unittest.TestCase):
    def setUp(self):
        pass

    def test_magic_to_mime(self):
        self.assertEqual("text/plain", util.magic_to_mime('ascii text, with crlf line terminators'))