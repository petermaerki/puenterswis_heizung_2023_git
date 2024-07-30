# Fehlerhandling DS18

DS18 Sensoren sind immer in redundaten Paaren angeordnet.

Dies gilt für dezentral am Speicher und in der Zentralheizung.


## Logik zur Darstellen von Fehlerhaften Sensoren

* Severity WARNING: Fehlertemperatur=1C
* Severity FATAL:  Fehlertemperatur=20C

| Konfiguration | Zustand DS18 | Fehlertemperatur | Rechentemperatur |
| - | - | :-: | - |
| DS18 x broken | anderer DS18 ok | - | anderer DS18 |
| DS18 x broken | anderer DS18 defekt | FATAL | - |
| - | ein DS18 defekt | WARNING | anderer DS18 |
| - | beide DS18 defekt | FATAL | - |
| - | Beide ok, delta T < 5C | - | erster DS18 |
| - | Beide ok, delta T > 5C | delta T | erster DS18 |
