https://github.com/hmaerki/webserver_hosteurope_grafana/blob/main/README_maerki-2024-01-09a.md


# https://docs.influxdata.com/influxdb/cloud/reference/key-concepts/data-elements/

https://docs.influxdata.com/influxdb/cloud/api-guide/client-libraries/python/

https://github.com/influxdata/influxdb-client-python

https://github.com/influxdata/influxdb-client-python/blob/master/examples/asynchronous.py



https://github.com/nanophysics/pico_nano_monitor/blob/main/influxdb_structure.py

```python
measurementExample = [
    {
        "measurement": "pico_emil",  # a measurement has one 'measurement'. It is the name of the pcb.
        "fields": {
            "temperature_C": "23.5",
            "humidity_pRH": "88.2",
        },
        "tags": {
            "setup": "zeus",
            "room": "B15",
            "position": "hintenLinks",
            "user": "pmaerki",
        },
    },
]
``` 


# Struktur für Heizung 2023
"measurement": "Heizung"

        dict_tags = {
            "position": "haus_08",  # "zentral"
            "etappe": "bochs",  # "puent"
            "haus": 8,
        }

        # Fields für Dezentral
        # sp_oben_temperatureC
        # sp_open_errorC
        # sp_mitte_temperatureC
        # sp_mitte_errorC
        # sp_unten_temperatureC
        # sp_unten_errorC
        # ventil_open

        # Fields fuer Zentral
        # Tbv1_C
        # energy_valve_open

