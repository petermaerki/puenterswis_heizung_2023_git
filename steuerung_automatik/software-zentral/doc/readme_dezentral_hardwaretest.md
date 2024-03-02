OBSOLETE!

# Dezentral: Hardwaretest

Generell:
    * Zentral: Modbus Dezentral: 'LED ZENTRALE' aus, oder blinken, falls mindestens 1 ds18 fehlerhaft. 

* Dezentral: Taste 1s drücken
  * erwartet: Zentral: Liest Modbus, gpio Taste ist gesetzt
  * Zentral: hsm: state_error_hardwaretest_01
    * Zentral: Eintrag influx
    * Zentral: Modbus Dezentral: 'LED ZENTRALE' ein
    * Zentral: Modbus Dezentral: Relais valve_open: aus
    * Zentral: Modbus Zentral: Relais 7 automatik: aus
    * Zentral: pause 10s
  * Zentral: hsm: state_error_hardwaretest_02
    * Zentral: Modbus Zentral: Relais 7 automatik: an
      * erwartet: Dezentral: Zentrale schliesst blaues Ventil.
      * erwartet: Dezentral: Relais 'Automatik', roter Indikator.
    * Zentral: pause 10s
  * Zentral: hsm: state_error_hardwaretest_03
    * Zentral: Modbus Dezentral: Relais valve_open: an
      * erwartet: Dezentral: Zentrale öffnet blaues Ventil.
      * erwartet: Dezentral: Relais 'Valve_open' und 'Automatik' roter Indikator.
    * Zentral: pause 10s
  * Zentral: Normalen betriebszustand
