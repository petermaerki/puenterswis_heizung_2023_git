from __future__ import annotations

import dataclasses
import logging

logger = logging.getLogger(__name__)

_LIST_MODULATION_PROZENT = [0, 30, 65, 100]

_OEKOFEN_GAIN_MODULATION_PROZENT_K = 4.0 - 0.3
"""
Faktor zwischen Modulation prozent und Abweichung Kessel zu Solltemperatur, gemessen bei Testläufen
"""
_OEKOFEN_MODULATION_BEI_NULL_ABWEICHUNG_PROZENT = 65.0
"""
Modulation bei Kessel gleich Solltemperatur
"""
_OEKOFEN_KESSEL_UEBER_UW_ON_C = 2.8
"""
Bei UW Regelbereich 10 ist die Kesseltemp typ so viel über der UW Freitabe temp
"""
_OEKOFEN_MAX_REGELTEMP_C = 85.0
"""
beim Schreiben über Modbus laesst Oekofen nur Werte bis Abschalttemperatur minus Einschalthysterese (10) zu. Komsich.
"""

_modbus_FAx_UW_TEMP_ON_C_max = 80.0
_modbus_FAx_UW_TEMP_ON_C_min = 60.0


@dataclasses.dataclass
class ModulationBrenner:
    idx0: int
    idx0_modulation: int

    @staticmethod
    def get_idx(modulation: int) -> int:
        for idx, m in enumerate(_LIST_MODULATION_PROZENT):
            if m == modulation:
                return idx
        raise ValueError(f"Modulation {modulation} ist nicht in {_LIST_MODULATION_PROZENT}!")

    def set_max(self) -> None:
        self.idx0_modulation = len(_LIST_MODULATION_PROZENT) - 1

    def calculate_modbus_FAx_REGEL_TEMP_C(self, modbus_FAx_UW_TEMP_ON_C: float) -> float:
        """
        Modbus Register: modbus_FAx_UW_TEMP_ON_C
            Bei dieser Temperatur startet die Umwaelzpumpe vom Brenner.
            Der Brenner wird in etwa diese Temperatur foerdern.
        """
        if modbus_FAx_UW_TEMP_ON_C > _modbus_FAx_UW_TEMP_ON_C_max:
            logging.warning(f"modbus_FAx_UW_TEMP_ON_C({modbus_FAx_UW_TEMP_ON_C:0,1f}) > _modbus_FAx_UW_TEMP_ON_C_max({_modbus_FAx_UW_TEMP_ON_C_max:0.1f})")
            modbus_FAx_UW_TEMP_ON_C = _modbus_FAx_UW_TEMP_ON_C_max

        if modbus_FAx_UW_TEMP_ON_C < _modbus_FAx_UW_TEMP_ON_C_min:
            logging.warning(f"modbus_FAx_UW_TEMP_ON_C({modbus_FAx_UW_TEMP_ON_C:0,1f}) > _modbus_FAx_UW_TEMP_ON_C_min({_modbus_FAx_UW_TEMP_ON_C_min:0.1f})")
            modbus_FAx_UW_TEMP_ON_C = _modbus_FAx_UW_TEMP_ON_C_min

        regel_temp_c = _OEKOFEN_KESSEL_UEBER_UW_ON_C + (self.modulation_prozent - _OEKOFEN_MODULATION_BEI_NULL_ABWEICHUNG_PROZENT) / _OEKOFEN_GAIN_MODULATION_PROZENT_K + modbus_FAx_UW_TEMP_ON_C
        regel_temp_c = min(regel_temp_c, _OEKOFEN_MAX_REGELTEMP_C)
        return regel_temp_c

    @property
    def short(self) -> str:
        modbus_FAx_REGEL_TEMP_C = self.calculate_modbus_FAx_REGEL_TEMP_C(modbus_FAx_UW_TEMP_ON_C=76.0)
        return f"{self.modulation_prozent:3d}%({modbus_FAx_REGEL_TEMP_C:4.1f})"

    @property
    def is_off(self) -> bool:
        return self.idx0_modulation <= 0

    @property
    def is_on(self) -> bool:
        return self.idx0_modulation > 0

    @property
    def is_min(self) -> bool:
        return self.idx0_modulation == 1

    @property
    def is_max(self) -> bool:
        return self.idx0_modulation >= len(_LIST_MODULATION_PROZENT) - 1

    @property
    def is_over_min(self) -> bool:
        return self.idx0_modulation > 1

    @property
    def modulation_prozent(self) -> int:
        return _LIST_MODULATION_PROZENT[self.idx0_modulation]

    def erhoehen(self) -> None:
        self.idx0_modulation += 1
        assert 0 <= self.idx0_modulation < len(_LIST_MODULATION_PROZENT)

    def absenken(self) -> None:
        self.idx0_modulation -= 1
        assert 0 <= self.idx0_modulation < len(_LIST_MODULATION_PROZENT)


@dataclasses.dataclass
class ZweiBrenner:
    zwei_brenner: tuple[ModulationBrenner, ModulationBrenner]

    @property
    def short(self) -> str:
        return ",".join([b.short for b in self.zwei_brenner])

    def on_but_not_max(self) -> list[ModulationBrenner]:
        return [b for b in self.zwei_brenner if b.is_on and not b.is_max]

    def off(self) -> list[ModulationBrenner]:
        return [b for b in self.zwei_brenner if b.is_off]

    def on(self) -> list[ModulationBrenner]:
        return [b for b in self.zwei_brenner if b.is_on]

    def min(self) -> list[ModulationBrenner]:
        return [b for b in self.zwei_brenner if b.is_min]

    def is_over_min(self) -> list[ModulationBrenner]:
        return [b for b in self.zwei_brenner if b.is_over_min]


class ModulationSoll:
    WARTEZEIT_OFEN_EIN_MIN = 30
    WARTEZEIT_OFEN_AUS_MIN = 15
    WARTEZEIT_OFEN_MODULIEREN_MIN = 15
    WARTEZEIT_OFEN_NICHTS_MIN = 1

    SP_ZENTRAL_LADUNG_MODULATION_ERHOEHEN_PROZENT = 5.0
    SP_ZENTRAL_LADUNG_MODULATION_REDUZIEREN_PROZENT = 62.5

    def __init__(self, modulation0: int = 0, modulation1: int = 1) -> None:
        self.zwei_brenner = ZweiBrenner(
            (
                ModulationBrenner(idx0=0, idx0_modulation=ModulationBrenner.get_idx(modulation0)),
                ModulationBrenner(idx0=1, idx0_modulation=ModulationBrenner.get_idx(modulation1)),
            )
        )
        self.wartezeit_min: int = 0

    @property
    def wartezeit_s(self) -> float:
        return 60.00 * self.wartezeit_min

    @property
    def nichts_tun(self) -> bool:
        return self.wartezeit_min == self.WARTEZEIT_OFEN_NICHTS_MIN

    @property
    def short(self) -> str:
        return f"{ self.zwei_brenner.short},{self.wartezeit_min:2d}min"

    def tick(self, ladung_prozent: float, manual_mode: bool) -> None:
        self.wartezeit_min = self.WARTEZEIT_OFEN_NICHTS_MIN

        if manual_mode:
            # Temporaere einfache Lösung
            # Langfristig
            #   Zustand der Brenner abfragen und 'zwei_brenner' sinnvoll
            #   initialisieren.
            self.zwei_brenner.zwei_brenner[0].set_max()
            self.zwei_brenner.zwei_brenner[1].set_max()
            return

        if ladung_prozent < self.SP_ZENTRAL_LADUNG_MODULATION_ERHOEHEN_PROZENT:
            self._erhoehen(ladung_prozent=ladung_prozent)
            return
        if ladung_prozent > self.SP_ZENTRAL_LADUNG_MODULATION_REDUZIEREN_PROZENT:
            self._reduzieren(ladung_prozent=ladung_prozent)

    def _erhoehen(self, ladung_prozent: float) -> None:
        list_brenner_on = self.zwei_brenner.on_but_not_max()
        if len(list_brenner_on) >= 1:
            # Brenner moduliert bereits
            list_brenner_on[0].erhoehen()
            self.wartezeit_min = self.WARTEZEIT_OFEN_MODULIEREN_MIN
            return

        list_brenner_off = self.zwei_brenner.off()
        if len(list_brenner_off) > 0:
            if ladung_prozent < 0:
                # Brenner einschalten
                list_brenner_off[0].erhoehen()
                self.wartezeit_min = self.WARTEZEIT_OFEN_EIN_MIN
                return

    def _reduzieren(self, ladung_prozent: float) -> None:
        list_brenner_is_over_min = self.zwei_brenner.is_over_min()
        if len(list_brenner_is_over_min) >= 1:
            # Brenner moduliert bereits
            list_brenner_is_over_min[0].absenken()
            self.wartezeit_min = self.WARTEZEIT_OFEN_MODULIEREN_MIN
            return

        list_brenner_on = self.zwei_brenner.on()
        if len(list_brenner_on) == 0:
            # Beide Brenner sind bereits aus
            return

        # Mindestens ein Brenner ist an
        if ladung_prozent > 100.0:
            # Brenner ausschalten
            list_brenner_on[0].absenken()
            self.wartezeit_min = self.WARTEZEIT_OFEN_AUS_MIN
            return

        if len(list_brenner_on) == 2:
            if ladung_prozent >= 95.0:
                # Brenner ausschalten
                list_brenner_on[0].absenken()
                self.wartezeit_min = self.WARTEZEIT_OFEN_AUS_MIN
                return
