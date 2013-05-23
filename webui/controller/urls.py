""" urls for controller app
"""
from coffin.views.generic import TemplateView
from django.conf.urls import patterns, url


urlpatterns = patterns(
    'webui.controller.views',

    url(r'^source/$', 'source_list', name='source_list'),
    url(r'^source/create/$', 'source_create', name='source_create'),
    url(r'^source/(?P<pk>\d+)/$', 'source_detail', name='source_detail'),
    url(r'^source/(?P<pk>\d+)/edit/$', 'source_update', name='source_update'),
    url(
        r'^source/(?P<pk>\d+)/start-workflow/$',
        'source_workflow',
        name='source_workflow'
    ),

    url(r'^source/(?P<pk>\d+)/dataset/create/$',
        'dataset_create', name='dataset_create'),
    url(r'^dataset/(?P<pk>\d+)/$', 'dataset_detail', name='dataset_detail'),
    url(r'^dataset/(?P<pk>\d+)/edit/$', 'dataset_update',
        name='dataset_update'),
    url(
        r'^dataset/(?P<pk>\d+)/start-workflow/$',
        'dataset_workflow',
        name='dataset_workflow'
    ),

    url(
        r'^source/(?P<pk>\d+)/fetchmetadata/$',
        'source_fetch_metadata',
        name='source_fetch_metadata'
    ),

    url(
        r'^source/(?P<pk>\d+)/uploadmetadata/$',
        'source_upload_metadata',
        name='source_upload_metadata'
    ),

    url(
        r'^archiveitem/(?P<pk>\d+)/$',
        'archiveitem_detail',
        name='archiveitem_detail'
    ),
    url(
        r'^archiveitem/(?P<pk>\d+)/csv/$',
        'archiveitem_csv',
        name='archiveitem_csv'
    ),
    url(
        r'^archiveitem/(?P<pk>\d+)/refine/create/$',
        'archiveitem_refine_create',
        name='archiveitem_refine_create'
    ),
    url(
        r'^archiveitem/(?P<pk>\d+)/refine/fetch/$',
        'archiveitem_refine_fetch',
        name='archiveitem_refine_fetch'
    ),
    url(
        r'^archiveitem/(?P<pk>\d+)/refine/sync/$',
        'archiveitem_refine_sync',
        name='archiveitem_refine_sync'
    ),
    url(
        r'^archiveitem/(?P<pk>\d+)/refine/push/$',
        'archiveitem_refine_push',
        name='archiveitem_refine_push'
    ),
    url(
        r'^archiveitem/(?P<pk>\d+)/mapped/stats/$',
        'archiveitem_mapped_stats',
        name='archiveitem_mapped_stats'
    ),
    url(
        r'^archiveitem/(?P<pk>\d+)/aggregator/add/$',
        'archiveitem_aggregator_add',
        name='archiveitem_aggregator_add'
    ),
    url(
        r'^archiveitem/(?P<pk>\d+)/aggregator/del/$',
        'archiveitem_aggregator_del',
        name='archiveitem_aggregator_del'
    ),

    url(r'^aggregator/(?P<pk>\d+)/$', 'aggregator_detail',
        name='aggregator_detail'),
    url(r'^aggregator/create/$', 'aggregator_create',
        name='aggregator_create'),
    url(r'^aggregator/(?P<pk>\d+)/edit/$', 'aggregator_update',
        name='aggregator_update'),
    url(r'^aggregator/(?P<pk>\d+)/export-for-silk/$', 'aggregator_export',
        name='aggregator_export'),
    url(r'^aggregator/(?P<pk>\d+)/post/$', 'aggregator_import',
        name='aggregator_import'),
    url(
        r'^aggregator/(?P<pk>\d+)/start-workflow/$',
        'aggregator_workflow',
        name='aggregator_workflow'
    ),
    url(r'^aggregator/$', 'aggregator_list', name='aggregator_list'),

    url(
        r'^tools/refine/batch/$',
        'refine_batch_edit',
        name='refine_batch_edit'
    ),
    url(
        r'^tools/$',
        TemplateView.as_view(
            template_name='controller/tools_list.html'
        ),
        name='tools_list'
    ),
)
