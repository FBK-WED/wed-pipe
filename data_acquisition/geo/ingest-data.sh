#!/bin/bash

#
# This script loads archives containing SHP files in PostGres.
#

CURR_DIR="$(cd "$(dirname "$0")"; pwd -P)"

. $CURR_DIR/../common/common.sh || { echo "Error while loading configuration, aborting."; exit 1; }

SOURCE_EPSG=32632
TARGET_EPSG=900913
ENCODING=latin1

# Decompress the given archive file or dir.
function decompress_archive() {
	local archive=$1

	if [ -d "$archive" ]; then
		echo Decompressing internal archive $archive content ...
		decompress_in_place "$archive"
		echo done
		expanded_archive="$archive"
	else
		decompressed_archive="${archive}_decompressed"
		echo Decompressing archive $archive into dir $decompressed_archive ...
		rm -fr "$decompressed_archive"
		mkdir -p "$decompressed_archive"
		decompress "$archive" "$decompressed_archive"
		echo Decompression completed
		expanded_archive="$decompressed_archive"
	fi
}

# Convert the SHP files within the specified archive to a destination EPSG.
function convert_archive() {
	local archive=$1
	local src_epsg=$2
	local tgt_epsg=$3

	rm   -fr "$archive"/$tgt_epsg
	mkdir -p "$archive"/$tgt_epsg
	for shapefile in $(find "$archive" -name '*.shp'); do
		echo Converting file $shapefile to EPSG $tgt_epsg into $archive/$tgt_epsg ...
		$OGR2OGR_TOOL -t_srs epsg:$tgt_epsg "$archive"/$tgt_epsg/$( basename $shapefile) $shapefile || \
			{ echo "Cannot convert with default SRS, enforcing EPSG: $src_epsg"; \
				$OGR2OGR_TOOL -skipfailures -s_srs epsg:$src_epsg -t_srs epsg:$tgt_epsg "$archive"/$tgt_epsg/ $shapefile; \
			} || { echo "Error while converting file $shapefile, aborting."; exit 1; }
		echo EPSG conversion completed
	done
}

# Ingest the given dir containing SHP files within the configured user PostGres.
function ingest_archive() {
	local archive=$1
	local db=$2
	local schema=$3

	echo Drop and create schema $schema...
	psql -d $db -c 'CREATE SCHEMA "'$schema'"'
	echo done.

	echo Ingesting SHP files into Spatial Database $db ...
	cd "$archive" || { echo "Error while accessing dir $archive . Aborting."; exit 1; }
	for shape in $( find $archive -name '*.shp' ); do
		shapename=${shape/.shp/}
		tablename=$( basename $shapename )
		$SHP2PGSQL_TOOL -I -W$ENCODING -d -s $TARGET_EPSG $shapename "${schema}.${tablename}" | $PSQL -d $db 2>&1 > /dev/null || { echo "Error while ingesting SHP file into pgSQL, aborting."; exit 1; }
		echo "WFOUT <shp_tables> : <$tablename>"
	done
	echo SHP ingestion completed.
}

function help() {
	echo "Usage: $0 [-h|--help] {-d|--database} <db> {-s|--schema} <schema> {-a|--archive} <archive-file>"
}

# Command-line parser.
while [[ $1 == -* ]]; do
	case "$1" in
		-h|--help|-\?) help; exit 0;;
		-d|--database) shift; readonly DB="$1"       ; shift;;
		-s|--schema)   shift; readonly SCHEMA="$1"   ; shift;;
		-a|--archive)  shift; readonly ARCHIVE="$1"  ; shift;;
		--) shift; break;;
		-*) echo "invalid option: $1" 1>&2; help; exit 1;;
	esac
done
if ! which "$OGR2OGR_TOOL">/dev/null; then
    echo "This script requires the $OGR2OGR_TOOL tool, aborting."
    exit 2
fi

if [ "$DB" == "" ]; then
	echo "database must be specified."; help; exit 1
fi
if [ "$SCHEMA" == "" ]; then
	echo "schema must be specified."; help; exit 1
fi
if [ "$ARCHIVE" == "" ]; then
	echo "archive must be specified."; help; exit 1
fi
if [ ! -e "$ARCHIVE" ]; then
	echo "Cannot find archive [$ARCHIVE]."; help; exit 1
fi

echo Starting Geo ingestion ...

expanded_archive=''
decompress_archive "$ARCHIVE"
convert_archive "$expanded_archive" $SOURCE_EPSG $TARGET_EPSG
ingest_archive "$expanded_archive"/$TARGET_EPSG $DB $SCHEMA

echo Ingestion completed.

#EOF
