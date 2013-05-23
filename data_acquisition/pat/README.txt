PAT README
==========

Description
-----------

  Set of scripts to scrape the PAT (Provincia Autonoma Trentino) Spatial Index.

Usage
-----

  Update the geo catalog index manually (this operation has not yet automated) using a web browser to open first the URL: 

    http://www.territorio.provincia.tn.it/portal/server.pt?open=512&objID=862&&PageID=32157&mode=2&in_hi_userid=18720&cached=true

  then having the session correctly configured open the URL:

     http://www.territorio.provincia.tn.it/portal/server.pt/gateway/PTARGS_0_18720_2521_862_0_43/http%3B/172.20.3.95%3B8380/geoportlet/srv/it/main.present.embedded?from=1&to=160

  and save the retrieved source content into the pat_geo_index.html file.

  Download the data:

    $ ./download_data.py -i /path/to/pat_geo_index.html -s /path/to/archive

  OR alternatively:

  Generate the CSV of the PAT metadata:

    $ ./download_data.py -i /path/to/pat_geo_index.html -c
