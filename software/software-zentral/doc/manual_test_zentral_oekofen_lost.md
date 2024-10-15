# Fallback zu Notheizung wenn Oekofen ausfällt

* Erwünschtes Verhalten im Fall von

  * Keine Modbus Kommunikation mit Oekofen
  * Oekofen in Wartung (Kaminfeger)
  * Oekofen im Fehlerzustand (kaputt)

* Erwünschtes Verhalten
  * hsm_zentral verbleibt in
    * state_ok_drehschalterauto_regeln
    * state_ok_drehschalterauto_manual
    * ...
  * 'Fehler'situationen
    * Keine Modbus Kommunikation mit Oekofen möglich:
      * hsm_zentral.modbus_oekofen_registers is auf None gesetzt
      * Resultiert in handler_oekofen.betrieb_notheizung
    * Oekofen in Wartung/Fehlerzustand
      * Für beide Brenner: OekofenRegisters.verfuegbar is False
      * Dies wird zusammengefasst in handler_oekofen.betrieb_notheizung


## Oekofen meldet Störung/Kaminfeger

ACHTUNG: Modbus wird nur im Minuteninvervall abgefragt!

* Precondition

  * Applikation läuft

* Stimuli

  * a) `ScenarioOekofenBrennerStoerung`
    * brenner_idx0 = 0
    * duration_s: 4*60s

* Expected Response

  * Grafana `betrieb_notheizung_prozent`: Datenpunkte erscheinen NICHT, da nur 1 Brenner in Störung

* Stimuli

  * a) `ScenarioOekofenBrennerStoerung`
    * brenner_idx0 = 1  # 1 !!!
    * duration_s: 2 *60s

* Expected Response

  * Grafana `betrieb_notheizung_prozent`: Datenpunkte erscheinen da beide Brenner in Störung
  * Timeout `BrennerError-ERROR` beginnt

* Stimuli

  * a) `ScenarioOekofenBrennerStoerung`
    * läuft ab

* Expected Response

  * Grafana `betrieb_notheizung_prozent`: Datenpunkte erscheinen nicht mehr
  * Timeout `BrennerError-ERROR` verschwindet

* Tests
  * 2024-10-15: success


## Modbus Oekofen fällt aus

ACHTUNG: Modbus wird nur im Minuteninvervall abgefragt!

* Precondition

  * Applikation läuft

* Stimuli

  * a) `ScenarioOekofenModbusNoResponseReceived`
    * duration_s: 120s

* Expected Response

  * Grafana `betrieb_notheizung_prozent`: Datenpunkte erscheinen
  * Grafana `brenner_1|2_uebersicht_prozent`: -100% (Modbus fehler)
  * Nach 120s:
    * Grafana `betrieb_notheizung_prozent`: Datenpunkte erscheinen nicht mehr
    * Timeout `BrennerError-ERROR` verschwindet

* Tests
  * 2024-10-15: success
