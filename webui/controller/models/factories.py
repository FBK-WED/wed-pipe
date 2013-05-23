""" factories for instantiating models
"""
from django.conf import settings
import factory

from webui.cnmain.utils import Uuid4Attribute, LoremIpsumAttribute
from webui.controller.models import Source, Dataset, ArchiveItem, Rule, \
    Aggregator


class SourceFactory(factory.Factory):
    """ factory for creating a Source instance
    """
    FACTORY_FOR = Source

    name = Uuid4Attribute(prefix='source')
    description = LoremIpsumAttribute(words=3)
    user_id = 1
    scraper_name = LoremIpsumAttribute(words=2)
    scraper_api_key = Uuid4Attribute()
    dispose_handler = settings.CONTROLLER_DISPOSE_HANDER_DEFAULT
    is_public = True


class DatasetFactory(factory.Factory):
    """ factory for creating a Dataset
    """
    FACTORY_FOR = Dataset

    source = factory.SubFactory(SourceFactory)
    download = Uuid4Attribute()
    url = factory.sequence('http://www.url.com/{0}'.format)
    name = Uuid4Attribute(prefix='dataset')
    curator = 'Topo Gigio'
    license = 'Do What the Fuck You Want to Public License'
    description = LoremIpsumAttribute(paragraphs=1)
    other_meta = '{}'
    csv_delimiter = ','
    csv_quotechar = '"'


class ArchiveItemFactory(factory.Factory):
    """ factory for creating an ArchiveItem
    """
    FACTORY_FOR = ArchiveItem

    dataset = factory.SubFactory(DatasetFactory)
    file_target = factory.Sequence('file_{0}.csv'.format)
    file_hash = "thisisanhash"


class RuleFactory(factory.Factory):
    """ factory for creating a Rule
    """
    FACTORY_FOR = Rule

    rule = '[]'
    hash = "thisisanhash"


class AggregatorFactory(factory.Factory):
    """ factory for creating an Aggregator
    """
    FACTORY_FOR = Aggregator

    name = Uuid4Attribute(prefix='aggregator')
    description = LoremIpsumAttribute(words=3)
    entity_type = settings.TRIPLE_DATABASE['PREFIXES']['sdv1']
    vertex_selector = "g.V('type', 'sd$Something')%limit.id.fill(m)"
    silk_rule = ''
