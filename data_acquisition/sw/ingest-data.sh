#!/bin/bash

CURR_DIR="$(cd "$(dirname "$0")"; pwd -P)"

. $CURR_DIR/../common/common.sh || { echo "Error while loading configuration, aborting."; exit 1; }

CSV_EPSG=4326
INT_EPSG=900913
GEO_COL=the_geom

# Create the geometry column using the lon,lat CSV_EPSG coordinates.
function create_geometry() {
	local db=$1
	local table=$2

	$PSQL -d $db -c "ALTER TABLE $table ADD COLUMN the_geom geometry" || { echo "Error while adding geometry column."; exit 4; }
	$PSQL -d $db -c "UPDATE  $table SET \
					$GEO_COL = ST_transform( PointFromText( 'POINT(' || lon || ' ' || lat || ')', $CSV_EPSG), $INT_EPSG) \
					WHERE lon IS NOT NULL AND lat IS NOT NULL;" || { echo "Error while generating geometry columns."; exit 5; }
}

function help() {
    echo "$0 [-h|--help] {-d|--database} <database> {-s|--schema} <schema> {-c|--scraper} <scraper>"
}

# Command-line parser.
while [[ $1 == -* ]]; do
    case "$1" in
      -h|--help|-\?) help; exit 0;;
      -d|--database) shift; readonly DB="$1"     ; shift;;
      -s|--schema)   shift; readonly SCHEMA="$1" ; shift;;
      -c|--scraper)  shift; readonly SCRAPER="$1"; shift;;
      --) shift; break;;
      -*) echo "invalid option: $1" 1>&2; help; exit 1;;
    esac
done

if [ "$DB" == "" ]; then
    echo "<db> parameter must be specified."; help; exit 1
fi
if [ "$SCHEMA" == "" ]; then
    echo "<schema> parameter must be specified."; help; exit 1
fi
if [ "$SCRAPER" == "" ]; then
    echo "<scraper> parameter must be specified."; help; exit 1
fi

# Create schema.
$PSQL -d $DB -c "CREATE SCHEMA ${SCHEMA}"

# Replace Table.
$PSQL -d $DB -c "DROP TABLE IF EXISTS ${SCHEMA}.${SCRAPER}"          || { echo "Error while dropping table."; exit 1; }
$PSQL -d $DB -c "$(./create_table.py $SCRAPER ${SCHEMA}.${SCRAPER})" || { echo "Error while creating table."; exit 2; }
wget "$SW_CSV_SERVICE&query=select%20*%20from%20%60swdata%60&name=$SCRAPER" -O - 2>/dev/null | psql -d $DB -c "COPY ${SCHEMA}.${SCRAPER} FROM STDIN WITH CSV HEADER" || { echo "Error while ingesting data. Aborting."; exit 3; }

# Create geometry if lon and lat columns are present.
psql -d wedpipe-test -c "SELECT count(*) FROM ${SCHEMA}.${SCRAPER} WHERE lon IS NOT NULL AND lat IS NOT NULL" && create_geometry $DB ${SCHEMA}.${SCRAPER}

echo
echo Ingestion done.
echo

exit 0
