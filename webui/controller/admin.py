"""
Defines custom ModelAdmin implementations for models.
"""
# pylint: disable=R0904,R0201,C0111
import urllib

from django.contrib import admin
from django.contrib import messages
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponseRedirect

from webui.controller.models import Source, Dataset, Rule, ArchiveItem, \
    Aggregator


# pylint: disable=W0613
def show_datasets_for_source(model, request, queryset):
    """Shows all datasets for a specific source."""
    if queryset.count() > 1:
        messages.error(request, 'You can select one source per time.')
    else:
        source = queryset[0]
        return HttpResponseRedirect(
            '/admin/controller/dataset/?source__name__exact=%s' % (
                urllib.quote_plus(source.name),)
        )
# pylint: enable=W0613

show_datasets_for_source.short_description = 'Show datasets for source'


def source_renderer(source_name):
    """Custom source name render."""
    return '<a href="/admin/controller/source/%s">%s</a>' % (
        source_name, source_name
    )


def ext_renderer(ext):
    """Custom extension render."""
    return '<b>%s</b>' % ext if ext is not None else \
        '<font color="grey">No Ext</font>'


def tags_renderer(tags):
    """Custom tag list render."""
    return ', '.join([u'<b>{}</b>'.format(tag.name) for tag in tags])


class SourceAdmin(admin.ModelAdmin):
    """Source model customization."""
    actions = [show_datasets_for_source]
    fieldsets = [
        (
            None, {'fields': ['name', 'description', 'tags', 'user',
                              'dispatcher', 'init_handler', 'dispose_handler',
                              'hash_handler']}),
        ('Scraper', {'fields': ['scraper_name', 'scraper_api_key']})
    ]
    list_display = ('name', 'description', 'tags_renderer', 'user')

    def tags_renderer(self, instance):
        return tags_renderer(instance.tags.all())

    tags_renderer.allow_tags = True
    tags_renderer.short_description = 'Tags'


class ExtensionFilter(SimpleListFilter):
    """Extension list filter."""
    # Filter name.
    title = 'Extension'

    # Filter parameter id.
    parameter_name = 'ext'

    def lookups(self, request, model_admin):
        extension_set = set()
        for dataset in Dataset.objects.all():
            ext = dataset.ext()
            extension_set.add((ext, ext))
        return extension_set

    def queryset(self, request, queryset):
        # return Dataset.objects.all()
        ext = self.value()
        # Dataset.ext_filter._ext = ext
        # return Dataset.ext_filter.all()
        if ext is None:
            return queryset.all()
        return queryset.filter(download__contains=ext)


class DatasetAdmin(admin.ModelAdmin):
    """Dataset model admin customization."""
    fieldsets = [
        (None, {'fields': ['source', 'url', 'update_rule']}),
        ('Metadata',
         {'fields': ['download', 'name', 'description', 'tags', 'curator',
                     'license', 'bounding_box', 'other_meta']}),
    ]
    list_display = (
        'name', 'source_renderer', 'tags_renderer', 'license', 'ext_renderer')
    list_filter = ['source', 'license', ExtensionFilter]

    def source_renderer(self, dataset):
        return source_renderer(dataset.source.name)

    source_renderer.allow_tags = True
    source_renderer.short_description = 'Source'

    def ext_renderer(self, dataset):
        return ext_renderer(dataset.ext())

    ext_renderer.allow_tags = True
    ext_renderer.short_description = 'Ext'

    def tags_renderer(self, instance):
        return tags_renderer(instance.tags.all())

    tags_renderer.allow_tags = True
    tags_renderer.short_description = 'Tags'


class RuleAdmin(admin.ModelAdmin):
    """Rule model admin customization."""
    list_display = ('hash', )


class ArchiveItemAdmin(admin.ModelAdmin):
    """ArchiveItem model admin customization."""
    list_display = ('file_target', 'dataset', 'rule', 'tablename')


class AggregatorAdmin(admin.ModelAdmin):
    """Aggregator model admin customization."""
    list_display = ('name', )


admin.site.register(Source, SourceAdmin)
admin.site.register(Dataset, DatasetAdmin)
admin.site.register(Rule, RuleAdmin)
admin.site.register(ArchiveItem, ArchiveItemAdmin)
admin.site.register(Aggregator, AggregatorAdmin)
