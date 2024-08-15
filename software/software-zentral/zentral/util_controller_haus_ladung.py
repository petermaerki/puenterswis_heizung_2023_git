from __future__ import annotations

import dataclasses
import typing

if typing.TYPE_CHECKING:
    from zentral.util_controller_verbrauch_schaltschwelle import HauserValveVariante


@dataclasses.dataclass(repr=True)
class HausLadung:
    nummer: int
    verbrauch_W: float | None
    ladung_Prozent: float
    valve_open: bool
    next_legionellen_kill_s: float

    def __post_init__(self) -> None:
        assert isinstance(self.nummer, int)
        assert isinstance(self.verbrauch_W, float | None)
        assert isinstance(self.ladung_Prozent, float)
        assert isinstance(self.valve_open, bool)
        assert isinstance(self.next_legionellen_kill_s, float)
        assert self.verbrauch_W >= 0.0


class HaeuserLadung(list[HausLadung]):
    @property
    def max_verbrauch_W(self) -> float:
        """ """
        return max([h.verbrauch_W for h in self if h.verbrauch_W is not None])

    @property
    def valve_open_count(self) -> int:
        return len([h for h in self if h.valve_open])

    def get_haus(self, nummer: int) -> HausLadung:
        for h in self:
            if h.nummer == nummer:
                return h
        raise ValueError(f"Haus number '{nummer}' not found!")

    def update_hvv(self, hvv: "HauserValveVariante") -> None:
        def set_valve(nummer: int, do_open: bool) -> None:
            self.get_haus(nummer=nummer).valve_open = do_open

        for nummer in hvv.haeuser_valve_to_open:
            set_valve(nummer=nummer, do_open=True)

        for nummer in hvv.haeuser_valve_to_close:
            set_valve(nummer=nummer, do_open=False)
