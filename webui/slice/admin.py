from django.contrib import admin
from webui.slice.models import Slicer


class SlicerAdmin(admin.ModelAdmin):
    """Slicer model admin customization."""
    list_display = ('name', )


admin.site.register(Slicer, SlicerAdmin)
