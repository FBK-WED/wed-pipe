import os
import sys

import fiona
from shapely.geometry import shape
from functools import partial
from itertools import izip
import pyproj
import csv

webuidir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, webuidir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'webui.settings'


def transform(func, geom):
    """Applies `func` to all coordinates of `geom` and returns a new
       geometry of the same type from the transformed coordinates.

       Source: https://github.com/sgillies/shapely/blob/master/shapely/ops.py
    """

    if geom.type in ('Point', 'LineString', 'Polygon'):

        # First we try to apply func to x, y, z sequences. When func is
        # optimized for sequences, this is the fastest, though zipping
        # the results up to go back into the geometry constructors adds
        # extra cost.
        try:
            if geom.type in ('Point', 'LineString'):
                return type(geom)(zip(*func(*izip(*geom.coords))))
            elif geom.type == 'Polygon':
                shell = type(geom.exterior)(
                    zip(*func(*izip(*geom.exterior.coords))))
                holes = list(
                    type(ring)(zip(*func(*izip(*ring.coords))))
                    for ring in geom.interiors
                )
                return type(geom)(shell, holes)

        # A func that assumes x, y, z are single values will likely raise a
        # TypeError, in which case we'll try again.
        except TypeError:
            if geom.type in ('Point', 'LineString'):
                return type(geom)([func(*c) for c in geom.coords])
            elif geom.type == 'Polygon':
                shell = type(geom.exterior)(
                    [func(*c) for c in geom.exterior.coords])
                holes = list(
                    type(ring)([func(*c) for c in ring.coords])
                    for ring in geom.interiors
                )
                return type(geom)(shell, holes)

    elif geom.type.startswith('Multi') or geom.type == 'GeometryCollection':
        return type(geom)([transform(func, part) for part in geom.geoms])
    else:
        raise ValueError('Type %r not recognized' % geom.type)


def main(args):
    """ the body of the script
    """

    with fiona.open(args.file) as source, open(args.out_file, "w") as out:
        encoding = args.encoding or source.encoding or 'utf-8'
        proj = args.proj or source.crs

        if not proj:
            raise ValueError("Can't find the SHP projection")

        header = []
        for val in source.schema['properties'].keys():
            if isinstance(val, unicode):
                val = val.encode("utf-8")
            elif isinstance(val, basestring):
                val = val.decode(encoding).encode("utf-8")
            header.append(val)
        header += ["geometry"]

        print "Using encoding: {}".format(encoding)

        project = partial(
            pyproj.transform,
            pyproj.Proj(init=proj)
            if isinstance(proj, basestring) else pyproj.Proj(proj),
            pyproj.Proj(init="epsg:4326")
        )

        print "Transforming projection {} to EPSG:4326".format(proj)

        csv_writer = csv.DictWriter(out, fieldnames=header)
        csv_writer.writeheader()

        for i, feature in enumerate(source):
            properties = {}
            for key, val in feature['properties'].items():
                if isinstance(val, unicode):
                    properties[key] = val.encode("utf-8")
                elif isinstance(val, basestring):
                    properties[key] = val.decode(encoding).encode("utf-8")
                else:
                    properties[key] = val

            try:
                properties["geometry"] = transform(
                    project,
                    shape(feature['geometry'])
                ).wkt
            except:  # pylint: disable=W0702
                print "Error processing a geometry"
                continue

            csv_writer.writerow(properties)

            if i > 0 and i % 1000 == 0:
                print "Processed {} features".format(i)

    print "SHP conversion to CSV completed"
    # Overwrite the input SHP with the CSV version of it
    os.rename(args.out_file, args.file)
