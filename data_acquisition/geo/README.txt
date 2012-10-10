GEO INDEX README
================

Description
-----------

  Set of PL/SQL scripts for indexing spatial entities collected during data acquisition.

Configuration
-------------

  The configuration must be executed just once and will erase the entire content of the index.
  $  psql -d wedpipe-test < geoindex.sql

Usage
-----

  Copy all geometries declared within table csv.tripadvisortrentorestaurants with ID in field 'url' and geometry in field 'the_geom'
  into the geometry index and return the ingestion version:

    $psql -d wedpipe-test -c "SELECT copy_geometries('csv', 'tripadvisortrentorestaurants', 'url', 'the_geom')"

  Compute the proximity triples for the entities ingested at revision 5 with max distance 50.

    $ psql -d wedpipe-test -c "SELECT to_ntriple(p) FROM compute_proximity(5, 50) as p" -o -
