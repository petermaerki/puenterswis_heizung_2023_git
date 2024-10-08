import logging

from zentral.util_action import ActionBaseEnum, ActionTimer
from zentral.util_controller_haus_ladung import HaeuserLadung
from zentral.util_controller_verbrauch_schaltschwelle import Evaluate, HauserValveVariante

logger = logging.getLogger(__name__)


class AnhebungAction(ActionBaseEnum):
    """
    anhebung wird aktualisiert alle INTERVAL_ANHEBUNG_S.
    """

    HAUS_PLUS = 5
    HAUS_MINUS = 5


class HandlerAnhebung:
    """
    State:
      * Anhebung

    Controls:
      * Ventile der Häuser
    """

    def __init__(self, now_s: float, last_hvv: HauserValveVariante):
        assert isinstance(now_s, float)
        assert isinstance(last_hvv, HauserValveVariante)
        self.now_s = now_s
        self.last_hvv = last_hvv
        self.actiontimer = ActionTimer()
        self.mock_solltemperatur_Tfv_C: float | None = None

    @property
    def solltemperatur_Tfv_C(self) -> float:
        if self.mock_solltemperatur_Tfv_C is not None:
            return self.mock_solltemperatur_Tfv_C
        if self.last_hvv.legionellen_kill_in_progress:
            return 75.0
        return 68.0

    def influxdb_add_fields(self, fields: dict[str, float]) -> None:
        self.actiontimer.influxdb_add_fields(fields=fields)
        fields["anhebung_dezentral_prozent"] = self.last_hvv.anhebung_prozent

    def update_last_hvv(self, haeuser_ladung: HaeuserLadung) -> HauserValveVariante:
        evaluate = Evaluate(
            anhebung_prozent=self.last_hvv.anhebung_prozent,
            haeuser_ladung=haeuser_ladung,
        )
        self.last_hvv = evaluate.hvv
        return self.last_hvv

    def anheben_plus_ein_haus(self, now_s: float, haeuser_ladung: HaeuserLadung) -> HauserValveVariante | None:
        if not self.actiontimer.is_over_and_cancel():
            return None
        if self.last_hvv.anhebung_prozent >= 100.0:
            return None
        hvv = self._find_anhebung_plus_ein_haus(haeuser_ladung=haeuser_ladung, anhebung_prozent=self.last_hvv.anhebung_prozent)
        self.last_hvv = hvv
        self.actiontimer.action = AnhebungAction.HAUS_PLUS
        return hvv

    def anheben_minus_ein_haus(self, now_s: float, haeuser_ladung: HaeuserLadung) -> HauserValveVariante | None:
        if not self.actiontimer.is_over_and_cancel():
            return None
        if self.last_hvv.anhebung_prozent <= 0.0:
            return None
        hvv = self._find_anhebung_minus_ein_haus(haeuser_ladung=haeuser_ladung, anhebung_prozent=self.last_hvv.anhebung_prozent)
        self.last_hvv = hvv
        self.actiontimer.action = AnhebungAction.HAUS_MINUS
        return hvv

    def _find_anhebung_plus_ein_haus(self, haeuser_ladung: HaeuserLadung, anhebung_prozent: float) -> HauserValveVariante:
        assert isinstance(haeuser_ladung, HaeuserLadung)
        assert isinstance(anhebung_prozent, float)

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
        assert isinstance(haeuser_ladung, HaeuserLadung)
        assert isinstance(anhebung_prozent, float)

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
