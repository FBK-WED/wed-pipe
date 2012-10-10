CONTROLLER README
=================

Description
-----------

This module defines the SpazioDati Controller.

Test
----

To test all modules:
  $ workon controller
  (controller)$ DJANGO_SETTINGS_MODULE=webui.settings nosetests --with-coverage --cover-package=controller [--cover-html] [-a '!online']

To produce Jenking compatible output:
  $ workon controller
  (controller)$ DJANGO_SETTINGS_MODULE=webui.settings nosetests --with-coverage --cover-package=controller --with-xunit --cover-erase --cover-xml

Run
---

To run the python scripts:
$ workon controller
$ cd webui/
$ export PYTHONPATH=.
$ export DJANGO_SETTINGS_MODULE=webui.settings
$ manage.py runserver 0.0.0.0:8000

Tasks
-----

    module: PAT
        frequency: once a week
        Actions:
            update pat_geo_idex.html
            download catalog
            ingest SHP data into Spatial DB
            ingest RDF data into TripleStore

    module: OSM
        frequency: once a week
        Actions: donwload and ingest OSM data into Spatial DB

    module: CSV
        frequency: once a day for events at least
        Actions: ingest CSV data into Spatial DB
        Sources: list of scrapers

    module: RDF
        frequency: once a day for events at least
        Actions: ingest RDF data into Triple Store


RabbitMQ Configuration
----------------------

See: http://celery.readthedocs.org/en/latest/getting-started/brokers/rabbitmq.html

$ export PATH="/opt/local/lib/rabbitmq/bin/:$PATH"
$ sudo rabbitmq-server -detached
$ # rabbitmqctl add_user wedpipe 1234
$ # rabbitmqctl add_vhost wedpipevhost
$ # rabbitmqctl set_permissions -p wedpipevhost wedpipe ".*" ".*" ".*"
$ rabbitmqctl status

To stop:
$ sudo rabbitmqctl stop

RabbitMQ Management Plugin
--------------------------

http://www.rabbitmq.com/management.html

http://vpn.example.org:55672/  (guest/guest)

Celery Running
--------------
cwd = git/controller
$ export PATH="/opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin/:$PATH"
$ export DJANGO_SETTINGS_MODULE=webui.settings
$ celeryd -l info -I scheduler.scheduler
$ celeryctl inspect enable_events
$ cd webui ; ./manage.py celerycam
