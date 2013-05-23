""" utility functions for data_acquisition scripts in python
"""
from os import environ  # do not remove
from os.path import join, dirname, abspath
from subprocess import Popen, PIPE


def read_config(filename=None):
    """ read the script default configuration from common/common.sh
    """
    if not filename:
        filename = join(dirname(abspath(__file__)), "../common/common.sh")

    # Read defaults from controller configuration
    cfg = source(filename, update=False, clean=True)
    # exported vars: PSQL psql.HOST psql.PORT psql.USER psql.PWD ISQL
    # ISQL_PORT ISQL_USER ISQL_PWD VIRTUOSO_DATA psql.DB psql.DBC

    return cfg


def source(script, update=True, clean=True):
    """
    Source variables from a shell script
    import them in the environment (if update==True)
    and report only the script variables (if clean==True)
    """
    global environ

    environ_back = None

    if clean:
        environ_back = dict(environ)
        environ.clear()

    pipe = Popen(". %s; env" % script, stdout=PIPE, shell=True)
    data = pipe.communicate()[0]

    env = dict(line.split("=", 1) for line in data.splitlines())

    if clean:
        # remove unwanted minimal vars
        env.pop('LINES', None)
        env.pop('COLUMNS', None)
        environ.update(environ_back)

    if update:
        environ.update(env)

    return env
