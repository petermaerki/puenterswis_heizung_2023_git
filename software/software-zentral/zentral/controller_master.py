"""
Liest speicher_ladung_prozent

Setzt temperaturen von Brenner 1 und 2
Sperrt Brenner
"""

import logging
import time
import typing

from zentral.constants import TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT
from zentral.handler_last import HandlerLast
from zentral.handler_oekofen import HandlerOekofen
from zentral.handler_pumpe import HandlerPumpe
from zentral.handler_sp_zentral import HandlerSpZentral
from zentral.util_scenarios import SCENARIOS, ScenarioControllerMinusEinHaus, ScenarioControllerPlusEinHaus
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
        haeuser_ladung_minimum_prozent, haeuser_ladung_avg_prozent = ctx.hsm_zentral.tuple_haeuser_ladung_minimum_prozent

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

        if haeuser_ladung_avg_prozent < 20.0 and self.ctx.is_winter:
            """Im Winder braucht es Reserve und der erste Brenne muss rechtzeitig gezündet werden."""
            if self.handler_oekofen.erster_brenner_zuenden():
                logger.info("erster_brenner_zuenden() damit Reserve im Winter")

        # Zweiter brenner loeschen
        if haeuser_ladung_avg_prozent > 40.0 and sp_ladung_zentral >= SpLadung.LEVEL3:
            if self.handler_oekofen.zweiter_brenner_loeschen():
                logger.info("sp_zentral_zu_warm: zweiter_brenner_loeschen() damit nicht am Schluss beide geloescht werden muessen")

        if SCENARIOS.remove_if_present(ScenarioControllerPlusEinHaus):
            if self.handler_last.plus_1_valve(now_s=now_s):
                logger.info("SCENARIO: sp_zentral_zu_warm: plus_1_valve()")
            return

        if SCENARIOS.remove_if_present(ScenarioControllerMinusEinHaus):
            if self.handler_last.minus_1_valve(now_s=now_s):
                logger.info("SCENARIO: sp_zentral_zu_kalt: minus_1_valve()")
            return

        if not self.handler_last.actiontimer.is_over:
            return

        def sp_dezentral_vorausschauend_laden():
            """Aufgrund der letzten Tage und daraus der Prognose für die Zukunft werden die dezentralen Speicher vorgeladen."""
            VERBRAUCH_W_ZU_VORLADEN_PROZENT = 5.0 / 1000.0
            VORAUSSCHAUEN_ZEIT_S = 3 * 3600
            sp_verbrauch_median_W = ctx.sp_verbrauch_median_W(time_s=time.time() + VORAUSSCHAUEN_ZEIT_S)
            haeuser_ladung_avg_prozent_soll = sp_verbrauch_median_W * VERBRAUCH_W_ZU_VORLADEN_PROZENT
            logger.info(f"In {VORAUSSCHAUEN_ZEIT_S=} erwarte ich {sp_verbrauch_median_W=:0.0f} und möchte daher jetzt {haeuser_ladung_avg_prozent_soll=:0.0f}")
            abweichung_prozent = max(0.0, haeuser_ladung_avg_prozent_soll - haeuser_ladung_avg_prozent)
            ladende_haeuser_soll = round(abweichung_prozent / 5.0)
            ladende_hauser = self.ctx.hsm_zentral.get_haeuser_ladung().effective_valve_open_count
            if haeuser_ladung_avg_prozent < haeuser_ladung_avg_prozent_soll:
                if ladende_hauser < ladende_haeuser_soll:
                    if self.handler_last.plus_1_valve(now_s=now_s):
                        logger.info(f"{ladende_hauser=}, {ladende_haeuser_soll=}. Um die dezentralen Speicher vorzuladen: plus_1_valve().")

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
                # if self.ctx.is_sommer:
                #     return
                # if haeuser_ladung_avg_prozent > 20.0:
                #     return
                # if haeuser_ladung_minimum_prozent > -10.0:
                #     return
                if sp_ladung_zentral == SpLadung.LEVEL0:
                    if self.handler_oekofen.brenner_zuenden():
                        logger.info("zweiten Brenner zünden: sp_zentral_zu_kalt: brenner_zuenden()")

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
