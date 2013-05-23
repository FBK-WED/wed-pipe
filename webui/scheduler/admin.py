from django.contrib import admin
from webui.scheduler.models import Scheduler


STATUSES = {
    'S': ('green', 'Success'),
    'F': ('red', 'Fail'),
    'I': ('yellow', 'Invalid'),
    'R': ('orange', 'Running'),
}


class SchedulerAdmin(admin.ModelAdmin):
    """Scheduler model admin customization."""
    list_display = ('content_object', 'created', 'status_renderer')
    list_filter = ['created', 'status']
    date_hierarchy = 'created'

    def status_renderer(self, scheduler):
        status = scheduler.status
        try:
            return '<font color="{}">{}</font>'.format(*STATUSES[status])
        except KeyError:
            return "<pre>{} ?</pre>".format(status)
    status_renderer.allow_tags = True
    status_renderer.short_description = 'Status'

admin.site.register(Scheduler, SchedulerAdmin)
