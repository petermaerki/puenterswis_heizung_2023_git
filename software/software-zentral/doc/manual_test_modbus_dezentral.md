# Fehler Modbus Dezentral

Fehler bei der Kommunikation mit den Häusern.

* Ziel

  Wie verhält sich die Applikation falls ein Haus nicht via Modbus erreichbar ist?


## Modbus fällt aus

* Precondition

  * Applikation läuft

* Stimuli

  * a) `ScenarioHausModbusNoResponseReceived`

    * Haus: 13
    * duration_s: 120

  * b) Haus ausstecken

* Expected Response

  * Grafana `Dezentral Modbus History Percent OK`: 100% -> 0%
  * Grafana `Dezentral Hsm`: hsm_state `ok` -> `error`
  * Grafana `Dezentral Valve open (simulation)`: Datenpunkte fehlen
  * pcb_dezentral: Ventil öffnet (nach 10min MODBUS_WATCHDOG_MS und reboot)
  * Der controller berücksichtigt dieses Haus nicht mehr. Dies muss mit dem Debugger verifiziert werden (`if not hsm_dezentral.is_state(hsm_dezentral.state_ok):`)

* Tests
  * 2024-07-28: success

## Modbus funktioniert wieder

* Stimuli

  * a) `ScenarioClearScenarios`
  * b) Haus einstecken

* Expected Response

  * Grafana `Dezentral Modbus History Percent OK`: 0% -> 100%
  * Grafana `Dezentral Hsm`: hsm_state `error` -> `ok`
  * Grafana `Dezentral Valve open (simulation)` Datenpunkte wieder vorhanden
  * pcb_dezentral: Ventil schliesst (falls genug Wärme vorhanden)
  * Der controller berücksichtigt dieses Haus wieder.

* Tests
  * 2024-07-28: success
