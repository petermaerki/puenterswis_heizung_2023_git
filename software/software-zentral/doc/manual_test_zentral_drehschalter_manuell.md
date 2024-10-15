# Verhalten Drehschalter Manuell


## Drehschalter Manuell: Auto -> Manuell

* Precondition

  * Drehschalter: Auto
  * Applikation läuft
  * Grafana `hsm_zentral_state_value` = `ok_drehschalterauto_regeln`

* Stimuli

  * `ScenarioZentralDrehschalterManuell`
    * duration_s: 120s
  * oder Drehschalter auf `Manuell` stellen

* Expected Response

  * Grafana `hsm_zentral_state_value` = `ok_drehschalterauto_manuell`
  * Messdaten werden weiter nach Grafana geloggt.
  * Ventile und Mischventil werden angezeit, aber nicht angesteuert.

* Stimuli

  * `ScenarioZentralDrehschalterManuell` ist abgelaufen
  * oder Drehschalter auf `Auto` stellen

* Expected Response

  * Grafana `hsm_zentral_state_value` = `ok_drehschalterauto_regeln`
  * Ventile und Mischventil werden wieder angesteuert.

* Tests
  * 2024-10-15: success
