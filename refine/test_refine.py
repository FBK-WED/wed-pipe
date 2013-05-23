import json
import unittest
import refine


THE_JSON = """
[
    {
        "operation": {
            "schema": {
                "baseUri": "http://wrong.base/",
                "prefixes": [
                    {
                        "name": "rdfs",
                        "uri": "http://www.w3.org/2000/01/rdf-schema#"
                    },
                    {
                        "name": "foaf",
                        "uri": "http://xmlns.com/foaf/0.1/"
                    },
                    {
                        "name": "xsd",
                        "uri": "http://www.w3.org/2001/XMLSchema#"
                    },
                    {
                        "name": "owl",
                        "uri": "http://www.w3.org/2002/07/owl#"
                    },
                    {
                        "name": "rdf",
                        "uri": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                    }
                ],
                "rootNodes": [
                    {
                        "isRowNumberCell": true,
                        "expression": "value",
                        "rdfTypes": [],
                        "nodeType": "cell-as-resource",
                        "links": [
                            {
                                "curie": "foaf:focus",
                                "uri": "http://xmlns.com/foaf/0.1/focus",
                                "target": {
                                    "isRowNumberCell": false,
                                    "expression": "value",
                                    "nodeType": "cell-as-literal",
                                    "columnName": "id"
                                }
                            },
                            {
                                "curie": "foaf:mbox",
                                "uri": "http://xmlns.com/foaf/0.1/mbox",
                                "target": {
                                    "isRowNumberCell": false,
                                    "expression": "value",
                                    "nodeType": "cell-as-literal",
                                    "columnName": "url"
                                }
                            },
                            {
                                "curie": "foaf:geekcode",
                                "uri": "http://xmlns.com/foaf/0.1/geekcode",
                                "target": {
                                    "isRowNumberCell": false,
                                    "expression": "value",
                                    "nodeType": "cell-as-literal",
                                    "columnName": "name"
                                }
                            },
                            {
                                "curie": "foaf:dnaChecksum",
                                "uri": "http://xmlns.com/foaf/0.1/dnaChecksum",
                                "target": {
                                    "isRowNumberCell": false,
                                    "expression": "value",
                                    "nodeType": "cell-as-literal",
                                    "columnName": "category"
                                }
                            }
                        ]
                    }
                ]
            },
            "description": "Save RDF schema skeleton",
            "op": "rdf-extension/save-rdf-schema"
        },
        "description": "Save RDF schema skeleton"
    }
]
"""


class TestRefine(unittest.TestCase):
    """Test suite for refine.py module."""

    def test_strip_rules(self):
        from mock import MagicMock
        archive_item = MagicMock()
        archive_item.datagraph_mapped_row_id = lambda x: 'blblblblbl'
        out = refine.strip_rules(
            json.loads(THE_JSON), archive_item
        )

        _base_uri = out[0]['schema']['baseUri']
        try:
            base_uri = unicode(_base_uri, 'utf8')
        except TypeError:
            base_uri = unicode(_base_uri)

        expected_uri = archive_item.datagraph_mapped_row_id('')
        self.assertEqual(expected_uri, base_uri)
