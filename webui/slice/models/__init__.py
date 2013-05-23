"""
models for slice app
"""

from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import permalink


class Slicer(models.Model):
    """ Slicer model
    """
    name = models.CharField(
        unique=True,
        max_length=1024,
        blank=False,
        validators=[MinLengthValidator(3)]
    )
    query_string = models.TextField()
    fields = models.CharField(
        max_length=2000,
        blank=False,
        default='acheneID, provenance'
    )

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    @permalink
    def get_absolute_url(self):
        return 'slicer_update', (self.pk, )
