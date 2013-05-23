"""
Utilities for slice app
"""
import simplejson as json
from webui.controller.models import ArchiveItem


def dicts2geojsonfeatures(objects):
    """
    Convert an iterable of dicts to geojson features.
    Supports point geometry, given as "lat" and "lon" keys in dicts and
    any other WKT geometry given as "geometry" key

    @param objects: a list of dicts
    """

    from shapely import wkt
    import geojson

    lat_key = "latitude"
    lon_key = "longitude"
    geometry_key = "geometry"

    for obj in objects:

        data = {
            'type': 'Feature',
            'properties': obj
        }
        try:
            lat = float(obj.pop(lat_key))
            lon = float(obj.pop(lon_key))
        except:  # pylint: disable=W0702
            pass
        else:
            data['geometry'] = {
                'type': 'Point',
                'coordinates': [lon, lat]
            }

        try:
            # Very ugly, but it seems the only way to do it
            geometry = json.loads(
                geojson.dumps(wkt.loads(obj.pop(geometry_key)))
            )
        except:  # pylint: disable=W0702
            pass
        else:
            data['geometry'] = geometry

        yield data


def dicts2geojson(objects):
    """ converts a dictionary to geojson
    """
    yield '{'

    yield '"crs":'
    yield json.dumps({
        "type": "name",
        "properties": {
            "name": "urn:ogc:def:crs:EPSG::4326"
        }
    })
    yield ','

    yield '"type": "FeatureCollection",'
    yield '"features": ['

    first = True
    for feature in dicts2geojsonfeatures(objects):
        if not first:
            yield ','
        first = False

        yield json.dumps(feature)

    yield ']}'


def get_sliced_data(query, fields, with_header=False):
    """
    Returns a query result.
    The result can be cleaned, removing duplicates

    In case of error it raises a ValueError
    """
    from urllib2 import HTTPError
    from tempfile import mkstemp
    # from webui.cnmain.utils import get_virtuoso

    # virtuoso = get_virtuoso(instance='master')

    from bulbs.titan import Graph
    from bulbs.config import Config

    header = [field.strip() for field in fields.split(',')]

    handle_, path = mkstemp(text=True)

    with open(path, 'w') as f:
        f.write(query)

    c = Config('http://localhost:8182/graphs/graph')
    g = Graph(c)

    g.scripts.update(path)

    try:
        nodes_fun = g.scripts.get('nodes')
    except KeyError:
        raise ValueError("Malformed query: missing nodes() function")

    nodes_id = g.gremlin.execute(nodes_fun, {}).content['results']

    if with_header:
        yield header

    block_size = 100
    has_results = False
    for i in range(len(nodes_id) / block_size + 1):
        start = i * block_size
        block = nodes_id[start:start + block_size]

        try:
            slice_fun = g.scripts.get('slice')
            content = g.gremlin.execute(slice_fun, {'nodes_id': block}).content
        except HTTPError, e:
            raise ValueError("Malformed query: {}".format(e.read()))

        for result in content['results']:
            has_results = True
            yield result

    # yield {'acheneID': '1', 'provenance': 'OSM'}
    # header = result.variables
    #
    # # handle owlim errors
    # if header == ['error-message']:
    #     raise ValueError(list(result.fetchone())[0][0])

    if not has_results:
        raise ValueError("No results for the given query")


def clean_sliced_data(query_result, fields):
    """
    Cleans a query_result from useless duplicated data
    """
    from django.conf import settings
    provenance_dict = {
        archiveitem.tablename: archiveitem.dataset.source.public_name
        for archiveitem in ArchiveItem.objects.all()
    }

    for row in query_result:
        try:
            achene_id = row['acheneID']
        except KeyError:
            raise ValueError('No field "acheneID"')

        row['acheneID'] = settings.DM_RESOURCE_BASE_PREFIX + achene_id

        try:
            row['provenance'] = sorted({
                provenance_dict.get(
                    provenance.split(':')[-1], 'Venturi Partner'
                ) for provenance in row['provenance']
            })
        except (KeyError, AttributeError):
            raise ValueError('No field "provenance"')

        if 'category' in fields:
            if 'category' not in row or not row['category']:
                row['category'] = settings.SLICE_DEFAULT_CATEGORY

            row['category'] = row['category'].replace(
                'http://ontologies.venturi.eu/taxonomies/',
                settings.DM_CATEGORY_BASE_PREFIX
            )

        yield row


def get_cleaned_sliced_data(query, fields, with_header=False):
    """
    Given a sparql query, execute it on the master graph and smush it.

    If with_header=True, the first returned element is a list containing data
    headers.
    """
    data = get_sliced_data(query, fields, with_header=with_header)
    if with_header:
        yield next(data)

    for row in clean_sliced_data(data, fields):
        yield row
