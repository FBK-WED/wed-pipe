""" a jinja2 template loader for coffin, taken from:
https://github.com/GaretJax/coffin/blob/master/coffin/template/loaders.py
"""
import re

from jinja2 import TemplateNotFound
from django.template.loader import BaseLoader, find_template_loader,\
    make_origin
from django.template import TemplateDoesNotExist
from coffin.template.loader import get_template
from django.conf import settings


class Loader(BaseLoader):
    """ A jinja2 template loader
    """
    is_usable = True
    _django_template_source_loaders = None

    def __init__(self, *args, **kwargs):
        super(Loader, self).__init__(*args, **kwargs)

        self._disabled = set()
        self._enabled = set()

        self._disabled_templates = set(
            getattr(settings, 'JINJA2_DISABLED_TEMPLATES', [])
        )

    def is_enabled(self, template_name):
        """ True if jinja2 is enabled on the given template
        """
        if template_name in self._disabled:
            return False
        elif template_name in self._enabled:
            return True
        else:
            # Check and update cache
            for pattern in self._disabled_templates:
                if re.match(pattern, template_name) is not None:
                    self._disabled.add(template_name)
                    return False
            self._enabled.add(template_name)
            return True

    def load_template(self, template_name, template_dirs=None):
        """ the main method: load a template using jinja2 if needed, otherwise
        fallback on default django loaders.
        """
        if self.is_enabled(template_name):
            try:
                template = get_template(template_name)
            except TemplateNotFound:
                raise TemplateDoesNotExist(template_name)
            return template, template.filename
        else:
            return self.get_django_template(template_name, template_dirs)

    def load_template_source(self, template_name, template_dirs=None):
        """ this method (which is abstract in the parent class) is not needed,
         because load_template has been overridden above.
        """
        return None, None

    def get_django_template(self, name, dirs=None):
        """ load a template using django instead of jinja2.
        """
        if self._django_template_source_loaders is None:
            loaders = []
            for loader_name in settings.JINJA2_TEMPLATE_LOADERS:
                loader = find_template_loader(loader_name)
                if loader is not None:
                    loaders.append(loader)
            self._django_template_source_loaders = tuple(loaders)

        for loader in self._django_template_source_loaders:
            try:
                source, display_name = loader(name, dirs)
                return source, make_origin(display_name, loader, name, dirs)
            except TemplateDoesNotExist:
                pass
        raise TemplateDoesNotExist(name)
