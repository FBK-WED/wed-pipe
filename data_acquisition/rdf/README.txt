RDF README
==========

Description
-----------

  This module is responsible for loading into the configured Triple Store the given RDF data.

Usage
-----

  Load local file:
    $ ./ingest-data.sh -d './specific_mappingbased_properties_el.nt' -g 'http://spazio/test/1'
  Load plain RDF resource:
    $ ./ingest-data.sh -d http://www.territorio.provincia.tn.it/geodati/788_Comuni_amministrativi___DB_Prior_10k__12_12_2011.rdf -g 'http://spazio/test/2'
  Load compressed RDF resource:
    $ ./ingest-data.sh -d 'http://downloads.dbpedia.org/3.7/el/specific_mappingbased_properties_el.nt.bz2' -g 'http://spazio/test/3'    
