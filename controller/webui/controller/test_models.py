import unittest
from django.core.exceptions import ValidationError
from webui.controller.models import validate_json, validate_bbox, validate_parameters, validate_init_handler, validate_dispose_handler, validate_dispatcher

class TestModels(unittest.TestCase):

	def test_validate_json_ok(self):
		validate_json('{}')

	def test_validate_json_nok(self):
		self.assertRaises(ValidationError, validate_json, '{{')

	def test_validate_bbox_ok(self):
		validate_bbox('1,2,3,4')

	def test_validate_bbox_nok_1(self):
		self.assertRaises(ValidationError,validate_bbox, '1,2,3')

	def test_validate_bbox_nok_2(self):
		self.assertRaises(ValidationError,validate_bbox, '1,2,X,4')

	def test_validate_bbox_nok_3(self):
		self.assertRaises(ValidationError,validate_bbox, '-181,2,3,4')

	def test_validate_bbox_nok_4(self):
		self.assertRaises(ValidationError,validate_bbox, '1,-91,3,4')

	def test_validate_bbox_nok_5(self):
		self.assertRaises(ValidationError,validate_bbox, '1,2,181,4')

	def test_validate_bbox_nok_6(self):
		self.assertRaises(ValidationError,validate_bbox, '1,2,3,91')

	def test_validate_parameters_ok(self):
		validate_parameters(['a', 'c'], ['a', 'b', 'c'])

	def test_validate_parameters_nok(self):
		self.assertRaises(ValidationError, validate_parameters, ['a', 'd'], ['a', 'b', 'c'])

	def test_validate_init_handler_ok(self):
		validate_init_handler('pass')

	def test_validate_init_handler_nok(self):
		self.assertRaises(ValidationError, validate_init_handler, 'def:')

	def test_validate_dispose_handler_ok(self):
		validate_dispose_handler('pass')

	def test_validate_dispose_handler_nok(self):
		self.assertRaises(ValidationError, validate_dispose_handler, 'def:')

	def test_validate_dispatcher_ok(self):
		validate_dispatcher('pass')

	def test_validate_dispatcher_nok(self):
		self.assertRaises(ValidationError, validate_dispatcher, 'def:')

