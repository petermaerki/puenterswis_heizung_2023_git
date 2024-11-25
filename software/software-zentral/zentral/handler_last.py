import logging
import typing

from zentral.constants import ABSCHALTGRENZE_BAND, ENABLE_TFV_ADAPTIV, SORT_BY_LADUNG_INDIVIDUELL_UND_HAUSREIHE_KORREKTUR, TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT
from zentral.util_action import ActionBaseEnum, ActionTimer
from zentral.util_controller_haus_ladung import HaeuserLadung, HausLadung

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class LastAction(ActionBaseEnum):
    HAUS_PLUS = 5
    HAUS_MINUS = 5


TFV_NORMAL_C = 68.0
TFV_LEGIONELLEN_KILL_C = 75.0
TPV_TEMPERATURHUB_C = 10.0
TPV_MIN_C = 40.0


class HandlerLast:
    def __init__(self, ctx: "Context", now_s: float):
        assert isinstance(now_s, float)
        self.ctx = ctx
        self.now_s = now_s
        self.actiontimer = ActionTimer()
        self.mock_solltemperatur_Tfv_C: float | None = None
        self.boost_Tfv: bool = False
        self.legionellen_kill_in_progress: bool = False
        self.target_valve_open_count: int = 0

    @property
    def solltemperatur_Tfv_C(self) -> float:
        if self.mock_solltemperatur_Tfv_C is not None:
            return self.mock_solltemperatur_Tfv_C

        if ENABLE_TFV_ADAPTIV:
            return self._solltemperatur_adaptiv_Tfv_C

        if self.legionellen_kill_in_progress:
            return TFV_LEGIONELLEN_KILL_C
        return TFV_NORMAL_C

    @property
    def _solltemperatur_adaptiv_Tfv_C(self) -> float:
        assert ENABLE_TFV_ADAPTIV
        list_sp_temperatur_mitte_C: list[float] = []
        list_ladung_individuell_prozent: list[float] = []

        def loop_haeuser_with_valve_open():
            haeuser_ladung = self.ctx.hsm_zentral.get_haeuser_ladung()
            for haus_ladung in haeuser_ladung:
                if not haus_ladung.valve_open:
                    continue
                sp_temperatur_mitte_C = haus_ladung.haus.status_haus.hsm_dezentral.modbus_iregs_all.sp_temperatur.mitte_C
                list_sp_temperatur_mitte_C.append(sp_temperatur_mitte_C)
                list_ladung_individuell_prozent.append(haus_ladung.ladung_individuell_prozent)

        loop_haeuser_with_valve_open()

        if len(list_ladung_individuell_prozent) == 0:
            return 0.0

        min_ladung_individuell_prozent = min(list_ladung_individuell_prozent)

        if True:
            if min_ladung_individuell_prozent > 0.0:
                self.boost_Tfv = False
            if min_ladung_individuell_prozent < -10.0:
                self.boost_Tfv = True

            if self.boost_Tfv:
                return TFV_LEGIONELLEN_KILL_C

        # boost_Tfv_C = TPV_MIN_C - min_ladung_individuell_prozent / 5.0 * TFV_LEGIONELLEN_KILL_C
        # """Boost Temperature steigt bei negativer ladung schnell an"""

        Taussen_C = self.ctx.modbus_communication.pcbs_dezentral_heizzentrale.TaussenU_C
        TEMPERATURHUB_KAELTE_C = max(0.0, 12.0 - Taussen_C)
        """
        Bei kalten Temperaturen muss der Vorlauf hoeher sein damit genügend Leistung geliefert wird.
        Beispiel: 
        Taussen_C 12.0  temperatur_mitte_C 30.0 -> adaptiv_soll_Tfv_C = 40.0
        Taussen_C 0.0  temperatur_mitte_C 30.0 -> adaptiv_soll_Tfv_C = 52.0
        """
        adaptiv_soll_Tfv_C = max(list_sp_temperatur_mitte_C) + TPV_TEMPERATURHUB_C + TEMPERATURHUB_KAELTE_C
        # adaptiv_soll_Tfv_C = max(adaptiv_soll_Tfv_C, boost_Tfv_C)
        adaptiv_soll_Tfv_C = max(40.0, adaptiv_soll_Tfv_C)
        adaptiv_soll_Tfv_C = min(75.0, adaptiv_soll_Tfv_C)
        return adaptiv_soll_Tfv_C

    def influxdb_add_fields(self, fields: dict[str, float]) -> None:
        self.actiontimer.influxdb_add_fields(fields=fields)

    def update_valves(self, now_s: float) -> None:
        """
        Haus zu warm: Ventil schliessen.
        Haus zu kalt: Ventil öffnen.
        """
        haeuser_ladung = self.ctx.hsm_zentral.get_haeuser_ladung()

        def abschaltgrenze_band() -> None:
            """
            Um die Rücklauftemperatur möglichst tief zu halten
            sollen Valves der Häuser mit der höchsten Rücklauftemperatur geschlossen werden.
            """

            def minimale_ladung_not_valve_open() -> float:
                list_ladung_individuell_prozent_not_valve_open: list[float] = []
                for haus_ladung in haeuser_ladung:
                    if not haus_ladung.valve_open:
                        list_ladung_individuell_prozent_not_valve_open.append(haus_ladung.ladung_individuell_prozent)
                if len(list_ladung_individuell_prozent_not_valve_open) == 0:
                    return 100.0
                return min(list_ladung_individuell_prozent_not_valve_open)

            selected_haus = self._find_minus_1_valve(haeuser_ladung=haeuser_ladung, now_s=now_s, log_info=False)
            if selected_haus is not None:
                ABSCHALTGRENZE_BAND_PROZENT = 45.0  # gute Werte 30.0 ... 80.0 ?

                abschaltgrenze_prozent = minimale_ladung_not_valve_open() + ABSCHALTGRENZE_BAND_PROZENT
                if selected_haus.ladung_individuell_prozent > abschaltgrenze_prozent:
                    changed = selected_haus.set_valve(valve_open=False)
                    assert changed
                    logger.info(f"{selected_haus.haus.influx_tag} valve closed, ladung_individuell {selected_haus.ladung_individuell_prozent:0.1f}% >= ABSCHALTGRENZE_PROZENT {abschaltgrenze_prozent:0.1f}%")

        if ABSCHALTGRENZE_BAND:  # and not self.ctx.is_vorladen_aktiv:
            abschaltgrenze_band()

        self.legionellen_kill_in_progress = haeuser_ladung.legionellen_kill_in_progress

        for haus_ladung in haeuser_ladung:
            if haus_ladung.ladung_individuell_prozent >= 100.0 and not self.ctx.is_vorladen_aktiv or haus_ladung.ladung_prozent >= 100:
                if self.legionellen_kill_in_progress:
                    if haus_ladung.legionellen_kill_required:
                        if self.ctx.modbus_communication.pcbs_dezentral_heizzentrale.sp_ladung_zentral_prozent > 25.0:
                            # if self.ctx.modbus_communication._sp_ladung_zentral.ladung_prozent > 25.0:
                            # Abschaltkriterium gilt nicht bei Legionellen kill.
                            continue
                changed = haus_ladung.set_valve(valve_open=False)
                if changed:
                    logger.info(f"{haus_ladung.haus.influx_tag} valve closed, ladung_individuell {haus_ladung.ladung_individuell_prozent:0.1f}% >= 100.0%")

            EINSCHALT_GRENZE_LADUNG_INDIVIDUELL_PROZENT = 5.0
            if haus_ladung.ladung_individuell_prozent <= EINSCHALT_GRENZE_LADUNG_INDIVIDUELL_PROZENT:
                changed = haus_ladung.set_valve(valve_open=True)
                if changed:
                    logger.info(f"{haus_ladung.haus.influx_tag} valve opened, ladung_individuell {haus_ladung.ladung_individuell_prozent:0.1f}% <= {EINSCHALT_GRENZE_LADUNG_INDIVIDUELL_PROZENT:0.1f}")

    def reduce_valve_open_count(self, now_s: float) -> bool:
        """
        effective_valve_open_count reduzieren bis target_valve_open_count

        return True: Falls ein Ventil geschlossen werden konnte
        """
        effective_valve_open_count = self.ctx.hsm_zentral.get_haeuser_ladung().effective_valve_open_count

        success = False
        while effective_valve_open_count > self.target_valve_open_count:
            if not self._minus_1_valve(now_s=now_s):
                break
            success = True
            effective_valve_open_count -= 1

        return success

    def increase_valve_open_count(self, now_s: float) -> bool:
        """
        effective_valve_open_count erhöhen bis target_valve_open_count

        return True: Falls ein Ventil geöffnet werden konnte
        """
        effective_valve_open_count = self.ctx.hsm_zentral.get_haeuser_ladung().effective_valve_open_count

        success = False
        while effective_valve_open_count < self.target_valve_open_count:
            if not self._plus_1_valve(now_s=now_s):
                break
            success = True
            effective_valve_open_count += 1

        return success

    def plus_1_valve(self, now_s: float) -> bool:
        success = self._plus_1_valve(now_s=now_s)
        if not TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT:
            if success:
                self.target_valve_open_count += 1
        return success

    def _plus_1_valve(self, now_s: float) -> bool:
        """
        Versuche ein valve zu öffnen.
        return true:
          falls dies möglich war
          LastAction.HAUS_PLUS
        KEINE Veränderung von target_valve_open_count
        """
        haeuser_to_choose_from: HaeuserLadung = HaeuserLadung()

        haeuser_ladung = self.ctx.hsm_zentral.get_haeuser_ladung()
        for haus_ladung in haeuser_ladung:
            if haus_ladung.valve_open:
                continue

            if haus_ladung.legionellen_kill_required:
                haeuser_to_choose_from = HaeuserLadung([haus_ladung])
                break

            if haus_ladung.ladung_individuell_prozent >= 80.0:
                continue
            haeuser_to_choose_from.append(haus_ladung)

        if len(haeuser_to_choose_from) == 0:
            return False

        selected_haus = self._select_haus(
            haeuser_to_choose_from=haeuser_to_choose_from,
            now_s=now_s,
            plus1_valve=True,
            log_info=True,
        )
        selected_haus.set_valve(valve_open=True)
        logger.info(f"{selected_haus.haus.influx_tag} geoeffnet: valve_open=True")
        self.actiontimer.action = LastAction.HAUS_PLUS
        return True

    def minus_1_valve(self, now_s: float) -> bool:
        if not TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT:
            if self.target_valve_open_count == 0:
                return False
        success = self._minus_1_valve(now_s=now_s)
        if not TEST_SIMPLIFY_TARGET_VALVE_OPEN_COUNT:
            if success:
                self.target_valve_open_count -= 1
        return success

    def _find_minus_1_valve(self, haeuser_ladung: HaeuserLadung, now_s: float, log_info: bool) -> HausLadung | None:
        haeuser_to_choose_from: HaeuserLadung = HaeuserLadung()
        # if self.ctx.is_vorladen_aktiv:
        #     return
        for haus_ladung in haeuser_ladung:
            if not haus_ladung.valve_open:
                continue
            if haus_ladung.ladung_individuell_prozent <= 30.0:
                continue
            if haus_ladung.legionellen_kill_required:
                continue
            haeuser_to_choose_from.append(haus_ladung)

        if len(haeuser_to_choose_from) == 0:
            return None

        return self._select_haus(
            haeuser_to_choose_from=haeuser_to_choose_from,
            now_s=now_s,
            plus1_valve=False,
            log_info=log_info,
        )

    def _minus_1_valve(self, now_s: float) -> bool:
        """
        Versuche ein valve zu schliessen.
        return true:
          falls dies möglich war
          LastAction.HAUS_MINUS
        KEINE Veränderung von target_valve_open_count
        """
        haeuser_ladung = self.ctx.hsm_zentral.get_haeuser_ladung()

        selected_haus = self._find_minus_1_valve(
            haeuser_ladung=haeuser_ladung,
            now_s=now_s,
            log_info=True,
        )
        if selected_haus is None:
            return False
        selected_haus.set_valve(valve_open=False)
        logger.info(f"{selected_haus.haus.influx_tag} geschlossen: valve_open=False")
        self.actiontimer.action = LastAction.HAUS_MINUS
        return True

    def _select_haus(self, haeuser_to_choose_from: HaeuserLadung, now_s: float, plus1_valve: bool, log_info: bool = True) -> HausLadung:
        if SORT_BY_LADUNG_INDIVIDUELL_UND_HAUSREIHE_KORREKTUR:
            hausreihe_korrektur_vorzeichen = -1.0 if plus1_valve else 1.0

            hausreihen = self.ctx.config_etappe.hausreihen.calculate(now_s=now_s)
            haeuser_to_choose_from.sort_by_ladung_individuell_und_hausreihe_korrektur(
                hausreihen=hausreihen,
                hausreihe_korrektur_vorzeichen=hausreihe_korrektur_vorzeichen,
            )
        else:
            haeuser_to_choose_from.sort_by_ladung_indiviuell()

        selected_haus = haeuser_to_choose_from[0 if plus1_valve else -1]

        if SORT_BY_LADUNG_INDIVIDUELL_UND_HAUSREIHE_KORREKTUR:
            hausreihe_korrektur_prozent = hausreihe_korrektur_vorzeichen * hausreihen.korrektur_prozent(haus_ladung=selected_haus)
            comment = f"{hausreihe_korrektur_prozent:+0.1f}%"
        else:
            comment = ""
        if log_info:
            label = "plus1_valve" if plus1_valve else "minus1_valve"
            logger.info(f"Selected: {label}: {selected_haus.haus.influx_tag} hausreihe '{selected_haus.hausreihe.label}': {selected_haus.ladung_individuell_prozent:0.1f}%{comment}")

        return selected_haus
