""" urls of the whole controller project
"""
from django.conf.urls import patterns, include, url
from django.contrib import admin


admin.autodiscover()


urlpatterns = patterns(
    '',

    url(r'', include('webui.cnmain.urls')),
    url(r'c/', include('webui.controller.urls')),
    url(r's/', include('webui.scheduler.urls')),
    url(r'l/', include('webui.slice.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin/', include(admin.site.urls)),
)
