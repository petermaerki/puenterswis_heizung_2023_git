"""
Liest speicher_ladung_prozent

Setzt temperaturen von Brenner 1 und 2
Sperrt Brenner
"""

import logging
import typing

from zentral.handler_elektro_notheizung import HandlerElektroNotheizung
from zentral.util_modulation_soll import BrennerAction, BrennerNum, BrennerZustaende, BrennerZustand, Modulation, ModulationSoll
from zentral.util_oekofen_brenner_uebersicht import EnumBrennerUebersicht, brenner_uebersicht_prozent

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class HandlerOekofen:
    def __init__(self, ctx: "Context", now_s: float) -> None:
        self.ctx = ctx
        self.handler_elektro_notheizung = HandlerElektroNotheizung(now_s=now_s)
        self.modulation_soll = ModulationSoll(modulation0=Modulation.OFF, modulation1=Modulation.OFF)
        self._initialized = False

    @property
    def betrieb_notheizung(self) -> bool:
        if not self._initialized:
            _ = self.brenner_zustaende

        brenner1, brenner2 = self.brenner_uebersicht_prozent
        return max(brenner1, brenner2) <= EnumBrennerUebersicht.AUSGESCHALTET_DURCH_BENUTZER

    @property
    def brenner_zustaende(self) -> BrennerZustaende:
        modbus_oekofen_registers = self.ctx.hsm_zentral.modbus_oekofen_registers
        if modbus_oekofen_registers is None:
            return BrennerZustaende(
                (
                    BrennerZustand(fa_temp_C=0.0, fa_runtime_h=0, verfuegbar=False),
                    BrennerZustand(fa_temp_C=0.0, fa_runtime_h=0, verfuegbar=False),
                )
            )
        brenner_zustaende = modbus_oekofen_registers.brenner_zustaende
        if not self._initialized:
            self._initialized = True
            for brenner_zustand in brenner_zustaende:
                logger.info(f"modulation_soll.initialize({brenner_zustand})")
            self.modulation_soll.initialize(brenner_zustaende=brenner_zustaende)
        return brenner_zustaende

    @property
    def anzahl_brenner_on(self) -> int:
        return len(self.modulation_soll.zwei_brenner.on())

    @property
    def brenner_uebersicht_prozent(self) -> tuple[int, int]:
        """
        return (brenner1, brenneer2)
        """
        return brenner_uebersicht_prozent(registers=self.ctx.hsm_zentral.modbus_oekofen_registers)

    def modulation_erhoehen(self) -> bool:
        """
        Return True: Falls die Leistung erhöht werden konnte.
        Return False: Bereits auf maximum Leistung.
        """
        ok = self.modulation_soll.modulation_erhoehen(brenner_zustaende=self.brenner_zustaende)
        self._update_relais()
        return ok

    def modulation_reduzieren(self) -> bool:
        """
        Return True: Falls die Leistung reduziert werden konnte.
        Return False: Bereits auf minimaler Leistung.
        """
        ok = self.modulation_soll.modulation_reduzieren(brenner_zustaende=self.brenner_zustaende)
        self._update_relais()
        return ok

    def erster_brenner_zuenden(self) -> bool:
        if self.anzahl_brenner_on == 0:
            return self.brenner_zuenden()
        return False

    def zweiter_brenner_loeschen(self) -> bool:
        if self.anzahl_brenner_on == 2:
            return self.brenner_loeschen()
        return False

    def handle_brenner_mit_stoerung(self) -> None:
        if self.modulation_soll.actiontimer.action == BrennerAction.ZUENDEN:
            # Während dem Zünden dürfen "Fehler" auftreten
            return

        # Alle Brenner die nicht brennen, sollen mit dem Relais gesperrt sein.
        # Aber erst nach einen Timeout!
        for idx0, brenner_zustand in enumerate(self.brenner_zustaende):
            brenner = self.modulation_soll.zwei_brenner[idx0]
            if brenner.is_off:
                continue

            if brenner_zustand.brennt:
                continue

            # Brenner brennt nicht, das Timeout starten
            brenner.set_error_if_not_already_set()

            if brenner.is_error_timer_over:
                brenner.cancel_error()
                logger.info(f"handle_brenner_mit_stoerung(): {brenner.label} loeschen()!")
                brenner.loeschen()
                continue

    def brenner_zuenden(self) -> bool:
        ok = self.modulation_soll.brenner_zuenden(brenner_zustaende=self.brenner_zustaende)
        self._update_relais()
        return ok

    def brenner_loeschen(self) -> bool:
        ok = self.modulation_soll.brenner_loeschen(brenner_zustaende=self.brenner_zustaende)
        self._update_relais()
        return ok

    def set_modulation_min(self) -> None:
        self.modulation_soll.set_modulation_min()
        self._update_relais()

    def set_brenner_modulation_manual_max(self) -> None:
        """
        Temporaere einfache Lösung
        Langfristig
          Zustand der Brenner abfragen und 'zwei_brenner' sinnvoll
          initialisieren.
        """
        for brenner in self.modulation_soll.zwei_brenner:
            brenner.set_max()
        self._update_relais()

    def set_modulation(self, brenner_num: BrennerNum, modulation: Modulation) -> None:
        """
        Only referenced by ScenarioOekofenBrennerModulation.
        """
        self.modulation_soll.set_modulation(brenner_num=brenner_num, modulation=modulation)
        self._update_relais()

    def _update_relais(self) -> None:
        relais = self.ctx.hsm_zentral.relais
        relais.relais_2_brenner1_sperren = self.modulation_soll.zwei_brenner[0].is_off
        relais.relais_4_brenner2_sperren = self.modulation_soll.zwei_brenner[1].is_off
        relais.relais_3_brenner1_anforderung = self.modulation_soll.zwei_brenner[0].is_on
        relais.relais_5_brenner2_anforderung = self.modulation_soll.zwei_brenner[1].is_on
