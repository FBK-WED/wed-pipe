CSV README
==========

Description
-----------

  Set of scripts for loading tabular data retrieved from the ScraperWiki API into a PostGres table.

Usage
-----

  Ingest Scraper data:

    $ ./ingest-data.sh -d venturi.fbk-test -s csv -c tripadvisortrentorestaurants
    $ ./ingest-data.sh -d venturi.fbk-test -s csv -c gamberorossotrentinoaltoadigerestaurants
    $ ./ingest-data.sh -d venturi.fbk-test -s csv -c eventisagreeventitrentino

  For more help:

    $ ./ingest-data.sh --help
