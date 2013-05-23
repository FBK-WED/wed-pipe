SOCRATA Acquisition README
==========================

This tool can be used to:

    - Ingest all available portal views into PostGres; (useful for debugging purposes)
    - Generate the portal metadata JSON to drive the ingestion process from the SD WED Pipe
      (useful to be run within ScraperWiki);
    - Ingest a single dataset URL (used within the workflow).

How to run it
=============

Obtain help
-----------

$ ./ingest.py -h
usage: ingest.py [-h] [--describe] [--describejson] [--importer]
                 [--urlimporter] [--url URL]
                 conf

Handle Socrata API.

positional arguments:
  conf            Tool JSON configuration

optional arguments:
  -h, --help      show this help message and exit
  --describe      Show human readable description for the API.
  --describejson  Show JSON metadata for the API compatible with the SW Meta
                  table.
  --importer      Import all portal data into PostGres.
  --urlimporter   Import specific portal data into PostGres.
  --url URL       The urlimporter target URL

Run Describe
------------

./ingest.py --describe "{\
   \"api\" : {\
       \"host\"   : \"https://dati.lombardia.it\",\
       \"user\"   : \"mostarda@fbk.eu\",\
       \"passwd\" : \"password\",\
       \"token\"  : \"tokenID\"\
   },\
   \"database\" : {\"db\" : \"venturi.fbk-test\", \"schema\" : \"plo\"}\
}"

Run Describe JSON
-----------------

./ingest.py --describejson "{\
   \"api\" : {\
       \"host\"   : \"https://dati.lombardia.it\",\
       \"user\"   : \"mostarda@fbk.eu\",\
       \"passwd\" : \"password\",\
       \"token\"  : \"tokenID\"\
   },\
   \"database\" : {\"db\" : \"venturi.fbk-test\", \"schema\" : \"plo\"}\
}"

Run Importer
------------

./ingest.py --importer "{\
   \"api\" : {\
       \"host\"   : \"https://dati.lombardia.it\",\
       \"user\"   : \"mostarda@fbk.eu\",\
       \"passwd\" : \"password\",\
       \"token\"  : \"tokenID\"\
   },\
   \"database\" : {\"db\" : \"venturi.fbk-test\", \"schema\" : \"plo\"}\
}"

Run URL Importer
-----------------

./ingest.py --urlimporter --url 'https://dati.lombardia.it/api/views/xy9p-k9bj.json' "{\
   \"api\" : {\
       \"host\"   : \"https://dati.lombardia.it\",\
       \"user\"   : \"mostarda@fbk.eu\",\
       \"passwd\" : \"password\",\
       \"token\"  : \"tokenID\"\
   },\
   \"database\" : {\"db\" : \"venturi.fbk-test\", \"schema\" : \"plo\"}\
}"
