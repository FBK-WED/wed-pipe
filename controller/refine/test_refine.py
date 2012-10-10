__author__ = 'mostarda'

import json
import unittest
import refine


class TestRefine(unittest.TestCase):
	"""Test suite for refine.py module."""

	def test_strip_rules(self):
		out = refine.strip_rules("""
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
		""", "http://fake.com/download", "/")

		self.assertEqual('http://mapped.example.org/a244f3935d118dc5968288a4c6f5a2aba82e61a4/', json.loads(out)[0]['schema']['baseUri'])