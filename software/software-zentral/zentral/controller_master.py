"""
Liest speicher_ladung_prozent

Setzt temperaturen von Brenner 1 und 2
Sperrt Brenner
"""

import logging
import time
import typing

from zentral.constants import TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT, VORAUSSCHAUEND_LADEN
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
        self.haeuser_ladung_avg_soll_prozent = 0.0

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
            return

        def brenner_geloescht_valves_zu():
            # Brenner aus: Last Target auf 0
            if self.handler_oekofen.anzahl_brenner_on == 0:
                # Last Target auf 0
                self.handler_last.target_valve_open_count = 0
                # Valve schliessen falls möglich
                self.handler_last.reduce_valve_open_count(now_s=now_s)

        # Falls alle valve zu sind, Modulation auf Minimum
        all_valves_closed = ctx.hsm_zentral.haeuser_all_valves_closed
        logger.debug(f"{betrieb_notheizung=} {all_valves_closed=} {sp_ladung_zentral=}")
        if all_valves_closed and self.ctx.is_sommer:
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
            if not self.ctx.vorladen_aktiv:
                brenner_geloescht_valves_zu()
                logger.debug("brenner_geloescht_valves_zu()")

        # Erster Brenner zünden
        if sp_ladung_zentral <= SpLadung.LEVEL1:
            self.handler_oekofen.erster_brenner_zuenden()

        if sp_ladung_zentral <= SpLadung.LEVEL2 and self.ctx.is_winter:  # haeuser_ladung_avg_prozent < 30.0 and self.ctx.is_winter:
            """Im Winter braucht es Reserve und der erste Brenner muss rechtzeitig gezündet werden."""
            if self.handler_oekofen.erster_brenner_zuenden():
                logger.info("erster_brenner_zuenden() damit Reserve im Winter")

        # Zweiter brenner loeschen
        if haeuser_ladung_avg_prozent > 40.0 and sp_ladung_zentral >= SpLadung.LEVEL3 and not self.ctx.is_vorladen_aktiv:
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
            VORAUSSCHAUEN_ZEIT_h_list = [0.5, 1.0, 1.5, 2, 2.5, 3, 3.5, 4]
            sp_verbrauch_W_list = [0.0]
            for vorausschauen_zeit_h in VORAUSSCHAUEN_ZEIT_h_list:
                sp_verbrauch_W = ctx.sp_verbrauch_W(time_s=time.time() + vorausschauen_zeit_h * 3600)
                if sp_verbrauch_W > 1.0:
                    """Falls Messwert vorhanden"""
                    sp_verbrauch_W_list.append(sp_verbrauch_W)
            if len(sp_verbrauch_W_list) == 0:
                return
            # sp_verbrauch_alle_W = sum(sp_verbrauch_W_list) / len(sp_verbrauch_W_list)  # Mittelwert ist ruhiger aber zu tief
            sp_verbrauch_alle_W = max(sp_verbrauch_W_list)  # Max

            haeuser_anzahl = len(self.ctx.config_etappe.haeuser)
            MINIMALE_LADUNG_PROZENT = 20.0
            VORLADUNG_STUNDEN = 3.0
            energie_haus_Wh = 13000.0  # 500 Liter um 20C wärmen, ganz grob
            # Ich betrachte nur einen Brenner
            RESERVE_FAKTOR = 1.5  # normal 1.0, je grösser desto mehr Reserve in der Vorladung
            haeuser_ladung_avg_soll_prozent = MINIMALE_LADUNG_PROZENT + RESERVE_FAKTOR * (sp_verbrauch_alle_W - self.ctx.config_etappe.brenner_einzeln_leistung_W) * VORLADUNG_STUNDEN / (haeuser_anzahl * energie_haus_Wh) * 100.0
            haeuser_ladung_avg_soll_prozent = min(65.0, haeuser_ladung_avg_soll_prozent)
            haeuser_ladung_avg_soll_prozent = max(20.0, haeuser_ladung_avg_soll_prozent)
            self.haeuser_ladung_avg_soll_prozent = haeuser_ladung_avg_soll_prozent
            if haeuser_ladung_avg_prozent > self.haeuser_ladung_avg_soll_prozent + 2.0:
                self.ctx.vorladen_aktiv = False
            if haeuser_ladung_avg_prozent < self.haeuser_ladung_avg_soll_prozent - 2.0:
                self.ctx.vorladen_aktiv = True
            ladende_haeuser = self.ctx.hsm_zentral.get_haeuser_ladung().effective_valve_open_count
            if self.ctx.vorladen_aktiv:
                if sp_ladung_zentral < SpLadung.LEVEL3:
                    if self.handler_oekofen.erster_brenner_zuenden():
                        logger.info("sp_dezentral_vorausschauend_laden(): erster_brenner_zuenden()")
                        return
                    if self.ctx.is_winter:  # and pcbs._sp_ladung_zentral.ladung_prozent < 60.0:
                        if self.handler_oekofen.modulation_erhoehen():
                            logger.info("sp_dezentral_vorausschauend_laden(): modulation_erhoehen()")
                            return
                if ladende_haeuser < 2:  # vorher 7, neu Modulation starten und mindestens ein einzelnes
                    if self.handler_last.plus_1_valve(now_s=now_s):
                        logger.info(f"{ladende_haeuser=} sp_dezentral_vorausschauend_laden(): Um die dezentralen Speicher vorzuladen: plus_1_valve().")
                        return
                if sp_ladung_zentral >= SpLadung.LEVEL3:
                    if ladende_haeuser < 5:
                        if self.handler_last.plus_1_valve(now_s=now_s):
                            logger.info(f"{ladende_haeuser=} sp_dezentral_vorausschauend_laden(): Um die dezentralen Speicher vorzuladen: plus_1_valve().")
                            return

        if VORAUSSCHAUEND_LADEN:
            sp_dezentral_vorausschauend_laden()

        def sp_zentral_zu_warm():
            if self.handler_sp_zentral.steigt:
                if not TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT:
                    if self.handler_last.increase_valve_open_count(now_s=now_s):
                        logger.info("sp_zentral_zu_warm: increase_valve_open_count()")
                        return
                if not self.ctx.is_vorladen_aktiv:
                    if self.handler_oekofen.modulation_reduzieren():
                        logger.info("sp_zentral_zu_warm: modulation_reduzieren()")
                        return
                if self.handler_last.plus_1_valve(now_s=now_s):
                    logger.info("sp_zentral_zu_warm: plus_1_valve()")
                    return
                if self.handler_oekofen.zweiter_brenner_loeschen():
                    logger.info("sp_zentral_zu_warm: zweiter_brenner_loeschen()")
                    brenner_geloescht_valves_zu()

        def sp_zentral_zu_kalt():
            if self.handler_sp_zentral.sinkt:
                if not TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT:
                    if self.handler_last.reduce_valve_open_count(now_s=now_s):
                        logger.info("sp_zentral_zu_kalt: reduce_valve_open_count()")
                        return
                if self.ctx.is_winter:
                    if self.handler_oekofen.modulation_erhoehen():
                        logger.info("sp_zentral_zu_kalt: modulation_erhoehen()")
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
