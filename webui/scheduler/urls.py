"""
Urls for scheduler app
"""

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'webui.scheduler.views',

    url(
        r'^task/(?P<task_id>[\da-f-]+)/$',
        'scheduler_result_detail_view',
        name='scheduler_result_detail_view'
    ),

    url(
        r'^scheduler/(?P<pk>\d+)/$',
        'scheduler_detail',
        name='scheduler_detail'
    ),

    url(
        r'^scheduler/$',
        'scheduler_list',
        name='scheduler_list'
    ),

    # url(
    #     r'^task/$',
    #     'scheduler_result_list_view',
    #     name='scheduler_result_detail_view'
    # ),
)
