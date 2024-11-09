"""
Liest speicher_ladung_prozent

Setzt temperaturen von Brenner 1 und 2
Sperrt Brenner
"""

import logging
import typing

from zentral.constants import TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT
from zentral.handler_last import HandlerLast
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
        self.handler_last = HandlerLast(ctx=ctx, now_s=now_s)
        self.handler_sp_zentral = HandlerSpZentral()

    def done(self) -> bool:
        return False

    def process(self, now_s: float) -> None:
        self.handler_last.update_valves(now_s=now_s)
        self.handler_oekofen.update_brenner_relais()
        self.handler_oekofen.modulation_soll.update_burnout()

        self._process(now_s=now_s)

    def _process(self, now_s: float) -> None:
        ctx = self.ctx
        pcbs = ctx.modbus_communication.pcbs_dezentral_heizzentrale
        sp_ladung_zentral = pcbs.sp_ladung_zentral
        self.handler_sp_zentral.set(now_s=now_s, ladung_prozent=pcbs._sp_ladung_zentral.ladung_prozent)

        betrieb_notheizung = self.handler_oekofen.betrieb_notheizung
        self.handler_oekofen.handler_elektro_notheizung.update(ctx=ctx, betrieb_notheizung=betrieb_notheizung)

        if not ctx.hsm_zentral.is_state_drehschalterauto():
            # Manual Mode
            self.handler_oekofen.set_brenner_modulation_manual_max()

        # Brenner aus: Last Target auf 0
        if self.handler_oekofen.anzahl_brenner_on == 0:
            # Last Target auf 0
            self.handler_last.target_valve_open_count = 0
            # Valve schliessen falls möglich
            self.handler_last.reduce_valve_open_count(now_s=now_s)

        # Falls alle valve zu sind, Modulation auf Minimum
        all_valves_closed = ctx.hsm_zentral.haeuser_all_valves_closed
        logger.debug(f"{betrieb_notheizung=} {all_valves_closed=} {sp_ladung_zentral=}")
        if all_valves_closed:
            logger.debug("set_modulation_min() weil alle valves closed")
            self.handler_oekofen.set_modulation_min()

        # Fernleitungspumpe Modulieren
        if sp_ladung_zentral > SpLadung.LEVEL1:
            self.handler_pumpe.tick(now_s=now_s)
        else:
            self.handler_pumpe.tick_pwm(now_s=now_s)

        # Brenner mit Störung
        self.handler_oekofen.handle_brenner_mit_stoerung()

        # Brenner loeschen
        if sp_ladung_zentral == SpLadung.LEVEL4:
            self.handler_oekofen.brenner_sofort_loeschen()

        # Erster Brenner zünden
        if sp_ladung_zentral <= SpLadung.LEVEL1:
            self.handler_oekofen.erster_brenner_zuenden()

        if not self.handler_last.actiontimer.is_over:
            return

        def sp_zentral_zu_warm():
            if self.handler_sp_zentral.steigt:
                if not TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT:
                    if self.handler_last.increase_valve_open_count(now_s=now_s):
                        logger.info("sp_zentral_zu_warm: increase_valve_open_count()")
                        return
                if self.handler_oekofen.modulation_reduzieren():
                    logger.info("sp_zentral_zu_warm: modulation_reduzieren()")
                    return
                if self.handler_last.plus_1_valve(now_s=now_s):
                    logger.info("sp_zentral_zu_warm: plus_1_valve()")
                    return
                if self.handler_oekofen.zweiter_brenner_loeschen():
                    logger.info("sp_zentral_zu_warm: zweiter_brenner_loeschen()")

        def sp_zentral_zu_kalt():
            if self.handler_sp_zentral.sinkt:
                if not TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT:
                    if self.handler_last.reduce_valve_open_count(now_s=now_s):
                        logger.info("sp_zentral_zu_kalt: reduce_valve_open_count()")
                        return
                if self.handler_last.minus_1_valve(now_s=now_s):
                    logger.info("sp_zentral_zu_kalt: minus_1_valve()")
                    return
                if self.handler_oekofen.modulation_erhoehen():
                    logger.info("sp_zentral_zu_kalt: modulation_erhoehen()")
                    return
                if sp_ladung_zentral == SpLadung.LEVEL0:
                    if self.handler_oekofen.brenner_zuenden():
                        logger.info("sp_zentral_zu_kalt: brenner_zuenden()")

        if sp_ladung_zentral >= SpLadung.LEVEL3:
            if self.handler_oekofen.anzahl_brenner_on >= 1:
                sp_zentral_zu_warm()

        if sp_ladung_zentral <= SpLadung.LEVEL1:
            sp_zentral_zu_kalt()

    def influxdb_add_fields(self, fields: dict[str, float]) -> None:
        self.handler_oekofen.modulation_soll.influxdb_add_fields(fields=fields)
        self.handler_pumpe._actiontimer_pumpe_aus_zu_kalt.influxdb_add_fields(fields=fields)
        self.handler_pumpe._actiontimer_pwm.influxdb_add_fields(fields=fields)
        self.handler_last.influxdb_add_fields(fields=fields)
