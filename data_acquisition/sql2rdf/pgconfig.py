"""
Handle the configuration of Postgres and Virtuoso
"""


class PGConfig(object):
    """
    Lazily holds connection configuration
    """

    def __init__(self):
        self._cfg = None
        self._constr = None
        self._constr_meta = None

    def __getattr__(self, item):
        try:
            return self.cfg[item]
        except KeyError:
            raise AttributeError(
                "class '{}' has no attribute '{}'".format(
                    self.__class__.__name__, item)
            )

    @property
    def constr(self):
        if not self._constr:
            self._constr = self.gen_constr()
        return self._constr

    @property
    def constr_meta(self):
        if not self._constr_meta:
            self._constr_meta = self.gen_constr(False)
        return self._constr_meta

    @property
    def cfg(self):
        if not self._cfg:
            self._cfg = self.read_config()
        return self._cfg

    @staticmethod
    def read_config(filename=None):
        from data_acquisition.common.utils \
            import read_config as common_read_config

        return common_read_config(filename)

    def gen_constr(self, datadb=True):
        return "host='%s' port='%s' dbname='%s' user='%s' password='%s'" % (
            self.cfg['PSQL_HOST'], self.cfg['PSQL_PORT'],
            datadb and self.cfg['PSQL_DB'] or self.cfg['PSQL_DBC'],
            self.cfg['PSQL_USER'], self.cfg['PSQL_PWD']
        )

## End config stuff
