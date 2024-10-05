from __future__ import annotations

import dataclasses
import enum


class SpLadung(enum.IntEnum):
    LEVEL0 = 0
    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3
    LEVEL4 = 4

    @property
    def lower_level_prozent(self) -> int:
        return {
            SpLadung.LEVEL0: -50,
            SpLadung.LEVEL1: 10,
            SpLadung.LEVEL2: 40,
            SpLadung.LEVEL3: 70,
            SpLadung.LEVEL4: 100,
        }[self]

    @property
    def upper_level_prozent(self) -> int:
        return {
            SpLadung.LEVEL0: SpLadung.LEVEL1.lower_level_prozent,
            SpLadung.LEVEL1: SpLadung.LEVEL2.lower_level_prozent,
            SpLadung.LEVEL2: SpLadung.LEVEL3.lower_level_prozent,
            SpLadung.LEVEL3: SpLadung.LEVEL4.lower_level_prozent,
            SpLadung.LEVEL4: 160,
        }[self]

    @property
    def band_width_prozent(self) -> int:
        return self.upper_level_prozent - self.lower_level_prozent

    def get_C(self, sp_temperatur: SpLadungZentral) -> tuple[float, float]:
        """
        lower and upper temperature
        """
        return {
            SpLadung.LEVEL0: (sp_temperatur.Tsz4_C, 90.0),
            SpLadung.LEVEL1: (sp_temperatur.Tsz3_C, sp_temperatur.Tsz4_C),
            SpLadung.LEVEL2: (sp_temperatur.Tsz2_C, sp_temperatur.Tsz3_C),
            SpLadung.LEVEL3: (sp_temperatur.Tsz1_C, sp_temperatur.Tsz2_C),
            SpLadung.LEVEL4: (0.0, sp_temperatur.Tsz1_C),
        }[self]


_KAPAZITAET_WASSER_J_kg_K = 4190

_SP_WASSER_KG = 1250.0
"""
Puent!
"""
_SP_1_WASSER_KG = _SP_WASSER_KG * 0.25
_SP_2_WASSER_KG = _SP_WASSER_KG * 0.25
_SP_3_WASSER_KG = _SP_WASSER_KG * 0.25
_SP_4_WASSER_KG = _SP_WASSER_KG * 0.25
assert abs(_SP_1_WASSER_KG + _SP_2_WASSER_KG + _SP_3_WASSER_KG + _SP_4_WASSER_KG - _SP_WASSER_KG) < 0.1


_MIN_NUETZLICHE_TEMPERATUR_C = 65.0


@dataclasses.dataclass
class SpLadungZentral:
    Tsz1_C: float
    Tsz2_C: float
    Tsz3_C: float
    Tsz4_C: float

    @property
    def ladung(self) -> SpLadung:
        """
        Level: [0..4]
        """
        level = 4
        for TszX_C in (self.Tsz1_C, self.Tsz2_C, self.Tsz3_C, self.Tsz4_C):
            if TszX_C > _MIN_NUETZLICHE_TEMPERATUR_C:
                return SpLadung(level)
            level -= 1
        return SpLadung(0)

    @property
    def ladung_prozent(self) -> float:
        for sp_ladung in reversed(SpLadung):
            lower_C, upper_C = sp_ladung.get_C(self)
            below_upper_C = upper_C - _MIN_NUETZLICHE_TEMPERATUR_C
            if below_upper_C > 0.0:
                diff2_C = max(0.1, upper_C - lower_C)
                anteil_below_upper = below_upper_C / diff2_C
                return anteil_below_upper * sp_ladung.band_width_prozent + sp_ladung.lower_level_prozent

        raise ValueError
