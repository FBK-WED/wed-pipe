PAT CKAN README
===============

Introduction
------------

This module contains scripts to ingest data from the Portale Geocartografico Trentino (http://www.territorio.provincia.tn.it/)
to a CKAN instance.

How to run
----------

The main script ingest.py accepts a dump of the HTML page of the portal index. A snapshot of the index as been included in the repo. Instructions to regenerate it can be found within the ../pat module.

To run the script first check that the CKAN_HOST and CKAN_API_KEY into ingest.py are correct.
The run the following command:

    $ ./ingest.py ../pat/index.html