# Arbeit vom Sonntag

## Tuning

* SW: Timeout nach Kommunikation
* SW: Timeout nach Fehler

* SW: Pause sicherstellen, klare Zeitkonstanten


* LOW: Test: Modbus Stress: Kondensator, Widerstand, Ein/Aus
* LOW: Test: Manuell: Mit Batterie 1 oder 0 überschreiben
* HIGH: Test: Tipptaster in Zentrale: Unterbrechnung von Modbus
* LOW: Störhaus
  * Sendet all 3 Senkunden ein gültiges Modbus packet
    * Zentrale empfängt gültiges Packet, das aber unsinnig ist
    * Packete zu Dezentral werden gestört
    * Packete von Dezentral werden gestört
  * Störhaus ist mit Zentrale verbunden
    * Störhaus wird via PC und USB bedient (run_from_PC)

* HIGH: Internet load
* SPÄTER: Test: Unterbruch zu Internet


## Implementation

* Usecase wenn Heizung da: Requirments aufschreiben
* Review Statemachine Haus
* Review Log
