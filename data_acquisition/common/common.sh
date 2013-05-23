#
# Common Bash functions.
#

#### BEGIN: configuration ####

# TODO: unify with webui.settings.py
COMMON_DIR="$(cd "$(dirname "$0")"; pwd -P)"

# General.
TMP_DIR=/tmp

# RDF NS
PAT_GRAPH_PREFIX=http://vocab.venturi.fbk.it/pat/

# Spatial
OGR2OGR_TOOL=ogr2ogr
SHP2PGSQL_TOOL=shp2pgsql
OSMFILTER_TOOL=$COMMON_DIR/../tools/osmfilter
OSM2PGSQL_TOOL=osm2pgsql

# ScraperWiki
SW_API='https://api.scraperwiki.com/api/1.0'
SW_CSV_SERVICE="$SW_API/datastore/sqlite?format=csv"

# PostGres
PSQL=psql
PSQL_HOST=vpn.venturi.fbk.eu
PSQL_PORT=5432
PSQL_USER=venturi.fbk
PSQL_PWD=password
# DEFAULT DB
PSQL_DB=controller-data
# WED Pipe (Django) DB
PSQL_DBC=controller-meta

# Virtuoso iSQL
REMOTE_USER=controller
ISQL=isql-vt
ISQL_HOST=localhost
ISQL_PORT=1111
ISQL_USER=dba
ISQL_PWD=dba
VIRTUOSO_DATA=/srv/virtuoso/data
RDF_DIR=rdf

if [ -e /etc/controller.conf ]; then
    # override variables here
    . /etc/controller.conf
fi

#### END:   configuration ####

# export stuff for python sourcing
export PSQL PSQL_HOST PSQL_PORT PSQL_USER PSQL_PWD ISQL ISQL_HOST ISQL_PORT ISQL_USER ISQL_PWD VIRTUOSO_DATA PSQL_DB PSQL_DBC REMOTE_USER

decompress() {
	local archive=$1
	local target=$2

	if [[ "$archive" =~ '.tgz' || "$archive" =~ '.tar.gz' ]]; then
		tar xvfz $archive -C $target || { echo "Error while decompressing archive $archive into $tmp_dir with TAR. Aborting."; exit 1; }
		return
	fi

	if [[ "$archive" =~ '.zip' ]]; then
		unzip $archive -d $target || { echo "Error while decompressing archive $archive into $tmp_dir with ZIP. Aborting."; exit 1; }
		return
	fi

	if [[ "$archive" =~ '.bz2' ]]; then
		bunzip2 $archive || { echo "Error while decompressing archive $archive into $tmp_dir with BZIP. Aborting."; exit 1; }
		mv ${archive/.bz2/} $target
		return
	fi

	echo "Unsupported extension for archive $archive. Aborting."
	exit 1
}

decompress_in_place() {
	local archive=$1

	if [ -d "$archive" ]; then
		echo "Detected folder. Decompressing internal zips ..."
		for zip in $( find "$archive" -name '*.zip' -type f ); do
			unzip -u "$zip" -d "${zip}_expanded" || { echo "Error while decompressing zip $zip , aborting."; exit 1; }
		done
		echo done
		return
	fi
}
