"""
Liest speicher_ladung_prozent

Setzt temperaturen von Brenner 1 und 2
Sperrt Brenner
"""

import logging
import time
import typing

from zentral.util_influx import InfluxRecords
from zentral.util_modulation_soll import BrennerAction, ZweiBrenner
from zentral.util_oekofen_brenner_uebersicht import EnumBrennerUebersicht

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class InfluxDataObsolete:
    def __init__(self, ctx: "Context") -> None:
        self.ctx = ctx
        self.records = InfluxRecords(ctx=ctx)

    def add(self, zwei_brenner: ZweiBrenner) -> None:
        fields = {}
        for brenner in zwei_brenner:
            fields[f"_brenner_{brenner.idx0+1}_modulation_soll_prozent"] = float(brenner.modulation.prozent) + brenner.idx0 * 0.3
        self.records.add_fields(fields=fields)

    async def send(self) -> None:
        await self.ctx.influx.write_records(records=self.records)


class ControllerOekofen:
    ELEKTRO_NOTHEIZUNG_Tsz4_MIN_C = 70.0
    ELEKTRO_NOTHEIZUNG_Tsz4_5MIN_C = 75.0
    ELEKTRO_NOTHEIZUNG_Tsz4_MAX_C = 75.0

    def __init__(self, now_s: float) -> None:
        self.last_tick_s: float = now_s
        self.elektro_notheizung_last_aus_s: float = time.monotonic()

    def _process_elektro_notheizung(self, ctx: "Context", betrieb_notheizung: bool) -> None:
        """
        betrieb_notheizung=True: Es ist kein Brenner verfügbar
        """
        if not betrieb_notheizung:
            # Kein Notheizbetrieb: Ausschalten
            ctx.hsm_zentral.relais.relais_1_elektro_notheizung = False
            return

        if ctx.hsm_zentral.relais.relais_1_elektro_notheizung:
            # Notheizung ist ein
            if ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C > self.ELEKTRO_NOTHEIZUNG_Tsz4_MAX_C:
                # Zu warm: Ausschalten
                ctx.hsm_zentral.relais.relais_1_elektro_notheizung = False
                self.elektro_notheizung_last_aus_s = time.monotonic()
            return

        # Notheizung ist aus
        if ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C < self.ELEKTRO_NOTHEIZUNG_Tsz4_MIN_C:
            # Zu kalt: Einschalten
            ctx.hsm_zentral.relais.relais_1_elektro_notheizung = True
            return

        if ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C < self.ELEKTRO_NOTHEIZUNG_Tsz4_5MIN_C:
            duration_aus_s = time.monotonic() - self.elektro_notheizung_last_aus_s
            if duration_aus_s > 5 * 60.0:
                # Zu kalt: Einschalten
                ctx.hsm_zentral.relais.relais_1_elektro_notheizung = True

    async def process(self, ctx: "Context", now_s: float) -> None:
        hsm_zentral = ctx.hsm_zentral
        oekofen_modulation_soll = hsm_zentral.oekofen_modulation_soll
        relais = hsm_zentral.relais

        brenner1, brenner2 = hsm_zentral.brenner_uebersicht_prozent
        betrieb_notheizung = max(brenner1, brenner2) <= EnumBrennerUebersicht.AUSGESCHALTET_DURCH_BENUTZER
        self._process_elektro_notheizung(ctx=ctx, betrieb_notheizung=betrieb_notheizung)
        if betrieb_notheizung:
            return

        relais.relais_2_brenner1_sperren = oekofen_modulation_soll.zwei_brenner[0].is_off
        relais.relais_4_brenner2_sperren = oekofen_modulation_soll.zwei_brenner[1].is_off
        relais.relais_3_brenner1_anforderung = oekofen_modulation_soll.zwei_brenner[0].is_on
        relais.relais_5_brenner2_anforderung = oekofen_modulation_soll.zwei_brenner[1].is_on

        if hsm_zentral.haeuser_all_valves_closed:
            oekofen_modulation_soll.set_modulation_min()

        pcbs = ctx.modbus_communication.pcbs_dezentral_heizzentrale
        sp_ladung = pcbs.sp_ladung_zentral
        oekofen_modulation_soll.abschalten_zweiter_Brenner(sp_ladung=sp_ladung)

        remaining_s = self.last_tick_s + oekofen_modulation_soll.action.wartezeit_s - now_s
        if remaining_s > 0.0:
            # Ein Brenner started/stoppt/moduliert
            # Wir warten bis der neue Zustand stabil ist.
            return

        manual_mode = min(brenner1, brenner2) <= EnumBrennerUebersicht.AUSGESCHALTET_DURCH_BENUTZER

        # influx_data = InfluxData(ctx=ctx)
        # influx_data.add(zwei_brenner=oekofen_modulation_soll.zwei_brenner)

        # TICK!!!
        oekofen_modulation_soll.tick(sp_ladung=sp_ladung, manual_mode=manual_mode)
        self.last_tick_s = now_s

        if oekofen_modulation_soll.action != BrennerAction.NICHTS:
            # influx_data.add(zwei_brenner=oekofen_modulation_soll.zwei_brenner)
            # await influx_data.send()
            logger.info(f"Modulation: {oekofen_modulation_soll.short}")
