from __future__ import annotations

import dataclasses
import enum
from zentral.util_action import ActionBaseEnum


class BrennerError(ActionBaseEnum):
    ERROR = 25


class BrennerNum(enum.IntEnum):
    BRENNER_1 = 0
    BRENNER_2 = 1

    @property
    def idx0(self) -> int:
        return self.value


@dataclasses.dataclass(frozen=True)
class BrennerZustand:
    fa_temp_C: float
    fa_runtime_h: float
    verfuegbar: bool = True
    zuendet_oder_brennt: bool = False
    brennt: bool = False


class BrennerZustaende(tuple[BrennerZustand, BrennerZustand]):
    pass


class Modulation(enum.IntEnum):
    OFF = 0
    MIN = 30
    # MEDIUM = 65
    MAX = 100

    @property
    def prozent(self) -> int:
        return self.value

    @property
    def erhoeht(self) -> Modulation:
        return _MHC.erhoeht(self)

    @property
    def abgesenkt(self) -> Modulation:
        return _MHC.abgesenkt(self)


class _ModulationHelperCache:
    def __init__(self) -> None:
        self.list_m = list(Modulation)
        self.max_idx0 = len(self.list_m) - 1

    def erhoeht(self, m: Modulation) -> Modulation:
        idx = self.list_m.index(m)
        return self.list_m[min(idx + 1, self.max_idx0)]

    def abgesenkt(self, m: Modulation) -> Modulation:
        idx = self.list_m.index(m)
        return self.list_m[max(idx - 1, 0)]


_MHC = _ModulationHelperCache()
