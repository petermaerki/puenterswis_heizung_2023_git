from __future__ import annotations

import dataclasses
import logging
import time
from typing import TYPE_CHECKING, Iterator, Optional

from zentral.util_persistence import Persistence

if TYPE_CHECKING:
    from zentral.context import Context
    from zentral.hsm_dezentral import HsmDezentral

INTERVAL_VERBRAUCH_HAUS_S = 3600.0
LEAD_TIME_VERBRAUCH_HAUS_S = 600.0

logger = logging.getLogger(__name__)

_TAG_VERBRAUCH_W = "verbrauch_W"
_TAG_TIME_S = "time_s"


@dataclasses.dataclass
class Messung:
    verbrauch_W: float
    time_s: float

    @property
    def to_dict(self) -> dict:
        "Deserialize for persistence"
        return {_TAG_VERBRAUCH_W: self.verbrauch_W, _TAG_TIME_S: self.time_s}

    @staticmethod
    def from_dict(m: dict) -> Messung:
        "Serialize for persistence"
        return Messung(verbrauch_W=m[_TAG_VERBRAUCH_W], time_s=m[_TAG_TIME_S])


class HistoryVerbrauchHaus:
    DURATION_24h_s = 24 * 3600
    BAND_1h_s = 3600

    def __init__(self, persistence: Persistence) -> None:
        self._max_length = 3 * 24
        self._messwerte: list[Messung] = []
        self._persistence = persistence
        self._load_data()

    def _load_data(self) -> None:
        """
        Load data from persistence file.
        """
        data = self._persistence.get_data()
        if data is None:
            # No persistence file found
            return
        assert isinstance(data, list)
        for m in data:
            assert isinstance(m, dict)
            self._messwerte.append(Messung.from_dict(m))

    def add(self, messung: Messung) -> None:
        self._messwerte.append(messung)
        if len(self._messwerte) > self._max_length:
            self._messwerte.pop(0)

        # Store data to persistence file.
        data = [m.to_dict for m in self._messwerte]
        self._persistence.push_data(data=data)

    @property
    def verbrauch_avg_W(self) -> Optional[float]:
        """
        return None if no data available
        """
        messwerte_count = len(self._messwerte)
        if messwerte_count == 0:
            return None
        return sum([m.verbrauch_W for m in self._messwerte]) / messwerte_count

    def iter_verbrauch(self, time_s: float) -> Iterator[float]:
        """
        Loop über die Messwerte.
        Falls ein Messwerte zur selben Tageszeit passt: Zurückgeben.
        """
        for messwert in self._messwerte:
            # TODO: 2024-12-31: Nachfolgende zwei Zeilen löschen
            if messwert.time_s < 100000:
                continue
            modulo_24h_s = (time_s - messwert.time_s) % self.DURATION_24h_s
            if modulo_24h_s < self.BAND_1h_s:
                yield messwert.verbrauch_W


class VerbrauchHaus:
    def __init__(self, persistence: Persistence) -> None:
        self.last_energie_J: Optional[float] = None
        """
        Is None during LEAD_TIME_VERBRAUCH_HAUS_S
        """
        self.next_interval_time_s: Optional[float] = None
        """
        Is None if the valve was open.
        As soon as the valve closes, this will be set to start measuring.

        Debug using: ssh -p 8022 localhost
        ctx.config_etappe.haeuser[8].status_haus.hsm_dezentral.verbrauch.next_interval_time_s
        ctx.config_etappe.haeuser[8].status_haus.hsm_dezentral.sp_energie_absolut_J
        ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt
        ctx.hsm_zentral._state_actual.full_name
        """
        self.history: HistoryVerbrauchHaus = HistoryVerbrauchHaus(persistence=persistence)

    async def update_valve(self, hsm_dezentral: "HsmDezentral", context: "Context") -> None:
        """
        Erkennt raising/falling von valve_open.
        Aktualisiert history sobald interval_s abgelaufen.
        """
        hsm_zentral = context.hsm_zentral
        valve_open = hsm_dezentral.dezentral_gpio.relais_valve_open

        if not hsm_zentral.is_state(hsm_zentral.state_ok_drehschalterauto):
            self.next_interval_time_s = None
            return

        if valve_open:
            self.next_interval_time_s = None
            return

        if self.next_interval_time_s is None:
            # Ventil wurde geschlossen: LEAD_TIME_VERBRAUCH_HAUS_S beginnt.
            self.last_energie_J = None
            self.next_interval_time_s = time.monotonic() + LEAD_TIME_VERBRAUCH_HAUS_S
            return

        # Ventil ist geschlossen: Ist INTERVAL_VERBRAUCH_HAUS_S/INTERVAL_VERBRAUCH_HAUS_S abgelaufen?
        remaining_s = self.next_interval_time_s - time.monotonic()
        if remaining_s > 0:
            return

        sp_energie_absolut_J = hsm_dezentral.sp_energie_absolut_J
        if sp_energie_absolut_J is None:
            # Wir haben noch keine Messwerte via modbus erhalten
            return
        last_energie_J = self.last_energie_J
        self.last_energie_J = sp_energie_absolut_J

        if last_energie_J is None:
            # LEAD_TIME_VERBRAUCH_HAUS_S ist abgelaufen
            # Starte ein INTERVAL_VERBRAUCH_HAUS_S
            self.next_interval_time_s += INTERVAL_VERBRAUCH_HAUS_S
            return

        # INTERVAL_VERBRAUCH_HAUS_S ist abgelaufen
        interval_energie_J = last_energie_J - sp_energie_absolut_J
        messung = Messung(
            verbrauch_W=interval_energie_J / INTERVAL_VERBRAUCH_HAUS_S,
            # time_s=self.next_interval_time_s - INTERVAL_VERBRAUCH_HAUS_S / 2.0,
            time_s=time.time(),
        )
        self.history.add(messung=messung)
        self.next_interval_time_s += INTERVAL_VERBRAUCH_HAUS_S

        # Avoid cyclic import
        from zentral.util_influx import InfluxRecords

        r = InfluxRecords(haus=hsm_dezentral.haus)
        r.add_fields(fields={"sp_verbrauch_W": messung.verbrauch_W})
        verbrauch_avg_W = self.verbrauch_avg_W
        if verbrauch_avg_W is not None:
            r.add_fields(fields={"sp_verbrauch_avg_W": verbrauch_avg_W})
        await context.influx.write_records(records=r)

    @property
    def verbrauch_avg_W(self) -> Optional[float]:
        """
        return None if no data available
        """
        return self.history.verbrauch_avg_W
