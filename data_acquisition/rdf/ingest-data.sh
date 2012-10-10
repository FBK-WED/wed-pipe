#!/bin/bash

CURR_DIR="$(cd "$(dirname "$0")"; pwd -P)"

. $CURR_DIR/../common/common.sh || { echo "Error while loading common.sh module. Aborting."; exit 1; }

function help() {
	echo "Usage: $0 [-h|--help] {-d|--data} <url-to-data> {-g|--graph} <graph>"
}

# Command-line parser.
while [[ $1 == -* ]]; do
	case "$1" in
		-h|--help|-\?) help; exit 0;;
		-d|--data)  shift; readonly DATA="$1"  ; shift;;
		-g|--graph) shift; readonly GRAPH="$1" ; shift;;
		--) shift; break;;
		-*) echo "invalid option: $1" 1>&2; help; exit 1;;
	esac
done
if [ "$DATA" == "" ]; then
	echo "<data> must be defined."; help; exit 1
fi
if [ "$GRAPH" == "" ]; then
	echo "<graph> must be defined."; help; exit 1
fi

# Download RDF file.
mkdir -p $VIRTUOSO_DATA/$RDF_DIR
if [[ "$DATA" =~ 'http://' || "$DATA" =~ 'https://' ]]; then
		graph_dir=${DATA/\//_}
		graph_dir=${graph_dir/:/__}
	data_file=$VIRTUOSO_DATA/$RDF_DIR/$graph_dir
	rm $data_file
	wget "$DATA" -O $data_file && { echo "RDF Data $DATA downloaded."; } || { echo "Error while downloading RDF data $DATA . Aborting."; exit 1; }
else
	data_file=$VIRTUOSO_DATA/$RDF_DIR/$(basename $DATA)
	rm $data_file
	cp $DATA $data_file || { echo "Error while copying data $DATA to data_file $data_file"; exit 1; }
fi

# Converting to a format suitable for Virtuoso.
if [[ "$data_file" =~ '.bz2' ]]; then
	zip_file=${data_file/bz2/gz}
	echo Converting "bz2 file to gzip into $zip_file ..."
	bunzip2 $data_file -c | gzip > $zip_file || { echo "Error while converting file, aborting."; exit 1; }
	data_file="$zip_file"
	echo done
fi

# Ingest RDF file.
$ISQL localhost:$ISQL_PORT $ISQL_USER $ISQL_PWD EXEC="SPARQL CLEAR GRAPH<$GRAPH>; DB.DBA.ld_file('"$data_file"', '"$GRAPH"');" || { echo "Error while processing file."; exit 1; }

exit 0
