"""
We need this entry point because of the strange python packages behaviour.
"""
import sys
import argparse
import os


sys.path.append(os.path.dirname(os.path.abspath(__name__)))


def pgsql2rdf(args):
    """ convert a DB table into rdf and ingest it
    """
    from data_acquisition.sql2rdf import pgsql2rdf

    if args.dumpall:
        pgsql2rdf.refresh_sources()
    else:
        remove_dir = False
        if not args.chdir:
            from tempfile import mkdtemp
            args.chdir = mkdtemp()
            remove_dir = True

        os.chdir(args.chdir)
        pgsql2rdf.refresh_sources(args.source)

        if remove_dir:
            import shutil
            shutil.rmtree(args.chdir)


def csv(args):
    """ ingest data from a CSV
    """
    from data_acquisition.ingest_csv import ingest_data
    ingest_data.main(args=args)


def shp(args):
    """ ingest data from a SHP
    """
    from data_acquisition.geo import ingest_data
    ingest_data.main(args=args)


def refine(args):
    """ apply Refine rule
    """
    from data_acquisition.refine import apply_rule
    apply_rule.main(args=args)


def rdf(args):
    """ ingest data from an RDF
    """
    from data_acquisition.rdf import ingest_data
    ingest_data.main(args=args)


def main():
    parser = argparse.ArgumentParser(
        description='Entry point for data acquisition python scripts')
    subparsers = parser.add_subparsers(help='sub-command help')

    pgsql2rdf_parser = subparsers.add_parser('pgsql2rdf')
    pgsql2rdf_parser.add_argument('source', default='')
    pgsql2rdf_parser.add_argument('-d', '--chdir', default='')
    pgsql2rdf_parser.add_argument('--dumpall', default=False)
    pgsql2rdf_parser.set_defaults(func=pgsql2rdf)

    csv_parser = subparsers.add_parser('csv', help='ingest data from a CSV')
    csv_parser.add_argument('-i', '--inspect', action='store_true',
                            default=False)
    csv_parser.add_argument('-e', '--erase', action='store_true',
                            default=False)
    csv_parser.add_argument('-d', '--database', default='')
    csv_parser.add_argument('-s', '--schema', default='')
    csv_parser.add_argument('-f', '--file', required=True)
    csv_parser.add_argument('-t', '--tablename', required=True)
    csv_parser.add_argument('-E', '--encoding', required=True)
    csv_parser.add_argument('-D', '--delimiter', required=True)
    csv_parser.add_argument('-q', '--quotechar', required=True)
    csv_parser.set_defaults(func=csv)

    shp_parser = subparsers.add_parser('shp', help='ingest data from a SHP')
    shp_parser.add_argument('-f', '--file', required=True)
    shp_parser.add_argument('-o', '--out_file', required=True)
    shp_parser.add_argument('-E', '--encoding', required=True)
    shp_parser.add_argument('-p', '--proj', required=True)
    shp_parser.set_defaults(func=shp)

    refine_parser = subparsers.add_parser('refine', help='Apply Refine rules')
    refine_parser.add_argument('-a', '--archiveitem_id', required=True)
    refine_parser.add_argument('-o', '--out_file', required=True)
    refine_parser.set_defaults(func=refine)

    rdf_parser = subparsers.add_parser('rdf', help='ingest data from an RDF')
    rdf_parser.add_argument('-f', '--file', required=True)
    rdf_parser.add_argument('-g', '--graph', required=True)
    rdf_parser.set_defaults(func=rdf)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
