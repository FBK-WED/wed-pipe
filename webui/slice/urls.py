"""
Urls for slice app
"""

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'webui.slice.views',

    url(r'^slicer/$', 'slicer_list', name='slicer_list'),
    url(r'^slicer/(?P<pk>\d+)/$', 'slicer_update',
        name='slicer_update'),
    url(r'^slicer/query/$', 'slicer_query',
        name='slicer_query'),
    url(r'^slicer/create/$', 'slicer_create',
        name='slicer_create'),

    url(
        r'^slicer/(?P<pk>\d+)/dump/$',
        'slicer_dump',
        name='slicer_dump'
    ),
)
