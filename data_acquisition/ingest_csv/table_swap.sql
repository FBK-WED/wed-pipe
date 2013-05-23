
-- http://stackoverflow.com/questions/1109061/insert-on-duplicate-update-postgresql/1109198#1109198
CREATE OR REPLACE FUNCTION merge_table(table_name TEXT, hash TEXT, fields TEXT, vals TEXT) RETURNS int AS
$$
DECLARE 
    r int;
BEGIN
    LOOP
        EXECUTE('UPDATE ' || table_name || ' SET ' || fields || ' = ' || vals || ' WHERE __sd_hash__ = ''' || hash || '''');
        GET DIAGNOSTICS r = ROW_COUNT;
        IF r > 0 THEN
            RETURN 0;
        END IF;
        BEGIN
            EXECUTE('INSERT INTO ' || table_name || fields || ' VALUES ' || vals);
            GET DIAGNOSTICS r = ROW_COUNT;
            IF r > 0 THEN
                RETURN 1;
            ELSE
                RETURN 2;
            END IF;
        EXCEPTION WHEN unique_violation THEN
            -- Nothing.
        END;
    END LOOP;
END;
$$
LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION append_table(swap_table varchar, master_table varchar)
RETURNS VOID
AS $$
	HASH = '__sd_hash__'
	swap_table_rs = plpy.execute('SELECT * FROM "%s"' % swap_table)
	# postgres 9.2 plpy.info(swap_table_rs.colnames())
	# postgres 9.2 plpy.info(swap_table_rs.coltypes())
	updates_count = 0
	inserts_count = 0
	unmodif_count = 0
	version_ts = str( plpy.execute('SELECT now()')[0]['now'] )
	for swap_row in swap_table_rs:
		keys = []
		vals = []
		for k in swap_row:
			keys.append('"%s"' % k.replace("'", ""))
			v = swap_row[k]
			if v is None:
				v = "null"
			elif type(v) == str:
				if len( v.strip() ) == 0:
					v = "null"
				else:
				  v = "''%s''" % v.replace("'", "")
			vals.append( str(v) )
		keys.append('version')
		vals.append("''%s''" % version_ts)
		keys_str = '(' + ','.join(keys) + ')'
		vals_str = '(' + ','.join(vals) + ')'
		result = plpy.execute( "SELECT merge_table('\"%s\"', '%s', '%s', '%s')" % (master_table, swap_row[HASH], keys_str, vals_str) )
		out_code = result[0]['merge_table']
		if out_code == 0:
			updates_count += 1
		elif out_code == 1:
			inserts_count += 1
		elif out_code == 2:
			unmodif_count += 1
	plpy.execute('DROP TABLE "%s"' % swap_table)
	plpy.notice('Rows updated: %d, added: %d, unmodified: %d' % (updates_count, inserts_count, unmodif_count));
	plpy.notice('Swap table [%s] removed.' % swap_table);
$$ LANGUAGE plpython2u;


-- BEGIN: Test procedure
DROP TABLE tmp_swap_table;
CREATE TABLE tmp_swap_table (
   HASH text PRIMARY KEY,
   F1   text,
   F2   text
);

INSERT INTO tmp_swap_table (hash, f1, f2) VALUES ('h1', 'v11', 'v12');
INSERT INTO tmp_swap_table (hash, f1, f2) VALUES ('h2', 'v21', 'v22');
INSERT INTO tmp_swap_table (hash, f1, f2) VALUES ('h3', 'v31', 'v32');

DROP TABLE tmp_master_table;
CREATE TABLE tmp_master_table (
   HASH text PRIMARY KEY,
   F1   text,
   F2   text
);

INSERT INTO tmp_master_table (hash, f1, f2) VALUES ('h1', 'v1X', 'v1Y');
INSERT INTO tmp_master_table (hash, f1, f2) VALUES ('hA', 'vA1', 'vA2');
INSERT INTO tmp_master_table (hash, f1, f2) VALUES ('hB', 'vB1', 'vB2');

SELECT append_table('tmp_swap_table', 'tmp_master_table');
-- END: Test procedure

