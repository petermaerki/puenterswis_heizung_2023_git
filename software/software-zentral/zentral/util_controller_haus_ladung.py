from __future__ import annotations

import dataclasses
import typing

if typing.TYPE_CHECKING:
    from zentral.config_base import Haus

_INDIVIDUELL_MAX_PROZENT = 100.0
_INDIVIDUELL_MIN_PROZENT = 40.0


@dataclasses.dataclass(repr=True, frozen=True)
class HausLadung:
    haus: Haus
    verbrauch_avg_W: float
    max_verbrauch_avg_W: float
    ladung_prozent: float
    valve_open: bool
    next_legionellen_kill_s: float

    def __post_init__(self) -> None:
        assert self.haus.__class__.__name__ == "Haus"
        assert isinstance(self.verbrauch_avg_W, float)
        assert isinstance(self.ladung_prozent, float)
        assert isinstance(self.valve_open, bool)
        assert isinstance(self.next_legionellen_kill_s, float)
        assert self.verbrauch_avg_W >= -1e-6

    def set_valve(self, valve_open: bool) -> None:
        self.haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = valve_open

    @property
    def legionellen_kill_soon(self) -> bool:
        return self.next_legionellen_kill_s < 1 * 24 * 3600.0

    @property
    def legionellen_kill_urgent(self) -> bool:
        return self.next_legionellen_kill_s < -2 * 24 * 3600.0

    @property
    def ladung_individuell_prozent(self) -> None:
        return self.ladung_prozent * 100.0 / (self.verbrauch_avg_W / self.max_verbrauch_avg_W * (_INDIVIDUELL_MAX_PROZENT - _INDIVIDUELL_MIN_PROZENT) + _INDIVIDUELL_MIN_PROZENT)


class HaeuserLadung(list[HausLadung]):
    @property
    def valve_open_count(self) -> int:
        return len([h for h in self if h.valve_open])

    def sort_by_ladung_indiviuell(self) -> None:
        def f_key(haus_ladung: HausLadung) -> float:
            return haus_ladung.ladung_individuell_prozent

        self.sort(key=f_key)
