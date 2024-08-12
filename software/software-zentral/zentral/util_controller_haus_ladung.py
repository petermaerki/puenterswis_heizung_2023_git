import dataclasses


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

    def set_valve(self, label: str, do_open: bool) -> None:
        for h in self:
            if h.label == label:
                h.valve_open = do_open
                return
        raise ValueError(f"Label '{label}' not found!")
