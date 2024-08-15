from __future__ import annotations
import dataclasses
import typing


if typing.TYPE_CHECKING:
    from zentral.util_controller_verbrauch_schaltschwelle import HauserValveVariante


@dataclasses.dataclass(repr=True)
class HausLadung:
    label: str
    verbrauch_W: float | None
    ladung_Prozent: float
    valve_open: bool
    next_legionellen_kill_s: float

    def __post_init__(self) -> None:
        assert isinstance(self.label, str)
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

    def get_haus(self, label: str) -> HausLadung:
        for h in self:
            if h.label == label:
                return h
        raise ValueError(f"Label '{label}' not found!")

    def update_hvv(self, hvv: "HauserValveVariante") -> None:
        def set_valve(label: str, do_open: bool) -> None:
            self.get_haus(label=label).valve_open = do_open

        for label_valve_open in hvv.haeuser_valve_to_open:
            # hsm_dezental.valve_open = True
            set_valve(label=label_valve_open, do_open=True)

        for label_valve_close in hvv.haeuser_valve_to_close:
            # hsm_dezental.valve_close = True
            set_valve(label=label_valve_close, do_open=False)
