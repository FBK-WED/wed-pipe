from django.conf.urls import patterns, include, url

# Comment the next two lines to disable the admin module:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	(r'^console/', 'controller.views.console'),

	# Controls the importer.
	(r'^import/(?P<method>\w+)/$', 'controller.views.fun_import'),

	# Controls the scheduler.
	(r'^scheduler/status/$', 'controller.views.scheduler_status'),
	(r'^scheduler/(?P<method>\w+)/$', 'controller.views.scheduler'),

	# Refine.
	(r'^refine/configuration/(?P<prj_id>\d+)$', 'controller.views.get_refine_rules' ),
	(r'^refine/delete/(?P<prj_id>\d+)$'       , 'controller.views.delete_refine_prj'),
	(r'^refine/put/$'                         , 'controller.views.store_refine_rules'),
	(r'^refine/get/$'                         , 'controller.views.retrieve_refine_rules'),
	(r'^refine/inspect/(?P<dataset_download_url>.+)$', 'controller.views.inspect_dataset'),
	(r'^refine/open/$'                               , 'controller.views.open_in_refine'),

	# Returns info about Workflow configuration.
	(r'^wf/configurations/(?P<conf_name>[^/]+)/$', 'controller.views.wf_configuration_html'),

	# Returns info about ScrapwerWiki configuration.
	(r'^sw/config/$', 'controller.views.scraperwiki_config'),

	# Uncomment the admin/doc line below to enable admin documentation.
	url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

	# Uncomment the next line to enable the admin.
	url(r'^admin/', include(admin.site.urls)),
)

