CONTROLLER README
=================

Description
-----------

This module defines the Venturi WED Pipe.

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

On Ubuntu/Debian, we use the guest login and the root vhost in rabbit, so there is no extra configuration to be applied.

For more information see: http://celery.readthedocs.org/en/latest/getting-started/brokers/rabbitmq.html


RabbitMQ Management Plugin
--------------------------

http://www.rabbitmq.com/management.html

http://vpn.venturi.fbk.eu:55672/  (guest/guest)

Celery Running
--------------
cwd = git/controller
$ export PATH="/opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin/:$PATH"
$ ./manage_worker.sh
