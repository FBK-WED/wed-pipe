import os
import sys
import envoy

webuidir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, webuidir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'webui.settings'

from django.conf import settings
from data_acquisition.utils import print_error_result


def delete_table(psql_on_db, tablename):
    print "Deleting table..."
    result = envoy.run(
        """{psql} -c 'DROP TABLE "{tablename}"'""".format(
            psql=psql_on_db, tablename=tablename
        )
    )
    if result.status_code == 2:
        print_error_result(result, "Error while executing command")
        exit(1)
    elif result.status_code == 1:
        print "Table", tablename, "didn't exist"
    else:
        print "Table", tablename, "dropped successfully"


def main(args):
    DATABASE = settings.TABULAR_DATABASE

    _, ext = os.path.splitext(args.file)
    ext = ext.strip('.').lower()

    print "Detected extension: " + ext

    is_url = args.file.startswith(('http://', 'https://'), )
    if args.inspect:
        if is_url:
            cmd = 'wget "{filename}" -O - | in2csv --no-inference -f {ext} ' \
                  '| csvstat'.format(filename=args.file, ext=ext)
        else:
            cmd = 'csvstat "{filename}"'.format(filename=args.file)

        result = envoy.run(cmd)
        print result.std_out
        exit(0)

    dbname = args.database
    dbport = DATABASE.get("PORT")
    dbhost = DATABASE.get('HOST')
    if not dbname:
        print 'Setting db to default:', DATABASE['NAME']
        dbname = DATABASE['NAME']

    psql_on_db = "psql -d {dbname} -U {dbuser} -p {dbport} -h {dbhost}" \
                 "".format(
                     dbname=dbname,
                     dbuser=DATABASE['USER'],
                     dbport=dbport or '5432',
                     dbhost=dbhost or 'localhost',
                 )

    connection_string = "postgresql://{dbuser}:{dbpass}@" \
                        "{dbhost}:{dbport}/{dbname}".format(
                            dbuser=DATABASE['USER'],
                            dbpass=DATABASE['PASSWORD'],
                            dbhost=dbhost or 'localhost',
                            dbport=dbport or '5432',
                            dbname=dbname
                        )

    print "starting ingestion"

    tablename = args.tablename
    print "table name:", tablename

    if args.erase:
        delete_table(psql_on_db, tablename)
        exit(0)

    delete_table(psql_on_db, tablename)

    delimiter_options = "-d '{}'".format(args.delimiter)
    if args.delimiter == '\\t':
        delimiter_options = '--tabs'
    # hack: quotechar is given always escaped (see tab-configuration.json)
    if args.quotechar.startswith('\\') and len(args.quotechar) > 1:
        args.quotechar = args.quotechar[1:]
    separator = iter(frozenset(('"', "'")) - frozenset(args.quotechar)).next()
    quotechar_options = "-q {0}{1}{0}".format(separator, args.quotechar)

    mime_encoding = args.encoding
    if not mime_encoding:
        result = envoy.run(
            'file --brief --mime-encoding "{}"'.format(args.file)
        )
        mime_encoding = result.std_out.strip()
    print "Using MIME encoding:", mime_encoding

    if is_url:
        cmd = """wget "{filename}" -O - |
        in2csv -f {ext} {delimiter_opts} {quotechar_opts} |
        csvsql --no-constraints {delimiter_opts} {quotechar_opts} --insert --db
        "{connection_string}" --table "{tablename}" --maxfieldsize 10485760
        -e "{mime}" --no-inference -""".format(
            filename=args.file,
            ext=ext,
            connection_string=connection_string,
            tablename=tablename,
            delimiter_opts=delimiter_options,
            quotechar_opts=quotechar_options,
            mime=mime_encoding,
        )

        result = envoy.run(cmd)
        if result.status_code:
            print_error_result(
                result, "Error while ingesting data. Aborting."
            )
            exit(1)
    else:
        # Note: the --maxfieldsize option is set to 10MB

        if ext in ("xls", "xlsx"):
            cmd = r"""
                in2csv -f {ext} {delimiter_opts} {quotechar_opts}
                "{filename}" | csvsql --no-constraints {delimiter_opts}
                {quotechar_opts} --insert -e "{mime}" --db
                "{connection_string}" --table "{tablename}"
                --maxfieldsize 10485760 --no-inference -
            """
        else:
            # Note: the -z option is set to 10MB
            cmd = r"""
                csvsql --no-constraints {delimiter_opts} {quotechar_opts}
                       --insert -e "{mime}" --db "{connection_string}"
                       --table "{tablename}" "{filename}"
                       --maxfieldsize 10485760 --no-inference
                """

        cmd = cmd.format(
            mime=mime_encoding,
            ext=ext,
            filename=args.file,
            connection_string=connection_string,
            tablename=tablename,
            delimiter_opts=delimiter_options,
            quotechar_opts=quotechar_options,
        )

        result = envoy.run(cmd)
        if result.status_code:
            print_error_result(result, "Error while ingesting data" + cmd)
            exit(1)

    print "Ingestion completed."
