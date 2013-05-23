# pylint: disable=C0111,C0103


class ClassSettings(object):
    def run(self, settings):
        pass


######## load custom settings, based on the DJANGO_CONF env var
class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def import_(path, global_vars, quiet=False):
    try:
        module = __import__(path, global_vars, locals(), ['*'])
    except ImportError:
        if quiet:
            return
        raise

    Settings = None
    for k, v in vars(module).iteritems():
        if k.startswith('_'):
            continue
        elif k == 'Settings':
            Settings = v
        else:
            global_vars[k] = v

    if Settings:
        context = AttributeDict(global_vars)
        Settings().run(context)
        global_vars.update(context)
