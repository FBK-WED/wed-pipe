"""
Factories for webui.scheduler models
"""
from django.contrib.contenttypes.models import ContentType
import factory

from webui.cnmain.utils import Uuid4Attribute
from webui.controller.models import Dataset, Aggregator
from webui.controller.models.factories import DatasetFactory, AggregatorFactory
from webui.scheduler.models import Scheduler


class SchedulerFactory(factory.Factory):
    """ factory for creating a Scheduler instance
    """
    FACTORY_FOR = Scheduler

    status = 'S'
    logger_name = Uuid4Attribute()


class DatasetSchedulerFactory(SchedulerFactory):
    """ factory for creating a Scheduler executed on a dataset
    """
    object_id = factory.LazyAttribute(
        lambda x: DatasetFactory().pk
    )
    content_type = factory.LazyAttribute(
        lambda x: ContentType.objects.get_for_model(Dataset)
    )


class AggregatorSchedulerFactory(SchedulerFactory):
    """ factory for creating a Scheduler executed on an aggregator
    """
    object_id = factory.LazyAttribute(
        lambda x: AggregatorFactory().pk
    )
    content_type = factory.LazyAttribute(
        lambda x: ContentType.objects.get_for_model(Aggregator)
    )
