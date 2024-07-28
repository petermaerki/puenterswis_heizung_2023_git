# Verbindung zum Internet verloren

## Internet disconnected

### Disconnect

* Precondition

  * Applikation läuft
  * Verbindung zum Internet ok

* Stimuli

  * Internet **hinter** Switch ausstecken: Der Raspberry Pi soll die Änderung **nicht** mitbekommen.
  * 2 Min warten, da jede Minute ein Datenpunkt (siehe ASYNCIO_TASK_HSM_DEZENTRAL_S)

* Expected Response

  * Applikation läuft weiter:

    ```bash
    journalctl --lines=100 --follow --unit heizung-app.service | grep 'Failed to resolve'
    ```
    
    output 

    ```
    ...urllib3.connectionpool ... Failed to resolve 'www.maerki.com'...
    ```

  * Grafana: 'Temperaturen Speicher' werden nicht mehr aktualisiert

* Tests
  * 2024-07-26: success

### Reconnect

* Stimuli
  
  * Internet wieder verbinden

* Expected Response

  * Einträge in Grafana erscheinen wieder. Keine Datenlücke.

* Tests
  * 2024-07-26: success

## maerki.com down

...
