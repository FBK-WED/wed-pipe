"""
Factories for slice app
"""

import factory

from webui.cnmain.utils import Uuid4Attribute
from webui.slice.models import Slicer


class SlicerFactory(factory.Factory):
    """ factory for creating a Slicer instance
    """
    FACTORY_FOR = Slicer

    name = Uuid4Attribute(prefix='slicer')
    query_string = "SELECT DISTINCT ?g WHERE {GRAPH ?g {?a ?b ?c}}"
    fields = 'acheneID, provenance'
