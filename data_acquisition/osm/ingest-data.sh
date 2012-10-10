#!/bin/bash

#
# This script downloads, converts and install OSM data into PortGres.
#

CURR_DIR="$(cd "$(dirname "$0")"; pwd -P)"

. $CURR_DIR/../common/common.sh

function download_archive() {
	local target="$1"
	local destination="$2"
	
	echo Downloading target $target into dir $destination ...
	mkdir $destination
	wget "$target" -O $2/$(basename $target) || { echo "Error while downloading archive. Aborting."; exit 1; }
	echo done.
}

function ingest_archive() {
	local archive=$1
	local decompressed=$2
	local db=$3
	local schema=$4
	
	# Decompression.
	echo Ingesting archive $archive ...
	rm $decompressed
	mkdir $decompressed || { echo "Cannot create decompression dir. Aborting."; exit 1; }
	echo Decompressing archive $archive into dir $decompressed ...
	decompress $archive $decompressed
	echo done.
	
	# OSM filtering.
	osm_file=$(ls $decompressed/*.osm)
	osm_file_filtered=${osm_file}.filtered
	echo Filtering OSM file $osm_file into $osm_file_filtered ...
	$OSMFILTER_TOOL $osm_file \
		--keep='tourism=alpine_hut =attraction =artwork =museum =viewpoint =monument amenity=arts_centre =theatre barrier=city_wall geological=palaeontological_site \
				historic=castle =fort =memorial =monument =ruins =building =manor tourism=alpine_hut =attraction =artwork =museum =viewpoint =monument' > $osm_file_filtered
	echo done.
	
	# OSM data ingestion
	$PSQL -d $db -c "DROP SCHEMA IF EXISTS $schema CASCADE;" || { echo "Error while dropping schema $schema. Aborting."; exit 1; }
	$PSQL -d $db -c "CREATE SCHEMA $schema;"                 || { echo "Error while creating schema $schema. Aborting."; exit 1; }
	$PSQL -d $db -c 'ALTER DATABASE "'$db'" SET search_path='$schema',public;' || { echo "Error while setting primary schema to '$schema'. Aborting."; exit 1; }
	$OSM2PGSQL_TOOL -d $db -p osm -P $PSQL_PORT -c -v $osm_file_filtered         || { echo "Error while ingesting OSM data."; exit 1; }
	$PSQL -d $db -c 'ALTER DATABASE "'$db'" RESET search_path'                 || { echo "Error while resetting default schema. Aborting."; exit 1; }
	
	echo Archive ingestion done.
}

function help() {
	echo "Usage: $0 [-h|--help] {-d|--database} <db> {-s|--schema} <schema> {-a|--archive} <archive-url>"
}

# Command-line parser.
while [[ $1 == -* ]]; do
	case "$1" in
		-h|--help|-\?) help; exit 0;;
		-d|--database) shift; readonly DB="$1"          ; shift;;
		-s|--schema)   shift; readonly SCHEMA="$1"      ; shift;;
		-a|--archive)  shift; readonly ARCHIVE_URL="$1" ; shift;;
		--) shift; break;;
		-*) echo "invalid option: $1" 1>&2; help; exit 1;;
	esac
done

if [ "$DB" == "" ]; then
	echo "database must be specified."; help; exit 1
fi
if [ "$SCHEMA" == "" ]; then
	echo "schema must be specified."; help; exit 1
fi

if [ "$ARCHIVE_URL" == "" ]; then
	echo "archive must be specified."; help; exit 1
fi

archive_dir=$TMP_DIR/sd-$(date +%s)
download_archive $ARCHIVE_URL $archive_dir
archive=$(ls $archive_dir/*.bz2)
ingest_archive $archive $archive_dir/decompressed $DB $SCHEMA

echo Ingestion completed.
