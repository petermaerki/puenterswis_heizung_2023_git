# Modbus Kommunikation innerhalb des Heizungsraumes

* Ziel

  Wie verhält sich die Applikation bei Kommunikationsfehlern

* Betroffene Slaves
  * Mischventil
  * DAQ
  * Relay
  * Oekofen

## Modbus Übertragungsfehler

### Modbus Unterbruch

* Precondition

  * Applikation läuft

* Stimuli

  * a) `ScenarioMischventilModbusNoResponseReceived` duration_s=20s
  * b) Mischventil: eines von:
    * Modbus ausstecken
    * Modbus kurzschliessen
    * Irgend einen betroffenen Modbus Slave ausschalten


* Expected Response

  * journalctl --lines=100 --follow --unit heizung-app.service

    ```
    ...WARNING - Mischventil: Modbus Error: ScenarioMischventilModbusNoResponseReceived

    ...WARNING - Watchdog modbus-'mischventil' has expired (14.344919553997897s > 10.0s)!
    ```

  * Applikation läuft weiter
    * Nach 10 s (See MODBUS_ZENTRAL_MAX_INACTIVITY_S):
      * Grafana: `hsm_zentral` wechselt in `state_error`
      * Relais öffnen (anlog Stromausfall)
        * 0: automatik,  # TODO: Korrekten Namen einsetzen
        * 6: pumpe_ein,  # TODO: Korrekten Namen einsetzen
        * 7: relais_7_automatik,

* Tests
  * 2024-07-26: success

### Modbus Unterbruch aufgehoben

* Stimuli
  
  * Modbus Verbindung wieder herstellen

* Expected Response

  * Nach 60s (STATE_ERROR_RECOVER_S) terminiert die Applikation und wird nach weiteren 60s (RestartSec=60) vom Service neu gestartet

    * journalctl --lines=100 --follow --unit heizung-app.service
      ```
      ... ERROR - No SignalError occured during 61.253626445999544s. Exit the application, the service will restart it.

      ... heizung-app.service: Main process exited, code=exited, status=42

      ... systemd[1]: Started heizung-app.service - Heizung app
      ```
* Tests
  * 2024-07-26: success
