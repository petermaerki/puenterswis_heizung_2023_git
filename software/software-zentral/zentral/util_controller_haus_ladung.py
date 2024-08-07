import dataclasses


@dataclasses.dataclass
class HausLadung:
    label: str
    verbrauch_W: float | None
    ladung_Prozent: float
    valve_open: bool
    last_legionellen_kill_s: float


class HaeuserLadung(list[HausLadung]):
    @property
    def max_verbrauch_W(self) -> float:
        """ """
        return max([h.verbrauch_W for h in self if h.verbrauch_W is not None])

    @property
    def valve_open_count(self) -> int:
        return len([h for h in self if h.valve_open])
