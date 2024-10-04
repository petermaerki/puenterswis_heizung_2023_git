from __future__ import annotations

import dataclasses
import enum
import logging

from zentral.util_action import ActionBaseEnum, ActionTimer

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


@dataclasses.dataclass(frozen=True)
class BrennerZustand:
    fa_temp_C: float
    fa_runtime_h: float
    verfuegbar: bool = True
    brennt: bool = False


class BrennerZustaende(tuple[BrennerZustand, BrennerZustand]):
    pass


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

    @property
    def short_idx0(self) -> str:
        return str(self.idx0)

    def erhoehen(self) -> None:
        self.modulation = self.modulation.erhoeht

    def absenken(self) -> None:
        self.modulation = self.modulation.abgesenkt

    def zuenden(self) -> None:
        self.modulation = Modulation.MIN

    def loeschen(self) -> None:
        self.modulation = Modulation.OFF

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

    def verfuegbar(self, brenner_zustaende: BrennerZustaende) -> bool:
        return brenner_zustaende[self.idx0].verfuegbar

    def fa_temp_C(self, brenner_zustaende: BrennerZustaende) -> float:
        return brenner_zustaende[self.idx0].fa_temp_C

    def fa_runtime_h(self, brenner_zustaende: BrennerZustaende) -> float:
        return brenner_zustaende[self.idx0].fa_runtime_h


class BrennerAction(ActionBaseEnum):
    ZUENDEN = 30
    LOESCHEN = 16
    MODULIEREN = 15
    NICHTS = 1


class ListBrenner(list[ModulationBrenner]):
    @property
    def short(self) -> str:
        return ",".join([b.short for b in self])

    @property
    def short_idx0(self) -> str:
        return "".join([b.short_idx0 for b in self])

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
        self.zwei_brenner = ListBrenner(
            (
                ModulationBrenner(idx0=0, modulation=modulation0),
                ModulationBrenner(idx0=1, modulation=modulation1),
            )
        )
        self.actiontimer = ActionTimer()

    @property
    def short(self) -> str:
        wartezeit_text = "--min"
        if self.actiontimer.action is not None:
            wartezeit_text = f"{self.actiontimer.action.wartezeit_min:2d}min"
        return f"{self.zwei_brenner.short},{wartezeit_text}"

    def initialize(self, brenner_zustaende: BrennerZustaende) -> None:
        assert len(brenner_zustaende) == 2
        assert len(self.zwei_brenner) == 2
        for brenner, brenner_zustand in zip(self.zwei_brenner, brenner_zustaende):
            if not brenner_zustand.verfuegbar:
                brenner.set_modulation(modulation=Modulation.OFF)
                continue

            modulation = Modulation.MIN if brenner_zustand.brennt else Modulation.OFF
            brenner.set_modulation(modulation=modulation)

    def list_brenner(self, brenner_zustaende: BrennerZustaende) -> ListBrenner:
        """
        Entfernen der Brenner, die nicht verfügbar (z. B. 'Touchscreen-Aus') sind.
        Ordnen nach Temperatur absteigend, Betriebsdauer aufsteigend,
        """
        assert len(self.zwei_brenner) == 2
        zwei_brenner_copy = ListBrenner(self.zwei_brenner)

        # Annahme: 'self.zwei_brenner[x]' entspricht 'brenner_zustaende[x]'
        diff_C = brenner_zustaende[0].fa_temp_C - brenner_zustaende[1].fa_temp_C
        if abs(diff_C) > 10.0:
            if diff_C < 0.0:
                zwei_brenner_copy.reverse()
        else:
            if brenner_zustaende[0].fa_runtime_h > brenner_zustaende[1].fa_runtime_h:
                zwei_brenner_copy.reverse()

        zwei_brenner_copy = ListBrenner([b for b in zwei_brenner_copy if b.verfuegbar(brenner_zustaende)])
        return zwei_brenner_copy

    def _log_action(self, brenner: ModulationBrenner, reason: str) -> None:
        logger.info(f"{self.actiontimer.action_name_full} brenner idx0={brenner.idx0}, {brenner.short}. {reason}")

    def set_modulation(self, brenner_num: BrennerNum, modulation: Modulation, action: BrennerAction) -> None:
        """
        Only referenced by ScenarioOekofenBrennerModulation.
        """
        assert isinstance(brenner_num, BrennerNum)
        assert isinstance(modulation, Modulation)
        assert isinstance(action, BrennerAction)

        brenner = self.zwei_brenner.get_brenner(brenner_num)
        brenner.set_modulation(modulation=modulation)
        self.actiontimer.action = action
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

    def _force(self, force: bool) -> None:
        if force:
            assert self.actiontimer.action == BrennerAction.NICHTS

    def modulation_erhoehen(self, brenner_zustaende: BrennerZustaende, force=False) -> bool:
        if not self.actiontimer.is_over_and_cancel():
            # We have to wait for the previous action to be finished
            return False
        self._force(force=force)

        list_brenner = self.list_brenner(brenner_zustaende).on_but_not_max()
        try:
            brenner = list_brenner.pop(0)
        except IndexError:
            return False
        # Brenner moduliert bereits
        brenner.erhoehen()
        self.actiontimer.action = BrennerAction.MODULIEREN
        self._log_action(brenner=brenner, reason="Erhoehen. Brenner moduliert bereits.")
        return True

    def brenner_zuenden(self, brenner_zustaende: BrennerZustaende, force=False) -> bool:
        if not self.actiontimer.is_over_and_cancel():
            # We have to wait for the previous action to be finished
            return False

        self._force(force=force)

        list_brenner = self.list_brenner(brenner_zustaende).off()
        try:
            brenner = list_brenner.pop(0)
        except IndexError:
            return False

        # Brenner einschalten
        brenner.zuenden()
        self.actiontimer.action = BrennerAction.ZUENDEN
        self._log_action(brenner=brenner, reason="Brenner einschalten.")
        return True

    def modulation_reduzieren(self, brenner_zustaende: BrennerZustaende, force=False) -> bool:
        if not self.actiontimer.is_over_and_cancel():
            # We have to wait for the previous action to be finished
            return False

        self._force(force=force)

        list_brenner = self.list_brenner(brenner_zustaende).is_over_min()
        try:
            brenner = list_brenner.pop(-1)
        except IndexError:
            return False

        # Brenner moduliert bereits
        brenner.absenken()
        self.actiontimer.action = BrennerAction.MODULIEREN
        self._log_action(brenner=brenner, reason="Absenken. Brenner moduliert bereits.")
        return True

    def brenner_loeschen(self, brenner_zustaende: BrennerZustaende, force=False) -> bool:
        if not self.actiontimer.is_over_and_cancel():
            # We have to wait for the previous action to be finished
            return False

        self._force(force=force)

        list_brenner = self.list_brenner(brenner_zustaende).on()
        try:
            # Wir nehmen den Brenner zuerst, der die höhere Betriebsdauer hat.
            brenner = list_brenner.pop(-1)
        except IndexError:
            # Beide Brenner sind bereits aus
            return False

        # Brenner loeschen
        brenner.loeschen()
        self.actiontimer.action = BrennerAction.LOESCHEN
        self._log_action(brenner=brenner, reason="Brenner ausschalten.")
        return True
