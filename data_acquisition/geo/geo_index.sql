CREATE OR REPLACE PROCEDURAL LANGUAGE plpython2u;

DROP TABLE geo_index;
CREATE TABLE IF NOT EXISTS geo_index ( 
	_schema  varchar,
	_table   varchar,
	id       varchar,
	the_geom geometry NOT NULL,
	version  bigint   NOT NULL,
	CONSTRAINT schema_table PRIMARY KEY(_schema, _table, id)
);

DROP   SEQUENCE geo_index_version;
CREATE SEQUENCE geo_index_version;

-- SELECT nextval('geo_index_version')
-- SELECT currval('geo_index_version')

-- Index performance test:
--   V1
--   SELECT L.id, R.id FROM geo_index AS L, geo_index AS R WHERE ST_DWithin(L.the_geom, R.the_geom, 50)

--   V2
--   10k record: 50 mt -> 254s
--   SELECT L.id, R.id FROM geo_index AS L INNER JOIN geo_index AS R ON ST_Disjoint(L.the_geom, R.the_geom) AND ST_DWithin(L.the_geom, R.the_geom, 50)
--   10k record: 50 mt -> 184s
--   20k record: 50 mt -> 799s
--   SELECT L.id, R.id FROM geo_index AS L INNER JOIN geo_index AS R ON L.id <> R.id AND ST_DWithin(L.the_geom, R.the_geom, 50)

CREATE OR REPLACE FUNCTION populate_random(size int, clean boolean=false)
RETURNS VOID
AS $$
	import random
	if clean: plpy.execute( "DELETE FROM geo_index WHERE _schema = 'fake_schema' AND _table = 'fake_table'" )
	next_version = int( plpy.execute("SELECT nextval('geo_index_version') AS nextval")[0]['nextval'] ) 
	for i in range(size):
		rs = plpy.execute("INSERT INTO geo_index(_schema, _table, id, the_geom, version) \
		                   VALUES ('fake_schema_{0}', 'fake_table_{0}', '{1}', ST_Transform( ST_GeomFromText('POINT({2})', 4326), 900913), {0})"\
		                   .format( next_version, i, str(random.uniform(10.5, 11.5)) + " " + str(random.uniform(41.5, 42.5)) ) )
$$ LANGUAGE plpython2u;

-- SELECT populate_random(40000)
-- SELECT *, ST_AsText(the_geom) from geo_index
-- SELECT COUNT(*) FROM geo_index

CREATE OR REPLACE FUNCTION copy_geometries(_schema varchar, _table varchar, id_col varchar, geom_col varchar)
RETURNS bigint
AS $$
	next_version = int( plpy.execute("SELECT nextval('geo_index_version') AS nextval")[0]['nextval'] )
	plpy.execute("DELETE FROM geo_index WHERE _schema = '{0}' AND _table = '{1}'".format(_schema, _table))
	counter = 0
	rs = plpy.execute("SELECT " + id_col + ",ST_AsText(" +  geom_col + ") AS " +	geom_col + " FROM " + _schema + "." + _table + " WHERE " + geom_col + " IS NOT NULL")
	for row in rs:
		plpy.execute("INSERT INTO geo_index(_schema, _table, id, the_geom, version) VALUES('{0}', '{1}', '{2}', ST_GeomFromText('{3}',900913), {4} )".format(_schema, _table, row[id_col], row[geom_col], next_version) )
		counter += 1
	plpy.notice('Total added geometries: ' + str(counter));
	return next_version
$$ LANGUAGE plpython2u;

-- SELECT copy_geometries('csv', 'tripadvisortrentorestaurants', 'url', 'the_geom')
-- SELECT copy_geometries('csv', 'gamberorossotrentinoaltoadigerestaurants', 'url', 'the_geom')

DROP TYPE proximity CASCADE;
CREATE TYPE proximity AS (
	id1  text,
	id2  text
);

CREATE OR REPLACE FUNCTION compute_proximity(version bigint, max_distance float)
RETURNS SETOF proximity
AS $$
	query = None
	if version == 0: 
		query = "SELECT L.id AS lid, R.id AS rid FROM geo_index AS L INNER JOIN geo_index AS R ON L.id <> R.id AND ST_DWithin(L.the_geom, R.the_geom, {0})".format(max_distance)
	else:
		query = "SELECT L.id AS lid, R.id AS rid FROM geo_index AS L INNER JOIN geo_index AS R ON L.version = {0} AND R.version <> {0} AND L.id <> R.id AND ST_DWithin(L.the_geom, R.the_geom, {1})".format(version, max_distance)
	rs = plpy.execute(query)
	for row in rs:
		# plpy.notice( "<{0}> <http://vocab.example.org#proximity> <{1}>".format(row['lid'], row['rid']) )
		yield (row['lid'], row['rid'])
$$ LANGUAGE plpython2u;

-- SELECT id1, id2 FROM compute_proximity(9, 50)
--   1290ms with 40k records

CREATE OR REPLACE FUNCTION to_ntriple(p proximity)
RETURNS text
AS $$
	return "<{0}> <http://vocab.example.org#proximity> <{1}> .".format(p['id1'], p['id2'])
$$ LANGUAGE plpython2u;


