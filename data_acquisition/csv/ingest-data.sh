#!/bin/bash

#
# This script loads archives containing SHP files in PostGres.
#

CURR_DIR="$(cd "$(dirname "$0")"; pwd -P)"

. $CURR_DIR/../common/common.sh || { echo "Error while loading configuration, aborting."; exit 1; }

function help() {
	echo "Usage: $0 [-h|--help] [-i|--inspect] [-d|--database] <database> [-s|--schema] <schema> {-f|--file} <[http://]/path/to/tabular-file>"
}

# Command-line parser.
while [[ $1 == -* ]]; do
	case "$1" in
		-h|--help|-\?) help; exit 0;;
		-i|--inspect)   shift; readonly INSPECT=1 ;;
		-f|--file)      shift; readonly FILE="$1" ; shift;;
		-d|--database)  shift; readonly DB=$1     ; shift;;
		-s|--schema)    shift; readonly SCHEMA=$1 ; shift;;
		--) shift; break;;
		-*) echo "invalid option: $1" 1>&2; help; exit 1;;
	esac
done

if [ "$FILE" == "" ]; then
    echo File must be specified.
    help
    exit 1
fi

filename="$( basename "$FILE" )"
ext="${filename#*.}"
echo Detected extension: $ext
if [[ ${#ext} -gt 3 ]]; then
    echo trying to fix extension ...
    if [[ "$filename" =~ ".csv" ]]; then
        ext=csv
    elif [[ "$filename" =~ ".xlsx" ]]; then
        ext=xlsx
    elif [[ "$filename" =~ ".xls" ]]; then
        ext=xls
    else
        echo "Cannot determine an extension for file $filename, aborting."
        exit 1
    fi
    echo Fixed extension to $ext
fi

[[ "$FILE" =~ "http://" || "$FILE" =~ "https://" ]] && { is_url=1; }
if [ "$INSPECT" == "1" ]; then  # Inspect
    if [ "$is_url" == "1" ]; then # Inspect URL
        wget "$FILE" -O - | in2csv -f $ext | csvstat
    else # Inspect file
        in2csv $FILE | csvstat
    fi
else # Ingest
    if [ "$DB" == "" ]; then # db required
        echo database parameter required to ingest.
        help
        exit 1
    fi
    if [ "$SCHEMA" != "" ]; then # schema optional
        schema="$SCHEMA."
    fi
    # postgresql://wedpipe:XXX@vpn.example.org/wedpipe-test
    connection_string="postgresql://$PSQL_USER:$PSQL_PWD@$PSQL_HOST:$PSQL_PORT/$DB"
    echo Starting ingestion ...
    tablename=$schema$( echo $FILE | md5sum | awk '{print $1}' )
    echo table name: $tablename
    $PSQL -d $DB -c 'DROP TABLE "'$tablename'"' && { echo "Table $tablename deleted successfully."; }
    if [ "$is_url" == "1" ]; then # Ingest from HTTP
        wget "$FILE" -O - | in2csv -f $ext | csvsql --insert --db $connection_string --table "$tablename" || { echo "Error while ingesting data. Aborting."; exit 1; }
    else # Ingest from file
        mime=$( file --mime-encoding "$FILE" | awk '{ print $2}' )
        echo Detected MIME Encoding: $mime
        in2csv -e "$mime" -f "$ext" "$FILE" | csvsql --insert --db "$connection_string" --table "$tablename" || { echo "Error while ingesting data. Aborting."; exit 1; }
    fi
    echo "WFOUT <schema> : <>"
    echo "WFOUT <shp_tables> : <$tablename>"
    echo Ingestion completed.
fi

#EOF
