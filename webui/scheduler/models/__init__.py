"""
Scheduler: list of scheduled Datasets, every Schedule is associated to the
           latest execution of a  Dataset.
"""
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import permalink
from django_extensions.db.models import TimeStampedModel


class Scheduler(TimeStampedModel):
    """ model for storing the execution status of something
    (the Source/Dataset workflow, Aggregator, ...)
    """
    SUCCESS = 'S'
    FAIL = 'F'
    INVALID = 'I'
    RUNNING = 'R'
    INCOMPLETE = 'N'

    STATUSES = (
        (SUCCESS, 'Success'),
        (FAIL, 'Fail'),
        (INVALID, 'Invalid'),
        (RUNNING, 'Running'),
        (INCOMPLETE, 'Incomplete'),
    )

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    status = models.CharField(
        max_length=1,
        choices=STATUSES,
        help_text="Last execution status"
    )

    error = models.TextField(
        blank=True,
        null=True,
        help_text="Last detected error (null if no error was raised)"
    )

    # A JSON containing the workflow execution input parameters.
    in_params = models.TextField(
        blank=True,
        null=True,
        help_text="Last execution input params"
    )

    # A JSON containing the workflow execution output parameters.
    out_params = models.TextField(
        blank=True,
        null=True,
        help_text="Last execution output params"
    )

    logger_name = models.CharField(
        help_text='Name of the logger that stored run info',
        max_length=64,
    )

    def __unicode__(self):
        return u"[{0}] {1} {2} - {3}".format(
            self.content_label,
            self.content_object.name,
            str(self.created),
            'SUCCESS' if self.status == self.SUCCESS else 'FAIL'
        )

    @property
    def content_label(self):
        """
        Returns a label for the Scheduler's content_object
        """
        mapping = {
            "source": "S",
            "dataset": "D",
            "aggregator": "A",
        }
        return mapping.get(self.content_type.model, '?')

    @permalink
    def get_absolute_url(self):
        return 'scheduler_detail', (self.pk,)
