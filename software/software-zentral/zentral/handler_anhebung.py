import logging

from zentral.util_action import ActionBaseEnum, ActionTimer
from zentral.util_controller_haus_ladung import HaeuserLadung
from zentral.util_controller_verbrauch_schaltschwelle import Evaluate, HauserValveVariante

logger = logging.getLogger(__name__)


class AnhebungAction(ActionBaseEnum):
    """
    anhebung wird aktualisiert alle INTERVAL_ANHEBUNG_S.
    """

    HAUS_PLUS = 12
    HAUS_MINUS = 12


class HandlerAnhebung:
    """
    State:
      * Anhebung

    Controls:
      * Ventile der Häuser
    """

    def __init__(self, now_s: float, last_anhebung_prozent: float, last_valve_open_count: int):
        assert isinstance(now_s, float)
        assert isinstance(last_anhebung_prozent, float)
        assert isinstance(last_valve_open_count, int)
        self.now_s = now_s
        self.last_anhebung_prozent = last_anhebung_prozent
        self.last_valve_open_count = last_valve_open_count
        self.actiontimer = ActionTimer()

    def influxdb_add_fields(self, fields: dict[str, float]) -> None:
        self.actiontimer.influxdb_add_fields(fields=fields)
        fields["anhebung_dezentral_prozent"] = self.last_anhebung_prozent

    def calculate_hvv(self, haeuser_ladung: HaeuserLadung) -> HauserValveVariante:
        evaluate = Evaluate(
            anhebung_prozent=self.last_anhebung_prozent,
            haeuser_ladung=haeuser_ladung,
        )
        return evaluate.hvv

    def anheben_plus_ein_haus(self, now_s: float, haeuser_ladung: HaeuserLadung) -> HauserValveVariante | None:
        if not self.actiontimer.is_over_and_cancel():
            return None
        if self.last_anhebung_prozent >= 100.0:
            return None
        hvv = self._find_anhebung_plus_ein_haus(haeuser_ladung=haeuser_ladung, anhebung_prozent=self.last_anhebung_prozent)
        self.last_anhebung_prozent = hvv.anhebung_prozent
        self.actiontimer.action = AnhebungAction.HAUS_PLUS
        return hvv

    def anheben_minus_ein_haus(self, now_s: float, haeuser_ladung: HaeuserLadung) -> HauserValveVariante | None:
        if not self.actiontimer.is_over_and_cancel():
            return None
        if self.last_anhebung_prozent <= 0.0:
            return None
        hvv = self._find_anhebung_minus_ein_haus(haeuser_ladung=haeuser_ladung, anhebung_prozent=self.last_anhebung_prozent)
        self.last_anhebung_prozent = hvv.anhebung_prozent
        self.actiontimer.action = AnhebungAction.HAUS_MINUS
        return hvv

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
