import dataclasses
import enum


import logging
import typing

from zentral.controller_haeuser_simple import ControllerHaeuserSimple
from zentral.util_controller_haus_ladung import HaeuserLadung
from zentral.util_controller_verbrauch_schaltschwelle import Evaluate, HauserValveVariante

if typing.TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class PeriodNotOverException(Exception):
    pass


class TemperaturZentral(enum.IntEnum):
    ZU_KALT = 0
    KALT = 1
    WARM = 2
    HEISS = 3


@dataclasses.dataclass(frozen=True, repr=True)
class ProcessParams:
    now_s: float
    anzahl_brenner_ein_1: int
    ladung_zentral_prozent: float
    haeuser_ladung: HaeuserLadung
    TPO_C: float


class ProcessInterval:
    def __init__(self, now_s: float):
        self.start_s = now_s
        self.last_time_over_s = -1e9

    def is_time_over(self, now_s: float, interval_s: float) -> bool:
        """
        Return True every 'PROCESS_INITERVAL_S'.
        """
        duration_time_over_last_s = now_s - self.last_time_over_s
        if duration_time_over_last_s >= interval_s:
            self.last_time_over_s = now_s
            return True
        return False


class ControllerHaeuser(ControllerHaeuserSimple):
    """
    Abbildung der Logik in sandbox_fuzzy/20240806a_diagramm_idee.ods

        Stellgrössen:
    * 'anhebung_prozent'
    * Brenner sperren
    * zentral WARM, KALT
    * Haeuser: valve_open
    """

    INTERVAL_ANHEBUNG_S = 60.0
    """
    anhebung wird aktualisiert alle INTERVAL_ANHEBUNG_S.
    """
    INTERVAL_HAUS_PLUS_S = 3 * 60.0
    INTERVAL_HAUS_MINUS_S = 10 * 60.0

    def __init__(self, now_s: float, last_anhebung_prozent: float, last_valve_open_count: int):
        assert isinstance(last_anhebung_prozent, float)
        assert isinstance(last_valve_open_count, int)
        self.last_anhebung_prozent = last_anhebung_prozent
        self.last_valve_open_count = last_valve_open_count

        super().__init__(now_s=now_s)

        self.debug_temperatur_zentral = TemperaturZentral.ZU_KALT
        self.interval_anhebung = ProcessInterval(now_s=now_s)
        self.interval_haus = ProcessInterval(now_s=now_s)

    def process(self, params: ProcessParams) -> HauserValveVariante:
        self.update_hauser_valve(params=params)

        hvv = self.process3(params=params)
        return hvv

    def process3(self, params: ProcessParams) -> HauserValveVariante:
        if params.anzahl_brenner_ein_1 >= 0:
            if params.ladung_zentral_prozent > 80.0:
                # Tabelle Zeile 4: Loescht bald
                self.debug_temperatur_zentral = TemperaturZentral.HEISS
                return self._process_1_2_loescht_bald(now_s=params.now_s, haeuser_ladung=params.haeuser_ladung)
            if params.ladung_zentral_prozent < -10.0:
                # Tabelle Zeile 6: brenner kommen nicht nach
                self.debug_temperatur_zentral = TemperaturZentral.KALT
                return self._process_1_2_brenner_kommen_nicht_nach(now_s=params.now_s, haeuser_ladung=params.haeuser_ladung)

        # Tabelle Zeile 8
        self.debug_temperatur_zentral = TemperaturZentral.WARM
        return self._process_leistung_ok(now_s=params.now_s, haeuser_ladung=params.haeuser_ladung)

    def _process_leistung_ok(self, now_s: float, haeuser_ladung: HaeuserLadung) -> HauserValveVariante:
        """
        Tabelle Zeile 8
        """
        if not self.interval_anhebung.is_time_over(now_s=now_s, interval_s=self.INTERVAL_ANHEBUNG_S):
            raise PeriodNotOverException()
        evaluate = Evaluate(anhebung_prozent=self.last_anhebung_prozent, haeuser_ladung=haeuser_ladung)
        self.last_anhebung_prozent -= 1.0
        if self.last_anhebung_prozent < 0.0:
            self.last_anhebung_prozent = 0.0
        self.last_valve_open_count = evaluate.valve_open_count
        return evaluate.hvv

    def _process_1_2_loescht_bald(self, now_s: float, haeuser_ladung: HaeuserLadung) -> HauserValveVariante:
        """
        # Tabelle Zeile 4: Loescht bald
        """
        if not self.interval_haus.is_time_over(now_s=now_s, interval_s=self.INTERVAL_HAUS_PLUS_S):
            raise PeriodNotOverException()

        hvv = self.find_anhebung_plus_ein_haus(haeuser_ladung=haeuser_ladung, anhebung_prozent=self.last_anhebung_prozent)
        self.last_anhebung_prozent = hvv.anhebung_prozent
        return hvv

    def _process_1_2_brenner_kommen_nicht_nach(self, now_s: float, haeuser_ladung: HaeuserLadung) -> HauserValveVariante:
        """
        Tabelle Zeile 6: brenner kommen nicht nach
        """
        if not self.interval_haus.is_time_over(now_s=now_s, interval_s=self.INTERVAL_HAUS_MINUS_S):
            raise PeriodNotOverException()

        hvv = self.find_anhebung_minus_ein_haus(haeuser_ladung=haeuser_ladung, anhebung_prozent=self.last_anhebung_prozent)
        self.last_anhebung_prozent = hvv.anhebung_prozent
        return hvv

    def find_anhebung_plus_ein_haus(self, haeuser_ladung: HaeuserLadung, anhebung_prozent: float) -> HauserValveVariante:
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

    def find_anhebung_minus_ein_haus(self, haeuser_ladung: HaeuserLadung, anhebung_prozent: float) -> HauserValveVariante:
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
