# -*- coding: utf-8 -*-
"""
Prende in input nome tabella, connessione db, namedgraph.
Restituisce un file turtle (IRI encoding).
L'RDF è cosi' fatto: per ogni riga dell'csv si crea una risorsa con uri
(data.venturi.fbk.eu/resource/NOMETABELLA/id-riga), per ogni colonna crea una
property del tipo raw.venturi.fbk.eu/property/NOMETABELLA/NOMECOLONNA.

Per ogni tripla crea una quadrupla in cui il URL-NAMEDGRAPH è il parametro
"namedgraph".

Quindi cerca nella tabella 'meta' di PostgreSQL la riga della colonna 'table'
che contiene 'NOMETABELLA' e genera le triple di metadata da quelle.

Le triple di metadata sono una serie di triple del tipo:

<URL-DEL-NAMEDGRAPH>
<raw.venturi.fbk.eu/metadata/NOME-METADATO>
<VALORE DEL METADATO>

Le tabelle nel db pgsql raw sono create con cose tipo:
    "CREATE TABLE <NOMETABELLA> (" + " VARCHAR,
        ".join(COLUMNS.replace(' ', '_').split(',')) + " VARCHAR);"

    dove NOMETABELLA è source_dataset e COLUMNS sono i nomi originali con
    eventuali spazi sostituiti da underscore
"""

from __future__ import print_function
from contextlib import closing

import os
import codecs
import logging
import sys
from os import path
from rdflib import Namespace, Literal, RDF


webuidir = path.join(path.dirname(__file__), '../..')
sys.path.insert(0, webuidir)

os.environ['DJANGO_SETTINGS_MODULE'] = 'webui.settings'

from django.conf import settings
from webui.controller.models import Source

PREFIXES = settings.TRIPLE_DATABASE['PREFIXES']
SDOWL = Namespace(PREFIXES['sdowl'])
SDMETA = Namespace(PREFIXES['meta'])
HASH_COLUMN_NAME = '__sd_hash__'

logger = logging.getLogger(__file__)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('errors.log')
file_handler.setLevel(logging.WARNING)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)


def generate_meta(a_django_obj):
    """ given a django model instance, return a dictionary with its
     fields to be added in the meta graph
    """
    return {
        field.name: getattr(a_django_obj, field.name)
        for field in type(a_django_obj)._meta.fields
    }


class TrigGraph(object):
    """ a graph
    """
    def __init__(self, name):
        self.name = name
        self.triples = []

    @staticmethod
    def nformat(tupla):
        """ Restituisce la tupla formattata in ntriple o nquads,
        supporta elementi da rdflib (metodo .n3) o stringhe generiche
        """
        return u' '.join(
            item.n3() if hasattr(item, 'n3') else unicode(item) for item in tupla
        ) + u' .'

    def add_triple(self, triple):
        """ add a triple to self
        """
        self.triples.append(triple)

    def __str__(self):
        return u'<{graph_name}> {{\n'.format(graph_name=self.name) + \
               u'\n'.join(
                   u'\t' + self.nformat(triple) for triple in self.triples
               ) + u'\n}\n'


class TrigFile(object):
    """ a trig file, that can contain an infinite number of graphs
    """
    def __init__(self, filename):
        self.filename = filename
        self.graphs = []

    def add_graph(self, name):
        """ add a graph to the trig file
        """
        graph = TrigGraph(name)
        self.graphs.append(graph)
        return graph

    def close(self):
        """ close the trig file
        """
        with codecs.open(self.filename, 'w', encoding='utf8') as fout:
            for graph in self.graphs:
                fout.write(unicode(graph))


def source_meta_quads(source):
    """ Genera le triple di metadati associate alla sorgente
    """
    entity = Namespace(source.metagraph_resource_id)
    klass = Namespace(PREFIXES["sdowl"])['Source']

    yield (entity, RDF.type, klass)

    for key, value in generate_meta(source).iteritems():
        yield entity, SDMETA[key], Literal(value)


def dataset_meta_quads(dataset):
    """ Genera le triple di metadati associate al dataset
    """
    entity = Namespace(dataset.metagraph_resource_id)
    klass = Namespace(PREFIXES["sdowl"])['Dataset']

    yield (entity, RDF.type, klass)
    yield (entity, SDOWL['belongs_to_source'],
           Namespace(dataset.source.metagraph_resource_id))

    for key, value in generate_meta(dataset).iteritems():
        yield entity, SDMETA[key], Literal(value)


def archive_item_meta_quads(archive_item):
    """ Genera le triple di metadati associate all'archive-item
    """
    entity = Namespace(archive_item.metagraph_resource_id)
    klass = Namespace(PREFIXES["sdowl"])['ArchiveItem']

    yield (entity, RDF.type, klass)
    yield (entity, SDOWL['belongs_to_dataset'],
           Namespace(archive_item.dataset.metagraph_resource_id))

    yield (entity, SDMETA['tablename'], Literal(archive_item.tablename))
    for key, value in generate_meta(archive_item).iteritems():
        yield entity, SDMETA[key], Literal(value)


def archive_item_data_quads(archive_item):
    """ Genera le triple riguardanti i dati di un ArchiveItem
    """
    row_iter = archive_item.data()
    header = row_iter.next()
    archive_entity = Namespace(archive_item.metagraph_resource_id)
    archive_ns = Namespace(
        '{}#'.format(archive_item.metagraph_resource_id)
    )

    try:
        hash_index = header.index(HASH_COLUMN_NAME)
    except ValueError:
        hash_index = None

    for i, row in enumerate(row_iter):
        key = row[hash_index] if hash_index is not None else i
        entity = Namespace(
            archive_item.datagraph_raw_row_id(key)
        )

        yield (entity, SDOWL['belongs_to_archiveItem'], archive_entity)
        for col_name, col_value in zip(header, row):
            if col_value is not None:
                yield (entity, archive_ns[col_name], Literal(col_value))


def refresh_sources(source_id=None):
    """ generate a .trig file for the source, and ingest it into virtuoso
    """
    sources = [Source.objects.get(pk=source_id)] \
        if source_id else Source.objects.all()

    filename = 'source-{}.trig'.format(source_id if source_id else 'all')
    n_triples = 0

    clear_graphs = []
    with closing(TrigFile(filename)) as trig:
        meta_graph = trig.add_graph(PREFIXES['meta_graph'])
        for source in sources:
            # add triples for source metadata
            for quad in source_meta_quads(source):
                meta_graph.add_triple(quad)
                n_triples += 1

            for dataset in source.datasets.all():
                # add triples for dataset metadata
                for quad in dataset_meta_quads(dataset):
                    meta_graph.add_triple(quad)
                    n_triples += 1

                for archive_item in dataset.archive_items.all():
                    # add triples for archive_item metadata
                    for quad in archive_item_meta_quads(archive_item):
                        meta_graph.add_triple(quad)
                        n_triples += 1
                    data_graph = trig.add_graph(
                        archive_item.datagraph_raw_name
                    )
                    clear_graphs.append(data_graph.name)
                    # add triples for archive item
                    for quad in archive_item_data_quads(archive_item):
                        data_graph.add_triple(quad)
                        n_triples += 1

    from webui.cnmain.utils import get_virtuoso
    virtuoso = get_virtuoso()
    logger.debug('ingesting {} into virtuoso'.format(filename))
    virtuoso.clear(clear_graphs)
    virtuoso.ingest(filename)

    return n_triples
