""" utility stuff
"""
from uuid import uuid4
from django.conf import settings
from django.contrib.webdesign import lorem_ipsum
from factory.declarations import OrderedDeclaration


class Uuid4Attribute(OrderedDeclaration):
    """ attribute for being used in factories, which return a random uuid
    """
    def __init__(self, prefix=''):
        self.prefix = prefix + '-' if prefix else prefix

    def evaluate(self, sequence, obj, containers=()):
        return self.prefix + str(uuid4())


class LoremIpsumAttribute(OrderedDeclaration):
    """ attribute for being used in factories, which return a lorem ipsum text
    """
    def __init__(self, words=0, paragraphs=0, common=None):
        self.words = words
        self.paragraphs = paragraphs
        self.common = common
        if self.common is None:
            self.common = self.words >= 10 or self.paragraphs > 1

    def evaluate(self, sequence, obj, containers=()):
        if self.words:
            return lorem_ipsum.words(self.words, common=self.common)
        return '\n'.join(
            lorem_ipsum.paragraphs(self.paragraphs, common=self.common)
        )


def get_redis():
    """ return a redis instance
    """
    from redis import Redis
    return Redis()


def _get_virtuoso_conf_by_name(instance):
    """ given a virtuoso instance name, return its configuration
    """
    if instance == 'master':
        return settings.TRIPLE_DATABASE_MASTER
    return settings.TRIPLE_DATABASE


def get_virtuoso(instance='default'):
    """ return a virtuoso instance
    """
    from pygraph import GenericGraph
    triple = _get_virtuoso_conf_by_name(instance)
    return GenericGraph.get_by_type(
        triple['TYPE'],
        host=triple['HOST'],
        port=triple['PORT'],
        admin_host=triple.get('ADMIN_HOST'),
        admin_port=triple.get('ADMIN_PORT'),
        user=triple.get('ADMIN_USER'),
        password=triple.get('ADMIN_PASSWORD'),
        scp_user=triple.get('SCP_USER'),
        scp_port=triple.get('SCP_PORT', 22),
        isql=triple.get('ISQL', '/usr/bin/isql-vt'),
        endpoint=triple.get('ENDPOINT', 'sparql'),
        sesame_console=triple.get('SESAME_CONSOLE', '/usr/bin/sesame-console'),
        repository_name=triple.get('REPOSITORY'),
        load_dir=triple.get('LOAD_DIR', '/srv/virtuoso/data/'),
        **triple.get('KWARGS', {})
    )


def get_virtuoso_endpoint(instance='default'):
    """ return the URL of the sparql endpoint
    """
    triple = _get_virtuoso_conf_by_name(instance)
    return 'http://{host}:{port}/{endpoint}'.format(
        host=triple['HOST'],
        port=triple['PORT'],
        endpoint=triple['ENDPOINT'],
    )


def get_sparql_query_metagraph_info(an_obj):
    """ return the SPARQL query for getting info about a resource (something
     like DESCRIBE, but it's not a describe...)
    """
    return 'SELECT ?concept, ?value, ?rev_value ' \
           'WHERE {{GRAPH <{graph}> ' \
           '{{{{<{resource}> ?concept ?value }} UNION ' \
           '  {{?rev_value ?concept <{resource}> }}}}}}'.format(
               graph=settings.TRIPLE_DATABASE['PREFIXES']['meta_graph'],
               resource=an_obj.metagraph_resource_id,
           )


def get_sparql_query_graph(graph_name):
    """ return the SPARQL query for getting all the triples of a graph
    """
    return 'SELECT ?resource, ?concept, ?value ' \
           'WHERE {{GRAPH <{graph}> {{?resource ?concept ?value}}}} ' \
           'LIMIT 50'.format(
               graph=graph_name
           )
