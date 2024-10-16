import logging
import typing

from zentral.util_action import ActionBaseEnum, ActionTimer
from zentral.util_controller_haus_ladung import HaeuserLadung

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class LastAction(ActionBaseEnum):
    HAUS_PLUS = 5
    HAUS_MINUS = 5


class HandlerLast:
    def __init__(self, ctx: "Context", now_s: float):
        assert isinstance(now_s, float)
        self.ctx = ctx
        self.now_s = now_s
        self.actiontimer = ActionTimer()
        self.mock_solltemperatur_Tfv_C: float | None = None
        self.legionellen_kill_in_progress: bool = False
        self.target_valve_open_count: int = 0

    @property
    def solltemperatur_Tfv_C(self) -> float:
        if self.mock_solltemperatur_Tfv_C is not None:
            return self.mock_solltemperatur_Tfv_C
        if self.legionellen_kill_in_progress:
            return 75.0
        return 68.0

    def influxdb_add_fields(self, fields: dict[str, float]) -> None:
        self.actiontimer.influxdb_add_fields(fields=fields)

    def update_valves(self, now_s: float) -> None:
        # Haus zu warm: Ventil schliessen.
        # Haus zu kalt: Ventil öffnen.
        haeuser_ladung = self.ctx.hsm_zentral.get_haeuser_ladung()
        for haus_ladung in haeuser_ladung:
            if haus_ladung.ladung_individuell_prozent >= 100.0:
                if self.legionellen_kill_in_progress:
                    if haus_ladung.legionellen_kill_soon:
                        continue
                haus_ladung.set_valve(valve_open=False)
            if haus_ladung.ladung_individuell_prozent <= 0.0:
                haus_ladung.set_valve(valve_open=True)

    def legionellen_kill_start(self) -> bool:
        if self.legionellen_kill_in_progress:
            return False

        for haus_ladung in self.ctx.hsm_zentral.get_haeuser_ladung():
            if haus_ladung.legionellen_kill_soon:
                self.legionellen_kill_in_progress = True
                return True

        return False

    def legionellen_kill_start_if_urgent(self) -> None:
        for haus_ladung in self.ctx.hsm_zentral.get_haeuser_ladung():
            if haus_ladung.legionellen_kill_urgent:
                self.legionellen_kill_in_progress = True

    def legionellen_kill_cancel(self) -> bool:
        if not self.legionellen_kill_in_progress:
            return False

        self.legionellen_kill_in_progress = False
        return True

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
            if haus_ladung.ladung_individuell_prozent >= 80.0:
                continue
            haeuser_to_choose_from.append(haus_ladung)

        if len(haeuser_to_choose_from) == 0:
            return False

        haeuser_to_choose_from.sort_by_ladung_indiviuell()

        selected_haus = haeuser_to_choose_from[0]
        selected_haus.set_valve(valve_open=True)
        logger.info(f"_plus_1_valve {selected_haus.haus.influx_tag}")
        self.actiontimer.action = LastAction.HAUS_PLUS
        return True

    def minus_1_valve(self, now_s: float) -> bool:
        if self.target_valve_open_count == 0:
            return False
        success = self._minus_1_valve(now_s=now_s)
        if success:
            self.target_valve_open_count -= 1
        return success

    def _minus_1_valve(self, now_s: float) -> bool:
        """
        Versuche ein valve zu schliessen.
        return true:
          falls dies möglich war
          LastAction.HAUS_MINUS
        KEINE Veränderung von target_valve_open_count
        """
        haeuser_to_choose_from: HaeuserLadung = HaeuserLadung()

        haeuser_ladung = self.ctx.hsm_zentral.get_haeuser_ladung()
        for haus_ladung in haeuser_ladung:
            if not haus_ladung.valve_open:
                continue
            if haus_ladung.ladung_individuell_prozent <= 30.0:
                continue
            if self.legionellen_kill_in_progress:
                if haus_ladung.legionellen_kill_soon:
                    continue
            haeuser_to_choose_from.append(haus_ladung)

        if len(haeuser_to_choose_from) == 0:
            return False

        haeuser_to_choose_from.sort_by_ladung_indiviuell()

        selected_haus = haeuser_to_choose_from[-1]
        selected_haus.set_valve(valve_open=False)
        logger.info(f"_minus_1_valve {selected_haus.haus.influx_tag}")
        self.actiontimer.action = LastAction.HAUS_MINUS
        return True
