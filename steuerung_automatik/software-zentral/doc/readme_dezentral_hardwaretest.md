# Dezentral: Hardwaretest

* Dezentral: Taste 1s drücken
  * erwartet: Zentral: Liest Modbus, gpio Taste is gesetzt
  * Zentral: Eintrag influx
  * Zentral: Modbus Dezentral: 'LED ZENTRALE' ein, oder blinken, falls mindestens 1 ds18 fehlerhaft. 
  * Zentral: Modbus Dezentral: Relais valve_open: aus
  * Zentral: Modbus Zentral: Relais 7 automatik: aus
    * Dezentral: Elfero setzt blaues Ventil 
  * Zentral: pause 10s
  * Zentral: Modbus Zentral: Relais 7 automatik: an
    * erwartet: Dezentral: Zentrale schliesst blaues Ventil.
    * erwartet: Dezentral: Relais 'Automatik', roter Indikator.
  * Zentral: pause 10s
  * Zentral: Modbus Dezentral: Relais valve_open: an
    * erwartet: Dezentral: Zentrale öffnet blaues Ventil.
    * erwartet: Dezentral: Relais 'Valve_open' und 'Automatik' roter Indikator.
  * Zentral: Modbus Dezentral: pause 10s
  * Zentral: Modbus Dezentral: 'LED ZENTRALE' aus
  * Zentral: Normalen betriebszustand