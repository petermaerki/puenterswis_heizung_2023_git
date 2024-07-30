# Zustand der ds18 Temperatur Sensoren

* Ziel

  Wie verhält sich die Applikation bei fehlerhaften Sensoren.

* Hier geht es um Fehler, die durch Redundanz entschärft werden

## Sensorpaar fällt aus

* Precondition

  * Applikation läuft

* Stimuli

  * a) `ScenarioHausSpDs18PairDisconnected`
    * Haus: 13
    * ds18_index: mitte
    * ds18_ok_percent: 15%
    * duration_s: 120s

  * b) Sensorpaar ausstecken

* Expected Response

  * Grafana `Temperaturen Speicher nur Mitte`: Keine Datenpunkte mehr
  * Grafana `DS18 errors`: Neu erscheint dieses Sensorpaar
