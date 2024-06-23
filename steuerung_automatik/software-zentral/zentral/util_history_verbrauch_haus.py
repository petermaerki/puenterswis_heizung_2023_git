import dataclasses
import time
from typing import TYPE_CHECKING, List, Optional

from zentral.constants import WHILE_HARGASSNER

if TYPE_CHECKING:
    from zentral.context import Context
    from zentral.hsm_dezentral import HsmDezentral

INTERVAL_VERBRAUCH_HAUS_S = 3600.0


@dataclasses.dataclass
class Messung:
    verbrauch_W: float
    time_s: float


@dataclasses.dataclass
class HistoryVerbrauchHaus:
    _max_length = 3 * 24
    _messwerte: List[Messung] = dataclasses.field(default_factory=list)

    def add(self, messung: Messung) -> None:
        self._messwerte.append(messung)
        if len(self._messwerte) > self._max_length:
            self._messwerte.pop()

    @property
    def avg_leistung_W(self) -> float:
        return sum([m.verbrauch_W for m in self._messwerte]) / len(self._messwerte)


@dataclasses.dataclass
class VerbrauchHaus:
    last_energie_J: float = 0.0
    next_interval_time_s: Optional[float] = None
    """
    Is None if the valve was open.
    As soon as the valve closes, this will be set to start measuring.
    """
    history: HistoryVerbrauchHaus = dataclasses.field(default_factory=HistoryVerbrauchHaus)

    async def update_valve(self, hsm_dezentral: "HsmDezentral", context: "Context") -> None:
        """
        Erkennt raising/falling von valve_open.
        Aktualisiert history sobald interval_s abgelaufen.
        """
        hsm_zentral = context.hsm_zentral
        if WHILE_HARGASSNER:
            valve_open = not hsm_zentral.relais.relais_6_pumpe_ein
        else:
            valve_open = hsm_dezentral.dezentral_gpio.relais_valve_open

        if not hsm_zentral.is_state(hsm_zentral.state_ok_drehschalterauto_regeln):
            return

        if valve_open:
            return

        if self.next_interval_time_s is None:
            # Ventil wurde geschlossen: Ein neues Interval beginnt.
            sp_energie_absolut_J = hsm_dezentral.sp_energie_absolut_J
            if sp_energie_absolut_J is None:
                # Wir haben noch keine Messwerte via modbus erhalten
                return
            self.last_energie_J = sp_energie_absolut_J
            self.next_interval_time_s = time.monotonic() + INTERVAL_VERBRAUCH_HAUS_S
            return

        # Ventil ist geschlossen: Ist ein Interval abgelaufen?
        if time.monotonic() < self.next_interval_time_s:
            return

        # Ein Interval ist abgelaufen
        sp_energie_absolut_J = hsm_dezentral.sp_energie_absolut_J
        if sp_energie_absolut_J is None:
            # Wir haben noch keine Messwerte via modbus erhalten
            return

        interval_energie_J = self.last_energie_J - sp_energie_absolut_J
        self.last_energie_J = sp_energie_absolut_J
        messung = Messung(verbrauch_W=interval_energie_J / INTERVAL_VERBRAUCH_HAUS_S, time_s=self.next_interval_time_s - INTERVAL_VERBRAUCH_HAUS_S / 2.0)
        self.history.add(messung=messung)
        self.next_interval_time_s += INTERVAL_VERBRAUCH_HAUS_S

        # Avoid cyclic import
        from zentral.util_influx import InfluxRecords

        r = InfluxRecords(haus=hsm_dezentral._haus)
        r.add_fields(fields={"sp_verbrauch_W": messung.verbrauch_W})
        await context.influx.write_records(records=r)

    @property
    def avg_leistung_W(self) -> float:
        # TODO: Fehlerhandling falls noch keine Messpunkt verfügbar
        return self.history.avg_leistung_W
