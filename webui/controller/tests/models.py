# pylint: disable=E1103,R0904,C0111,C0103,E1101,C0302,W0232,R0201,W0212
from django.core.exceptions import ValidationError

from webui.controller.models import validate_json, validate_bbox, \
    validate_parameters, validate_init_handler, validate_dispose_handler, \
    validate_dispatcher
from webui.controller.models.factories import ArchiveItemFactory, RuleFactory

from webui.tests import TestCase


class TestModels(TestCase):
    def test_validate_json_ok(self):
        validate_json('{}')

    def test_validate_json_nok(self):
        self.assertRaises(ValidationError, validate_json, '{{')

    def test_validate_bbox_ok(self):
        validate_bbox('1,2,3,4')

    def test_validate_bbox_nok_1(self):
        self.assertRaises(ValidationError, validate_bbox, '1,2,3')

    def test_validate_bbox_nok_2(self):
        self.assertRaises(ValidationError, validate_bbox, '1,2,X,4')

    def test_validate_bbox_nok_3(self):
        self.assertRaises(ValidationError, validate_bbox, '-181,2,3,4')

    def test_validate_bbox_nok_4(self):
        self.assertRaises(ValidationError, validate_bbox, '1,-91,3,4')

    def test_validate_bbox_nok_5(self):
        self.assertRaises(ValidationError, validate_bbox, '1,2,181,4')

    def test_validate_bbox_nok_6(self):
        self.assertRaises(ValidationError, validate_bbox, '1,2,3,91')

    def test_validate_parameters_ok(self):
        validate_parameters(['a', 'c'], ['a', 'b', 'c'])

    def test_validate_parameters_nok(self):
        self.assertRaises(
            ValidationError, validate_parameters, ['a', 'd'], ['a', 'b', 'c'])

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


class ArchiveItemTestCase(TestCase):
    def test_get_rule_none(self):
        obj = ArchiveItemFactory()
        self.assertIsNone(obj.get_refine_rule())

    def test_get_rule_invalid(self):
        from refine.refine import IllegalRuleCheckSum
        obj = ArchiveItemFactory(rule=RuleFactory(hash="pippero"))
        with self.assertRaises(IllegalRuleCheckSum):
            obj.get_refine_rule()

    def test_get_rule_valid(self):
        obj = ArchiveItemFactory(rule=RuleFactory())
        self.assertEqual(obj.get_refine_rule(), obj.rule.rule)
