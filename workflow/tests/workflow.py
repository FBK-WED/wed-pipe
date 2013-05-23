#!/usr/bin/env python

"""
workflow.py test suite.
"""

import os
import unittest
from django.utils.unittest.case import skip
from ..workflow import Workflow, BASH_VAR_PATTERN


class TestSequenceFunctions(unittest.TestCase):
    def setUp(self):
        self.test_configuration = \
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + \
            '/test-configurations/test-configuration.json'

        self.workflow = Workflow(
            self.test_configuration,
            {'input_1': "IN1", "input_2": "IN2", "input_3": "IN3"}
        )
        self.workflow.store_out = True
        self.workflow.store_err = True

    def test_properties(self):
        self.assertEqual(True, self.workflow.store_out)
        self.assertEqual(True, self.workflow.store_err)

    def test_doc(self):
        self.assertIsNotNone(self.workflow.__doc__)
        self.assertIsNotNone(self.workflow.process_command.__doc__)

    def test_describe(self):
        describe = self.workflow.describe()
        print 'describe:', describe
        self.assertIsNotNone(describe)

    def test_get_vars(self):
        vars = self.workflow.get_vars()
        for var in vars:
            print 'var:', var
        self.assertIsNotNone(vars)

    def test_expanded_vars(self):
        import re
        for var, val in self.workflow.get_expanded_vars():
            print 'Expanded var: %s=%s' % (var, val)
            self.assertIsNone(re.search(BASH_VAR_PATTERN, val))

    def test_expanded_nested(self):
        expanded = self.workflow.expand_string('$nested')
        print 'expanded:', expanded
        self.assertEquals('/path/to/root/module/geo_index/test', expanded)

    @skip("since we're not returning the workflow output anymore, but logging"
          "it instead, this test doesn't apply anymore")
    def test_run_module(self):
        out = self.workflow.run_module()
        print 'out:', out
        self.assertEquals(
            "{'wf_output': [u'Activated module Test WED Pipe Module ', 'Runn"
            "ing sequence', u'[OUT] ACTION IN1\\n[OUT] WFOUT <AK1> : <V11>', u"
            "'[OUT] ACTION IN2\\n[OUT] WFOUT <AK1> : <V12>\\n[OUT] WFOUT <AK1>"
            " : <V11>', [u'Activated module Test Inner WED Pipe Module ', 'R"
            "unning sequence', u'[OUT] SUB ACTION INA'], u'[OUT] ACTION IN3\\n"
            "[OUT] WFOUT <AK2> : <V2>', u'Executing next action action-4', [u'"
            "Activated module Test WED Pipe Module ', 'Running fragment sequ"
            "ence from [action-4]', u'[OUT] ACTION 4']], 'wf_output_params': {"
            "u'AK2': [u'V2'], u'AK1': [u'V12', u'V11'], 'k0': ['v0'], 'kIN': ["
            "u'IN1'], 'k1': ['v1']}}",
            repr(out)
        )

    def test_wf_error(self):
        with self.assertRaises(Exception):
            self.workflow = Workflow(
                self.test_configuration,
                {'input_1': "IN1"}
            )


if __name__ == '__main__':
    unittest.main()
