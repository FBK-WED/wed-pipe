#from django.conf import settings
from appconf import AppConf


class WED PipeConf(AppConf):

    DISPATCHER_DEFAULT = """
    if file.mime_by_ext == 'application/archive':
        return recurse()

    actions = []

    shp = file.path.endswith(".shp")
    csv = (file.mime_by_ext == 'text/csv' or file.mime_by_origin == 'text/csv')
    xls = (
        file.mime_by_ext == 'application/vnd.ms-excel' or
        file.path.endswith('.xslx')
    )

    if shp:
        actions.append(
            ('geo-configuration', {
             'data': file.path,
             'output': file.path + ".converted.csv",
             'encoding': archive_item.dataset.encoding,
             'proj': archive_item.dataset.projection })
        )

    if shp or csv or xls:
        actions.append(
            ('tab-configuration', {
             'schema' : '',
             'data' : file.path,
             'tablename' : archive_item.tablename,
             'csv_delimiter' : archive_item.dataset.csv_delimiter,
             'csv_quotechar' : archive_item.dataset.csv_quotechar,
             'encoding': archive_item.dataset.encoding })
        )

        if archive_item.rule:
            actions.append(
                ('refine-configuration', {
                 'archiveitem_id' : str(archive_item.pk),
                 'out_file': file.path + '.turtle'})
            )

            actions.append(
                ('rdf-configuration', {
                 'data' : file.path + '.turtle',
                 'graph' : archive_item.datagraph_mapped_name })
            )

        return actions
    else:
        raise UnsupportedDatasetException('Unknown MIMEType')
    """

    DISPOSE_HANDER_DEFAULT = """
    return ( '2rdf-configuration', { 'source' : source.id } )
    """

    class Meta:
        prefix = 'controller'
        proxy = True
settings = WED PipeConf()
