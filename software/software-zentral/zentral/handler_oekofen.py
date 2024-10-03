"""
Liest speicher_ladung_prozent

Setzt temperaturen von Brenner 1 und 2
Sperrt Brenner
"""

import logging
import typing

from zentral.handler_elektro_notheizung import HandlerElektroNotheizung
from zentral.util_modulation_soll import BrennerAction, Modulation, ModulationSoll
from zentral.util_oekofen_brenner_uebersicht import EnumBrennerUebersicht, brenner_uebersicht_prozent

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class HandlerOekofen:
    def __init__(self, ctx: "Context", now_s: float) -> None:
        self.ctx = ctx
        self.handler_elektro_notheizung = HandlerElektroNotheizung(now_s=now_s)
        self.modulation_soll = ModulationSoll(modulation0=Modulation.OFF, modulation1=Modulation.OFF)

    @property
    def is_over(self) -> bool:
        return self.modulation_soll.actiontimer.is_over

    @property
    def betrieb_notheizung(self) -> bool:
        brenner1, brenner2 = self.brenner_uebersicht_prozent
        return max(brenner1, brenner2) <= EnumBrennerUebersicht.AUSGESCHALTET_DURCH_BENUTZER

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
        ok = self.modulation_soll.modulation_erhoehen()
        self._update_relais()
        return ok

    def modulation_reduzieren(self) -> bool:
        """
        Return True: Falls die Leistung reduziert werden konnte.
        Return False: Bereits auf minimaler Leistung.
        """
        ok = self.modulation_soll.modulation_reduzieren()
        self._update_relais()
        return ok

    def brenner_zuenden(self) -> bool:
        ok = self.modulation_soll.brenner_zuenden()
        self._update_relais()
        return ok

    def brenner_loeschen(self) -> bool:
        ok = self.modulation_soll.brenner_loeschen()
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

    def _update_relais(self) -> None:
        relais = self.ctx.hsm_zentral.relais
        relais.relais_2_brenner1_sperren = self.modulation_soll.zwei_brenner[0].is_off
        relais.relais_4_brenner2_sperren = self.modulation_soll.zwei_brenner[1].is_off
        relais.relais_3_brenner1_anforderung = self.modulation_soll.zwei_brenner[0].is_on
        relais.relais_5_brenner2_anforderung = self.modulation_soll.zwei_brenner[1].is_on

    async def process_obsolete(self, ctx: "Context", now_s: float) -> None:
        hsm_zentral = ctx.hsm_zentral
        relais = hsm_zentral.relais

        brenner1, brenner2 = hsm_zentral.brenner_uebersicht_prozent
        betrieb_notheizung = max(brenner1, brenner2) <= EnumBrennerUebersicht.AUSGESCHALTET_DURCH_BENUTZER
        self.handler_elektro_notheizung.update(ctx=ctx, betrieb_notheizung=betrieb_notheizung)
        if betrieb_notheizung:
            return

        relais.relais_2_brenner1_sperren = self.modulation_soll.zwei_brenner[0].is_off
        relais.relais_4_brenner2_sperren = self.modulation_soll.zwei_brenner[1].is_off
        relais.relais_3_brenner1_anforderung = self.modulation_soll.zwei_brenner[0].is_on
        relais.relais_5_brenner2_anforderung = self.modulation_soll.zwei_brenner[1].is_on

        if hsm_zentral.haeuser_all_valves_closed:
            self.modulation_soll.set_modulation_min()

        pcbs = ctx.modbus_communication.pcbs_dezentral_heizzentrale
        sp_ladung = pcbs.sp_ladung_zentral
        self.modulation_soll.abschalten_zweiter_Brenner(sp_ladung=sp_ladung)

        if not self.actiontimer_brenner.is_over:
            # Ein Brenner started/stoppt/moduliert
            # Wir warten bis der neue Zustand stabil ist.
            return

        manual_mode = min(brenner1, brenner2) <= EnumBrennerUebersicht.AUSGESCHALTET_DURCH_BENUTZER

        # influx_data = InfluxData(ctx=ctx)
        # influx_data.add(zwei_brenner=oekofen_modulation_soll.zwei_brenner)

        # TICK!!!
        self.modulation_soll.tick(sp_ladung=sp_ladung, manual_mode=manual_mode)
        self.actiontimer_brenner.action = modulation_soll.action
        if modulation_soll.action != BrennerAction.NICHTS:
            # influx_data.add(zwei_brenner=oekofen_modulation_soll.zwei_brenner)
            # await influx_data.send()
            logger.info(f"Modulation: {modulation_soll.short}")
