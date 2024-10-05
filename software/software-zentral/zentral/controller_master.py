"""
Liest speicher_ladung_prozent

Setzt temperaturen von Brenner 1 und 2
Sperrt Brenner
"""

import logging
import typing

from zentral.handler_anhebung import HandlerAnhebung
from zentral.handler_oekofen import HandlerOekofen
from zentral.handler_pumpe import HandlerPumpe
from zentral.handler_sp_zentral import HandlerSpZentral
from zentral.util_sp_ladung_zentral import SpLadung

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class ControllerMaster:
    def __init__(self, ctx: "Context", now_s: float) -> None:
        self.ctx = ctx
        self.now_s = now_s
        self.handler_oekofen = HandlerOekofen(ctx=ctx, now_s=now_s)
        self.handler_pumpe = HandlerPumpe(ctx=ctx, now_s=now_s)
        # ladung = ctx.hsm_zentral.get_haeuser_ladung()
        # last_valve_open_count = ladung.valve_open_count
        last_valve_open_count = 0  # TODO: Add correct value
        self.handler_anhebung = HandlerAnhebung(
            now_s=now_s,
            last_anhebung_prozent=0.0,
            last_valve_open_count=last_valve_open_count,
        )
        self.handler_sp_zentral = HandlerSpZentral()

    def done(self) -> bool:
        return False

    def process(self, now_s: float) -> None:
        self._process(now_s=now_s)

        hvv = self.handler_anhebung.calculate_hvv(haeuser_ladung=self.ctx.hsm_zentral.get_haeuser_ladung())
        self.ctx.hsm_zentral.update_hvv(hvv=hvv)

    def _process(self, now_s: float) -> None:
        ctx = self.ctx
        pcbs = ctx.modbus_communication.pcbs_dezentral_heizzentrale
        sp_ladung_zentral = pcbs.sp_ladung_zentral
        self.handler_sp_zentral.set(ladung_prozent=pcbs._sp_ladung_zentral.ladung_prozent)

        if sp_ladung_zentral > SpLadung.LEVEL1:
            self.handler_pumpe.tick(now_s=now_s)
        else:
            self.handler_pumpe.tick_pwm(now_s=now_s)

        betrieb_notheizung = self.handler_oekofen.betrieb_notheizung
        self.handler_oekofen.handler_elektro_notheizung.update(ctx=ctx, betrieb_notheizung=betrieb_notheizung)

        if not ctx.hsm_zentral.is_drehschalterauto_regeln():
            # Manual Mode
            # TODO: Aufstarten... Flash nicht zu oft schreiben
            self.handler_oekofen.set_brenner_modulation_manual_max()

        all_valves_closed = ctx.hsm_zentral.haeuser_all_valves_closed
        logger.debug(f"{betrieb_notheizung=} {all_valves_closed=} {sp_ladung_zentral=}")
        if all_valves_closed:
            logger.debug("set_modulation_min()")
            self.handler_oekofen.set_modulation_min()

        # Anhebung hinunter
        if sp_ladung_zentral <= SpLadung.LEVEL1:
            if self.handler_sp_zentral.sinkt:
                self.handler_anhebung.anheben_minus_ein_haus(now_s=now_s, haeuser_ladung=self.ctx.hsm_zentral.get_haeuser_ladung())

        #  Anhebung hinauf
        if sp_ladung_zentral >= SpLadung.LEVEL3:
            if self.handler_oekofen.anzahl_brenner_on > 0:
                if self.handler_sp_zentral.steigt:
                    if self.handler_anhebung.last_valve_open_count < 5:
                        self.handler_anhebung.anheben_plus_ein_haus(now_s=now_s, haeuser_ladung=self.ctx.hsm_zentral.get_haeuser_ladung())

        # Brenner zünden
        if pcbs._sp_ladung_zentral.ladung_prozent < 25.0:
            if self.handler_oekofen.erster_brenner_zuenden():
                return

        # Modulation erhöhen
        if sp_ladung_zentral == SpLadung.LEVEL0:
            if not all_valves_closed:
                if self.handler_sp_zentral.sinkt:
                    if not self.handler_oekofen.modulation_erhoehen():
                        if self.handler_oekofen.brenner_zuenden():
                            return

        # Modulation reduzieren
        if pcbs._sp_ladung_zentral.ladung_prozent > 55.0:
            if self.handler_sp_zentral.steigt:
                if self.handler_oekofen.modulation_reduzieren():
                    return

        #  Brenner löschen
        if sp_ladung_zentral == SpLadung.LEVEL4:
            self.handler_oekofen.brenner_loeschen()

    def influxdb_add_fields(self, fields: dict[str, float]) -> None:
        self.handler_oekofen.modulation_soll.actiontimer.influxdb_add_fields(fields=fields)
        self.handler_pumpe._actiontimer_pumpe_aus_zu_kalt.influxdb_add_fields(fields=fields)
        self.handler_pumpe._actiontimer_pwm.influxdb_add_fields(fields=fields)
        self.handler_anhebung.influxdb_add_fields(fields=fields)
