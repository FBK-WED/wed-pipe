""" urls for cnmain app
"""
from django.conf.urls import patterns, url


urlpatterns = patterns(
    'webui.cnmain.views',

    url(r'^$', 'index', name='index'),
    url(r'^sparql/$', 'sparql_view', name='sparql'),
    url(r'^login/$', 'login_view', name='login'),
    url(r'^logout/$', 'logout_view', name='logout'),
)
