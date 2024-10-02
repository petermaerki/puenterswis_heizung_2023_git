import dataclasses
import enum


class SpLadung(enum.IntEnum):
    LEVEL0 = 0
    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3
    LEVEL4 = 4

    @property
    def level_prozent(self) -> int:
        return self.value * 25


@dataclasses.dataclass
class SpTemperaturZentral:
    Tsz1_C: float
    Tsz2_C: float
    Tsz3_C: float
    Tsz4_C: float

    @property
    def energie_J(self) -> float:
        """
        TODO: OBSOLETE
        """
        if self.Tsz4_C > LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C:
            energie_1_J = (self.Tsz1_C - LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C) * LadungZentral.SP_1_WASSER_KG * LadungZentral.KAPAZITAET_WASSER_J_kg_K
            energie_2_J = (self.Tsz2_C - LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C) * LadungZentral.SP_2_WASSER_KG * LadungZentral.KAPAZITAET_WASSER_J_kg_K
            energie_3_J = (self.Tsz3_C - LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C) * LadungZentral.SP_3_WASSER_KG * LadungZentral.KAPAZITAET_WASSER_J_kg_K
            energie_4_J = (self.Tsz4_C - LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C) * LadungZentral.SP_4_WASSER_KG * LadungZentral.KAPAZITAET_WASSER_J_kg_K
            return max(energie_1_J, 0) + max(energie_2_J, 0) + max(energie_3_J, 0) + max(energie_4_J, 0)

        # Fuer kontinuierlichen Uebergang nur obere Temperatur und gesamtes Wasser
        return (self.Tsz4_C - LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C) * LadungZentral.SP_WASSER_KG * LadungZentral.KAPAZITAET_WASSER_J_kg_K

    @property
    def ladung(self) -> SpLadung:
        """
        Level: [0..4]
        """
        level = 4
        for TszX_C in (self.Tsz1_C, self.Tsz2_C, self.Tsz3_C, self.Tsz4_C):
            if TszX_C > LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C:
                return SpLadung(level)
            level -= 1
        return SpLadung(0)


class LadungZentral:
    KAPAZITAET_WASSER_J_kg_K = 4190

    SP_WASSER_KG = 1250.0
    """
    Puent!
    """
    SP_1_WASSER_KG = SP_WASSER_KG * 0.25
    SP_2_WASSER_KG = SP_WASSER_KG * 0.25
    SP_3_WASSER_KG = SP_WASSER_KG * 0.25
    SP_4_WASSER_KG = SP_WASSER_KG * 0.25
    assert abs(SP_1_WASSER_KG + SP_2_WASSER_KG + SP_3_WASSER_KG + SP_4_WASSER_KG - SP_WASSER_KG) < 0.1

    # Fuer die definition der Ladung 100%
    SPEICHER_100_PROZENT_C = 75.0

    MIN_NUETZLICHE_TEMPERATUR_C = 65.0

    def __init__(self, sp_temperatur: SpTemperaturZentral):
        self.sp_temperatur = sp_temperatur

    @property
    def energie_J(self) -> float:
        """
        TODO: OBSOLETE
        """
        raise NotImplementedError("Achtung: Unterschied Wassermenge Bochs/Puent!")
        # return self.sp_temperatur.energie_J

    @property
    def ladung_prozent(self) -> float:
        """
        TODO: OBSOLETE
        """
        energie_100_J = (self.SPEICHER_100_PROZENT_C - self.MIN_NUETZLICHE_TEMPERATUR_C) * self.SP_WASSER_KG * self.KAPAZITAET_WASSER_J_kg_K
        return self.sp_temperatur.energie_J / energie_100_J * 100.0

    @property
    def ladung(self) -> SpLadung:
        return self.sp_temperatur.ladung
