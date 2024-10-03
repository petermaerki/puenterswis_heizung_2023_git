from __future__ import annotations

import dataclasses
import enum
import logging

from zentral.util_action import ActionBaseEnum
from zentral.util_sp_ladung_zentral import SpLadung

logger = logging.getLogger(__name__)


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


class BrennerNum(enum.IntEnum):
    BRENNER_1 = 0
    BRENNER_2 = 1

    @property
    def idx0(self) -> int:
        return self.value


class Modulation(enum.IntEnum):
    OFF = 0
    MIN = 30
    MEDIUM = 65
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


@dataclasses.dataclass
class ModulationBrenner:
    idx0: int
    modulation: Modulation

    @property
    def label(self) -> str:
        return f"Brenner {self.idx0+1}"

    def set_modulation(self, modulation: Modulation) -> None:
        self.modulation = modulation

    def set_max(self) -> None:
        self.modulation = Modulation.MAX

    def calculate_modbus_FAx_REGEL_TEMP_C(self, modbus_FAx_UW_TEMP_ON_C: float) -> float:
        """
        Modbus Register: modbus_FAx_UW_TEMP_ON_C
            Bei dieser Temperatur startet die Umwaelzpumpe vom Brenner.
            Der Brenner wird in etwa diese Temperatur foerdern.
        """
        if modbus_FAx_UW_TEMP_ON_C > _modbus_FAx_UW_TEMP_ON_C_max:
            logger.warning(f"modbus_FAx_UW_TEMP_ON_C({modbus_FAx_UW_TEMP_ON_C:0,1f}) > _modbus_FAx_UW_TEMP_ON_C_max({_modbus_FAx_UW_TEMP_ON_C_max:0.1f})")
            modbus_FAx_UW_TEMP_ON_C = _modbus_FAx_UW_TEMP_ON_C_max

        if modbus_FAx_UW_TEMP_ON_C < _modbus_FAx_UW_TEMP_ON_C_min:
            logger.warning(f"modbus_FAx_UW_TEMP_ON_C({modbus_FAx_UW_TEMP_ON_C:0,1f}) > _modbus_FAx_UW_TEMP_ON_C_min({_modbus_FAx_UW_TEMP_ON_C_min:0.1f})")
            modbus_FAx_UW_TEMP_ON_C = _modbus_FAx_UW_TEMP_ON_C_min

        regel_temp_c = _OEKOFEN_KESSEL_UEBER_UW_ON_C + (self.modulation.prozent - _OEKOFEN_MODULATION_BEI_NULL_ABWEICHUNG_PROZENT) / _OEKOFEN_GAIN_MODULATION_PROZENT_K + modbus_FAx_UW_TEMP_ON_C
        regel_temp_c = min(regel_temp_c, _OEKOFEN_MAX_REGELTEMP_C)
        return regel_temp_c

    @property
    def short(self) -> str:
        modbus_FAx_REGEL_TEMP_C = self.calculate_modbus_FAx_REGEL_TEMP_C(modbus_FAx_UW_TEMP_ON_C=76.0)
        return f"{self.modulation.prozent:3d}%({modbus_FAx_REGEL_TEMP_C:4.1f})"

    def erhoehen(self) -> None:
        self.modulation = self.modulation.erhoeht

    def absenken(self) -> None:
        self.modulation = self.modulation.abgesenkt

    @property
    def is_off(self) -> bool:
        return self.modulation == Modulation.OFF

    @property
    def is_on(self) -> bool:
        return self.modulation >= Modulation.MIN

    @property
    def is_min(self) -> bool:
        return self.modulation == Modulation.MIN

    @property
    def is_max(self) -> bool:
        return self.modulation == Modulation.MAX

    @property
    def is_over_min(self) -> bool:
        return self.modulation > Modulation.MIN


class BrennerAction(ActionBaseEnum):
    EIN = 30
    AUS = 16
    MODULIEREN = 15
    NICHTS = 1


class ZweiBrenner(list[ModulationBrenner]):
    @property
    def short(self) -> str:
        return ",".join([b.short for b in self])

    def on_but_not_max(self) -> list[ModulationBrenner]:
        return [b for b in self if b.is_on and not b.is_max]

    def off(self) -> list[ModulationBrenner]:
        return [b for b in self if b.is_off]

    def on(self) -> list[ModulationBrenner]:
        return [b for b in self if b.is_on]

    def min(self) -> list[ModulationBrenner]:
        return [b for b in self if b.is_min]

    def is_over_min(self) -> list[ModulationBrenner]:
        return [b for b in self if b.is_over_min]

    def get_brenner(self, brenner_num: BrennerNum) -> ModulationBrenner:
        for brenner in self:
            if brenner.idx0 == brenner_num.idx0:
                return brenner
        raise ValueError(f"Does not exist: {brenner_num}")


class ModulationSoll:
    def __init__(self, modulation0: Modulation = Modulation.OFF, modulation1: Modulation = Modulation.OFF) -> None:
        self.zwei_brenner = ZweiBrenner(
            (
                ModulationBrenner(idx0=0, modulation=modulation0),
                ModulationBrenner(idx0=1, modulation=modulation1),
            )
        )
        self.action: BrennerAction = BrennerAction.NICHTS

    @property
    def short(self) -> str:
        return f"{ self.zwei_brenner.short},{self.action.wartezeit_min:2d}min"

    def _log_action(self, brenner: ModulationBrenner, reason: str) -> None:
        logger.info(f"brenner idx0={brenner.idx0}, {brenner.short} {self.action}. {reason}")

    def set_modulation(self, brenner_num: BrennerNum, modulation: Modulation, action: BrennerAction) -> None:
        """
        Only referenced by ScenarioOekofenBrennerModulation.
        """
        assert isinstance(brenner_num, BrennerNum)
        assert isinstance(modulation, Modulation)
        assert isinstance(action, BrennerAction)

        brenner = self.zwei_brenner.get_brenner(brenner_num)
        brenner.set_modulation(modulation=modulation)
        self.action = action
        self._log_action(brenner=brenner, reason="set_modulation(). Vermutlich Scenario.")

    def set_modulation_min(self) -> None:
        """
        Falls kein Haus Energie benötigt, also alle ventile geschlossen sind,
        so reduzieren wir sofort alle Brenner, sofern eingeschaltet, auf min.
        """
        for brenner in self.zwei_brenner:
            if brenner.modulation > Modulation.MIN:
                brenner.set_modulation(modulation=Modulation.MIN)
                self._log_action(brenner=brenner, reason="Absenken auf MIN, da kein Haus Enerige benötigt.")

    def abschalten_zweiter_Brenner(self, sp_ladung: SpLadung) -> None:
        list_brenner_on = self.zwei_brenner.on()
        if len(list_brenner_on) < 2:
            return
        if sp_ladung < SpLadung.LEVEL4:
            return

        # Beide Brenner brennen und Speicher ist maximal warm

        # Erster Brenner auf MIN setzen
        list_brenner_on[0].set_modulation(Modulation.MIN)
        self._log_action(brenner=list_brenner_on[0], reason="zweiter_Brenner_abschalten(): Erster Brenner auf Minimum.")

        # Zweiter Brenner direkt ausschalten
        list_brenner_on[1].set_modulation(Modulation.OFF)
        self.action = BrennerAction.AUS
        self._log_action(brenner=list_brenner_on[1], reason="zweiter_Brenner_abschalten(): Zweiten Brenner ausschalten.")

    def tick(self, sp_ladung: SpLadung, manual_mode: bool) -> None:
        assert isinstance(sp_ladung, SpLadung)
        assert isinstance(manual_mode, bool)

        self.action = BrennerAction.NICHTS

        if manual_mode:
            # Temporaere einfache Lösung
            # Langfristig
            #   Zustand der Brenner abfragen und 'zwei_brenner' sinnvoll
            #   initialisieren.
            for brenner in self.zwei_brenner:
                brenner.set_max()
            return

        if sp_ladung < SpLadung.LEVEL2:
            self._erhoehen(sp_ladung=sp_ladung)
            return
        if sp_ladung > SpLadung.LEVEL2:
            self._reduzieren(sp_ladung=sp_ladung)

    def _erhoehen(self, sp_ladung: SpLadung) -> None:
        list_brenner_on = self.zwei_brenner.on_but_not_max()
        if len(list_brenner_on) >= 1:
            # Brenner moduliert bereits
            list_brenner_on[0].erhoehen()
            self.action = BrennerAction.MODULIEREN
            self._log_action(brenner=list_brenner_on[0], reason="Erhoehen. Brenner moduliert bereits.")
            return

        list_brenner_off = self.zwei_brenner.off()
        if len(list_brenner_off) > 0:
            if sp_ladung <= SpLadung.LEVEL0:
                # Brenner einschalten
                list_brenner_off[0].erhoehen()
                self.action = BrennerAction.EIN
                self._log_action(brenner=list_brenner_off[0], reason="Brenner einschalten.")
                return

    def _reduzieren(self, sp_ladung: SpLadung) -> None:
        list_brenner_is_over_min = self.zwei_brenner.is_over_min()
        if len(list_brenner_is_over_min) >= 1:
            # Brenner moduliert bereits
            list_brenner_is_over_min[0].absenken()
            self.action = BrennerAction.MODULIEREN
            self._log_action(brenner=list_brenner_is_over_min[0], reason="Absenken. Brenner moduliert bereits.")
            return

        list_brenner_on = self.zwei_brenner.on()
        if len(list_brenner_on) == 0:
            # Beide Brenner sind bereits aus
            return

        # Mindestens ein Brenner ist an
        if sp_ladung >= SpLadung.LEVEL4:
            # Brenner ausschalten
            list_brenner_on[0].absenken()
            self.action = BrennerAction.AUS
            self._log_action(brenner=list_brenner_on[0], reason="Brenner ausschalten.")
