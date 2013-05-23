import util

import simplejson as json

from google.refine import refine
from django.conf import settings

CSV_SEPARATOR = ','

RDF_SCHEMA_MAPPING_OPERATION = 'rdf-extension/save-rdf-schema'

HASH_COLUMN_NAME = '__sd_hash__'


def get_refine_server_url():
    """Get the Google Refine url"""
    server_url = 'http://' + settings.REFINE_EXTERNAL_HOST
    if settings.REFINE_EXTERNAL_PORT:
        server_url = server_url + ':' + settings.REFINE_EXTERNAL_PORT
    return server_url


def get_refine_ws():
    """Returns a new Google Refine workspace."""
    server_url = get_refine_server_url()
    return refine.Refine(server_url)


def change_base_uri(operation, archive_item, compact=False):
    """
    Changes the base URI of the RDF mapping operation with one depending on
    the dataset source.
    """
    if compact:
        base_uri = settings.TRIPLE_DATABASE['PREFIXES']["sdres"]
    else:
        base_uri = archive_item.datagraph_mapped_row_id('')
    operation['schema']['baseUri'] = base_uri


def strip_rules(rules_json, archive_item):
    """Strips out non operation entries from a given GRefine history JSON
    export."""
    rules = []
    for rule_json in rules_json:
        operation = rule_json.get('operation')
        if not operation:
            continue
        if operation.get('op') == RDF_SCHEMA_MAPPING_OPERATION:
            compact = \
                not operation['schema']['rootNodes'][0]['isRowNumberCell']
            change_base_uri(operation, archive_item, compact)
        rules.append(operation)
    return rules


# def append_hash_rule(hash_code, rules_json, hash_base_column):
#     operation = {
#         'op': 'core/column-addition',
#         'description': 'Added programmatically to compute hash',
#         'engineConfig': {'facets': [], 'mode': 'row-based'},
#         'newColumnName': HASH_COLUMN_NAME,
#         "columnInsertIndex": 0,
#         'baseColumnName': hash_base_column,
#         'expression': 'grel:%s' % hash_code,
#         'onError': 'store-error'
#     }
#     rules_json.append(operation)
#     return rules_json


def apply_refine_on_file(out_file_turtle, archive_item):
    """Applies a set of rules over an input file and produces a turtle file.
    """

    refine_prj = None

    # out_file_ext = get_extension(in_file)
    # out_file = in_file[0: -len(out_file_ext)] + '.refine' + out_file_ext

    try:
        refine_prj = archive_item.create_refine_project(save=False)

        rules = archive_item.get_refine_rule()
        rules = strip_rules(rules, archive_item)
        refine_prj.apply_operations_json(
            json.dumps(
                rules
                # append_hash_rule(
                #     archive_item.dataset.source.hash_handler,
                #     rules,
                #     refine_prj.columns[0]
                # )
            )
        )
        # file_handler = refine_prj.export(export_format='csv')
        # util.delete_file_silently(out_file)
        # with open(out_file, 'w') as out_file_handler:
        #     out_file_handler.write(file_handler.read())
        # Produces the turtle file if some mapping is defined.
        # out_file_turtle = None
        if contain_rdf_mapping(rules):
            # out_file_turtle = out_file + '.turtle'
            util.delete_file_silently(out_file_turtle)
            export_rdf_file(refine_prj, out_file_turtle)
        else:
            raise NoRDFRule
    except Exception:
        raise
    finally:
        if refine_prj:
            refine_prj.delete()


def contain_rdf_mapping(rules):
    """Checks whether a set of operations contains an RDF mapping. """
    print rules
    for rule in rules:
        try:
            if rule['op'] == u'rdf-extension/save-rdf-schema':
                return True
        except KeyError:
            pass
    return False


def export_rdf_file(refine_prj, out_file):
    """Exports content of a GRefine project to an output file."""
    sock = refine_prj.export('turtle')
    with open(out_file, 'w') as out_file_handler:
        while True:
            line = sock.readline()
            if line == '':
                break
            out_file_handler.write(line)


class IllegalRuleCheckSum(Exception):
    """
    A Dataset file declares a rule which checksum is different from the one
    generated during the definition of that rule.
    """
    pass


class NoRDFRule(Exception):
    """
    No rule defined for creating an RDF
    """
    pass
