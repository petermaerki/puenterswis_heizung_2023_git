import dataclasses


@dataclasses.dataclass
class SpTemperaturZentral:
    Tsz1_C: float
    Tsz2_C: float
    Tsz3_C: float
    Tsz4_C: float

    @property
    def energie_J(self) -> float:
        if self.Tsz4_C > LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C:
            energie_1_J = (self.Tsz1_C - LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C) * LadungZentral.SP_1_WASSER_KG * LadungZentral.KAPAZITAET_WASSER_J_kg_K
            energie_2_J = (self.Tsz2_C - LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C) * LadungZentral.SP_2_WASSER_KG * LadungZentral.KAPAZITAET_WASSER_J_kg_K
            energie_3_J = (self.Tsz3_C - LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C) * LadungZentral.SP_3_WASSER_KG * LadungZentral.KAPAZITAET_WASSER_J_kg_K
            energie_4_J = (self.Tsz4_C - LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C) * LadungZentral.SP_4_WASSER_KG * LadungZentral.KAPAZITAET_WASSER_J_kg_K
            return max(energie_1_J, 0) + max(energie_2_J, 0) + max(energie_3_J, 0) + max(energie_4_J, 0)

        # Fuer kontinuierlichen Uebergang nur obere Temperatur und gesamtes Wasser
        return (self.Tsz4_C - LadungZentral.MIN_NUETZLICHE_TEMPERATUR_C) * LadungZentral.SP_WASSER_KG * LadungZentral.KAPAZITAET_WASSER_J_kg_K


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
        raise NotImplementedError("Achtung: Unterschied Wassermenge Bochs/Puent!")
        return self.sp_temperatur.energie_J

    @property
    def ladung_prozent(self) -> float:
        energie_100_J = (self.SPEICHER_100_PROZENT_C - self.MIN_NUETZLICHE_TEMPERATUR_C) * self.SP_WASSER_KG * self.KAPAZITAET_WASSER_J_kg_K
        return self.sp_temperatur.energie_J / energie_100_J * 100.0
