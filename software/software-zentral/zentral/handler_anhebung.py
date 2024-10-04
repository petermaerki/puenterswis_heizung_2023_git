import logging
import typing

from zentral.util_action import ActionBaseEnum, ActionTimer
from zentral.util_controller_haus_ladung import HaeuserLadung
from zentral.util_controller_verbrauch_schaltschwelle import Evaluate, HauserValveVariante

if typing.TYPE_CHECKING:
    from zentral.context import Context


logger = logging.getLogger(__name__)


class AnhebungAction(ActionBaseEnum):
    """
    anhebung wird aktualisiert alle INTERVAL_ANHEBUNG_S.
    """

    HAUS_PLUS = 3
    HAUS_MINUS = 10


class HandlerAnhebung:
    """
    State:
      * Anhebung

    Controls:
      * Ventile der Häuser
    """

    def __init__(self, ctx: "Context", now_s: float, last_anhebung_prozent: float, last_valve_open_count: int):
        assert isinstance(now_s, float)
        assert isinstance(last_anhebung_prozent, float)
        assert isinstance(last_valve_open_count, int)
        self.ctx = ctx
        self.now_s = now_s
        self.last_anhebung_prozent = last_anhebung_prozent
        self.last_valve_open_count = last_valve_open_count
        self.actiontimer = ActionTimer()

    def influxdb_add_fields(self, fields: dict[str, float]) -> None:
        self.actiontimer.influxdb_add_fields(fields=fields)
        fields["anhebung_dezentral_prozent"] = self.last_anhebung_prozent

    def _process_leistung_ok_osolete(self, now_s: float, haeuser_ladung: HaeuserLadung) -> HauserValveVariante:
        """
        Tabelle Zeile 8
        """
        1 / 0
        # if not self.interval_anhebung.is_time_over(now_s=now_s, interval_s=self.INTERVAL_ANHEBUNG_S):
        #     raise PeriodNotOverException()
        evaluate = Evaluate(anhebung_prozent=self.last_anhebung_prozent, haeuser_ladung=haeuser_ladung)
        self.last_anhebung_prozent -= 1.0
        if self.last_anhebung_prozent < 0.0:
            self.last_anhebung_prozent = 0.0
        self.last_valve_open_count = evaluate.valve_open_count
        return evaluate.hvv

    def update_valves(self) -> None:
        evaluate = Evaluate(
            anhebung_prozent=self.last_anhebung_prozent,
            haeuser_ladung=self.ctx.hsm_zentral.get_hauser_ladung(),
        )
        self.ctx.hsm_zentral.update_hvv(hvv=evaluate.hvv)

    def anheben_plus_ein_haus(self, ctx: "Context", now_s: float) -> None:
        if not self.actiontimer.is_over_and_cancel():
            return
        if self.last_anhebung_prozent >= 100.0:
            return
        hvv = self._find_anhebung_plus_ein_haus(haeuser_ladung=ctx.hsm_zentral.get_hauser_ladung(), anhebung_prozent=self.last_anhebung_prozent)
        self.last_anhebung_prozent = hvv.anhebung_prozent
        self.actiontimer.action = AnhebungAction.HAUS_PLUS

    def anheben_minus_ein_haus(self, ctx: "Context", now_s: float) -> None:
        if not self.actiontimer.is_over_and_cancel:
            return
        if self.last_anhebung_prozent <= 0.0:
            return
        hvv = self._find_anhebung_minus_ein_haus(haeuser_ladung=ctx.hsm_zentral.get_hauser_ladung(), anhebung_prozent=self.last_anhebung_prozent)
        self.last_anhebung_prozent = hvv.anhebung_prozent
        self.actiontimer.action = AnhebungAction.HAUS_MINUS

    def _find_anhebung_plus_ein_haus(self, haeuser_ladung: HaeuserLadung, anhebung_prozent: float) -> HauserValveVariante:
        while True:
            if anhebung_prozent > 99.0:
                anhebung_prozent = 100.0

            evaluate = Evaluate(
                anhebung_prozent=anhebung_prozent,
                haeuser_ladung=haeuser_ladung,
            )

            if anhebung_prozent > 99.0:
                return evaluate.hvv
            if len(evaluate.hvv.haeuser_valve_to_open) > 0:
                return evaluate.hvv

            anhebung_prozent += 1.0

    def _find_anhebung_minus_ein_haus(self, haeuser_ladung: HaeuserLadung, anhebung_prozent: float) -> HauserValveVariante:
        while True:
            if anhebung_prozent < 1.0:
                anhebung_prozent = 0.0

            evaluate = Evaluate(
                anhebung_prozent=float(anhebung_prozent),
                haeuser_ladung=haeuser_ladung,
            )

            if anhebung_prozent < 1.0:
                return evaluate.hvv
            if len(evaluate.hvv.haeuser_valve_to_close) > 0:
                return evaluate.hvv

            anhebung_prozent -= 1.0
