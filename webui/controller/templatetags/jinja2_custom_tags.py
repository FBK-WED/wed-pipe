from uuid import uuid4

from django.conf import settings
from django.template.defaultfilters import slugify

from coffin import template
from jinja2 import contextfunction


register = template.Library()


@contextfunction
def crispy(context, form):
    from jinja2 import Markup
    from crispy_forms.utils import render_crispy_form \
        as crispy_render_crispy_form

    return Markup(crispy_render_crispy_form(form, context=context))


@register.filter
def silk_id(archive_item):
    """ given an archive_item returns the ID to be used in silk to
     represent its data source.
    """
    a_str = '-'.join(
        (archive_item.dataset.name, archive_item.file_hash)
    )
    return slugify(a_str)[:26]


register.object(crispy)
register.object('uuid', lambda: str(uuid4()))
register.object('settings', settings)
