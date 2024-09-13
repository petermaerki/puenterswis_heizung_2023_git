import dataclasses

from zentral.util_transition import linear_transition


@dataclasses.dataclass
class SpTemperatur:
    unten_C: float
    mitte_C: float
    oben_C: float

    @property
    def energie_absolut_J(self) -> float:
        """
        Energie bezueglich 0C
        """
        energie_u_J = self.unten_C * LadungBase.SP_UNTEN_WASSER_KG * LadungBase.KAPAZITAET_WASSER_J_kg_K
        energie_m_J = self.mitte_C * LadungBase.SP_MITTE_WASSER_KG * LadungBase.KAPAZITAET_WASSER_J_kg_K
        energie_o_J = self.oben_C * LadungBase.SP_OBEN_WASSER_KG * LadungBase.KAPAZITAET_WASSER_J_kg_K
        return energie_u_J + energie_m_J + energie_o_J


class LadungBase:
    KAPAZITAET_WASSER_J_kg_K = 4190

    SP_WASSER_KG = 690
    # Folgende drei Faktoren sind gewaehlt in Anlehnung an das geschaetzte Volumen bei den Sensoren, Besprechung 2024-03-27 Peter Schaer und Peter Maerki
    ANTEIL_WASSER_UNTEN = 40.0 / 100.0
    ANTEIL_WASSER_MITTE = 30.0 / 100.0
    ANTEIL_WASSER_OBEN = 30.0 / 100.0
    SP_UNTEN_WASSER_KG = SP_WASSER_KG * ANTEIL_WASSER_UNTEN
    SP_MITTE_WASSER_KG = SP_WASSER_KG * ANTEIL_WASSER_MITTE
    SP_OBEN_WASSER_KG = SP_WASSER_KG * ANTEIL_WASSER_OBEN
    assert abs(SP_UNTEN_WASSER_KG + SP_MITTE_WASSER_KG + SP_OBEN_WASSER_KG - SP_WASSER_KG) < 0.1

    # Fuer die definition der Ladung 100%
    UNTEN_100_PROZENT_C = 45.0
    MITTE_100_PROZENT_C = 65.0
    OBEN_100_PROZENT_C = 65.0

    # minimale Temperatur zum Duschen.
    # z.B. https://www.edeka.de/ernaehrung/beauty/ideale-duschtemperatur-im-sommer.jsp
    # "Die ideale Duschtemperatur bewegt sich im Bereich der Koerpertemperatur, also um die 37 °C.
    # Wer es etwas waermer mag, kann die Wassertemperatur auf bis zu 43 °C erhoehen, wer lieber kaelter duscht,
    # kann die Wassertemperatur auf bis zu 18 °C senken."
    DUSCH_TEMPERATUR_MIN_C = 40.0

    def __init__(self, sp_temperatur: SpTemperatur):
        self.sp_temperatur = sp_temperatur

    @property
    def ladung_prozent(self) -> float:
        return 1.0


class LadungBodenheizung(LadungBase):
    """
    Fuer Heizung minimale Speichertemperatur
    heizkurve_heizungswasser_C = (20.0 - self.stimuli.umgebungstemperatur_C) * 10.0 / 28.0 + 25.0  # gemaess Heizkurve VC Engineering
    """

    OFFSET_C = 3.0
    """
    Offset weil der Aussentemperaturfuehler auf einer Betonwand montiert ist und diese Wand durch die Abwaerme der Heizzentrale etwas waermer als die effektive Aussentempeatur ist.
    """

    AUSSENTEMPERATURGENZE_HEIZEN_C = 14.0 + OFFSET_C
    """
    Ueber dieser Aussentemperatur muss nicht mehr geheizt werden
    http://archiv.hev-zuerich.ch.rubin.ch-meta.net/jahr-2006/ms-art-200612-05.htm
    "In der Regel sollte geheizt werden, wenn die Aussentemperatur unter 14 Grad sinkt."
    """

    MAX_PROZENT = 200.0

    def __init__(self, sp_temperatur: SpTemperatur, temperatur_aussen_C: float):
        super().__init__(sp_temperatur=sp_temperatur)
        self.temperatur_aussen_C = temperatur_aussen_C
        self.heiz_temperatur_min_C = (20.0 - temperatur_aussen_C) * 10.0 / 28.0 + 25.0
        self.energie_100_J = self._energie_J(
            SpTemperatur(
                unten_C=self.UNTEN_100_PROZENT_C,
                mitte_C=self.MITTE_100_PROZENT_C,
                oben_C=self.OBEN_100_PROZENT_C,
            )
        )

    @property
    def energie_J(self) -> float:
        return self._energie_J(self.sp_temperatur)

    def _energie_J(self, sp_temperatur: SpTemperatur) -> float:
        if sp_temperatur.mitte_C > self.heiz_temperatur_min_C:
            energie_u_J = (sp_temperatur.unten_C - self.heiz_temperatur_min_C) * self.SP_UNTEN_WASSER_KG * self.KAPAZITAET_WASSER_J_kg_K
            energie_m_J = (sp_temperatur.mitte_C - self.heiz_temperatur_min_C) * self.SP_MITTE_WASSER_KG * self.KAPAZITAET_WASSER_J_kg_K
            return max(energie_u_J, 0) + max(energie_m_J, 0)

        return (sp_temperatur.mitte_C - self.heiz_temperatur_min_C) * (self.SP_UNTEN_WASSER_KG + self.SP_MITTE_WASSER_KG) * self.KAPAZITAET_WASSER_J_kg_K

    @property
    def ladung_prozent(self) -> float:
        uebergangsbereich_C = 2.0  # Uebergangsbereich damit kein abrupter Wechsel
        ladung_falls_heizperiode_prozent = self.energie_J / self.energie_100_J * 100.0
        transition_prozent = linear_transition(
            x=self.temperatur_aussen_C,
            start_x=self.AUSSENTEMPERATURGENZE_HEIZEN_C,
            end_x=self.AUSSENTEMPERATURGENZE_HEIZEN_C + uebergangsbereich_C,
            start_y=ladung_falls_heizperiode_prozent,
            end_y=self.MAX_PROZENT,
        )
        return max(transition_prozent, ladung_falls_heizperiode_prozent)

    @property
    def is_sommer(self) -> float:
        # return self.ladung_prozent > self.MAX_PROZENT - 1.0
        return self.temperatur_aussen_C > self.AUSSENTEMPERATURGENZE_HEIZEN_C


def _baden_energie_J(sp_temperatur: SpTemperatur) -> float:
    if sp_temperatur.oben_C > LadungBase.DUSCH_TEMPERATUR_MIN_C:
        energie_u_J = (sp_temperatur.unten_C - LadungBase.DUSCH_TEMPERATUR_MIN_C) * LadungBase.SP_UNTEN_WASSER_KG * LadungBase.KAPAZITAET_WASSER_J_kg_K
        energie_m_J = (sp_temperatur.mitte_C - LadungBase.DUSCH_TEMPERATUR_MIN_C) * LadungBase.SP_MITTE_WASSER_KG * LadungBase.KAPAZITAET_WASSER_J_kg_K
        energie_o_J = (sp_temperatur.oben_C - LadungBase.DUSCH_TEMPERATUR_MIN_C) * LadungBase.SP_OBEN_WASSER_KG * LadungBase.KAPAZITAET_WASSER_J_kg_K
        return max(energie_u_J, 0) + max(energie_m_J, 0) + max(energie_o_J, 0)

    # Fuer kontinuierlichen Uebergang nur obere Temperatur und gesamtes Wasser
    return (sp_temperatur.oben_C - LadungBase.DUSCH_TEMPERATUR_MIN_C) * (LadungBase.SP_UNTEN_WASSER_KG + LadungBase.SP_MITTE_WASSER_KG + LadungBase.SP_OBEN_WASSER_KG) * LadungBase.KAPAZITAET_WASSER_J_kg_K


class LadungBaden(LadungBase):
    MAXIMALE_ENERGIE_BADEN_J = _baden_energie_J(
        SpTemperatur(
            LadungBase.UNTEN_100_PROZENT_C,
            LadungBase.MITTE_100_PROZENT_C,
            LadungBase.OBEN_100_PROZENT_C,
        )
    )

    LADUNG_BADEN_0_PROZENT = _baden_energie_J(
        SpTemperatur(0.0, 40.0, 50.0)  # es braucht diese Energie um eine Badewanne zu fuellen
    )

    @property
    def energie_J(self) -> float:
        return _baden_energie_J(self.sp_temperatur)

    @property
    def ladung_prozent(self) -> float:
        return (self.energie_J - self.LADUNG_BADEN_0_PROZENT) / (self.MAXIMALE_ENERGIE_BADEN_J - self.LADUNG_BADEN_0_PROZENT) * 100.0


class LadungMinimum(LadungBase):
    def __init__(self, sp_temperatur: SpTemperatur, temperatur_aussen_C: float):
        super().__init__(sp_temperatur=sp_temperatur)
        self.sp_temperatur = sp_temperatur
        self.ladung_baden = LadungBaden(sp_temperatur)
        self.ladung_bodenheizung = LadungBodenheizung(sp_temperatur, temperatur_aussen_C)

    @property
    def ladung_prozent(self) -> float:
        return min(self.ladung_baden.ladung_prozent, self.ladung_bodenheizung.ladung_prozent)
