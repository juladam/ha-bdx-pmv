#Home Assistant Integration - Bordeaux Métropole - Panneaux à message variable

Une clef est nécessaire pour interroger le webservice

https://data.bordeaux-metropole.fr/opendata/key


sensor:
  - platform: bdx_pmv
    bdx_data_key: !secret bdx_data_key