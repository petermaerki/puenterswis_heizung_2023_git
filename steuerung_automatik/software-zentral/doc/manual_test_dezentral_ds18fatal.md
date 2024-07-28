# Zustand der ds18 Temperatur Sensoren

* Ziel

  Wie verhält sich die Applikation bei fehlerhaften Sensoren.

* Hier geht es um fatale Fehler
  * Zwei Sensorpaare liefern stark unterschiedliche Temperaturen
  * Ein Sensorpaar fällt aus, also keine ONEWIRE Kommunikation

## Stark unterschiedliche Temperaturen des Sensorpaars

### Fehler einfügen

* Precondition

  * Applikation läuft

* Stimuli

  * a) `ScenarioHausSpTemperatureDiscrepancy`

    * Haus: 13
    * ds18_index: unten_a
    * discrepancy_C: 20
    * duration_s: 120

  * b) Einen Sensor physikalisch erwärmen/abkühlen

* Expected Response

  * Grafana `Temperaturen Speicher nur Mitte`: Keine Datenpunkte mehr
  * Grafana `DS18 errors`: Neu erscheint dieses Sensorpaar mit 10C (DS18_REDUNDANCY_ERROR_DIFF_C)
  * pcb_dezentral: blinkt weiss (Fehler)
  * Grafana `Dezentral Hsm`: hsm_state `ok` -> `error`
  * Grafana `Dezentral Valve open (simulation)`: xx -> open

### Fehler entfernen

* Stimuli

  * a) `ScenarioClearScenarios`
  * b) Einen Sensor physikalisch erwärmen/abkühlen

* Expected Response
  * Selbstheilend: Alle obigen Effekte verschwinden wieder

## Sensorpaar defekt

### Fehler einfügen

* Precondition

  * Applikation läuft

* Stimuli
  * pcb_dezentral: Alle dx18 ausstecken

* Expected Response
  * Wie Test oben, aber:
  * Grafana `DS18 errors`: Neu erscheint dieses Sensorpaar mit 20C (DS18_REDUNDANCY_FATAL_C)

### Fehler entfernen

  * Wie Test oben