import logging
import time
import typing

from zentral.controller_base import ControllerMischventilABC
from zentral.controller_mischventil_simple import ControllerMischventilSimple
from zentral.util_scenarios import SCENARIOS, ScenarioZentralSolltemperatur

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class Credit:
    """
    Falls der Kredit zu klein ist, wird der gain ('faktor') reduziert um
    die Schwingung zu verhindern.
    """

    _GRENZE_GAIN_REDUKTION_PROZENT = 50.0
    """
    ist der actuation_credit_prozent kleiner als dieser Wert, so wird der gain reduziert
    """
    assert 10.0 < _GRENZE_GAIN_REDUKTION_PROZENT <= 100.0

    def __init__(self, now_s: float):
        self.time_last_credit_s = now_s
        self.mischventil_actuation_credit_100 = 100.0
        """
        0.0 .. 100.0
        """
        self.last_Tfr_C = 0.0
        self.last_Tfv_soll_C = 0.0
        self.last_Tsz4_C = 0.0

    def add_mischventil_credit(self, credit: float) -> None:
        self.mischventil_actuation_credit_100 += credit
        self.mischventil_actuation_credit_100 = min(100.0, max(self.mischventil_actuation_credit_100, 0.0))

    @property
    def faktor(self) -> float:
        return min(self.mischventil_actuation_credit_100 / self._GRENZE_GAIN_REDUKTION_PROZENT, 1.0)

    def update_credit(
        self,
        now_s: float,
        Tfr_C: float,
        Tfv_soll_C: float,
        Tsz4_C: float,
    ) -> None:
        duration_s = now_s - self.time_last_credit_s
        self.time_last_credit_s = now_s

        if abs(Tsz4_C - self.last_Tsz4_C) > 2.0:
            # die Bedingungen haben geaendert, das Mischventil muss reagieren
            self.last_Tsz4_C = Tsz4_C
            self.add_mischventil_credit(5.0)

        if abs(Tfr_C - self.last_Tfr_C) > 2.0:
            # die Bedingungen haben geaendert, das Mischventil muss reagieren
            self.last_Tfr_C = Tfr_C
            self.add_mischventil_credit(5.0)

        if abs(Tfv_soll_C - self.last_Tfv_soll_C) > 2.0:
            # die Bedingungen haben geaendert, das Mischventil muss reagieren
            self.last_Tfv_soll_C = Tfv_soll_C
            self.add_mischventil_credit(5.0)

        self.add_mischventil_credit(duration_s / 60.0 * 0.2)


class PumpeAnlaufzeitMischventil:
    """
    Wenn die Pumpe anläuft, dauert es 120s bis das System stabil
    ist und mit Regeln begonnen werden kann.
    """

    _WARTEZEIT_NACH_PUMPE_EIN_s = 120.0
    """
    Siehe 20240914a_messung_totzeit.ods / log
    """

    def __init__(self):
        self.pumpe_start_s: float = 0.0
        self.last_pumpe_ein = False

    def pumpe(self, now_s: float, ein: bool) -> None:
        # Log if pumpe changes
        def ein_aus(v: bool) -> str:
            return "ein" if v else "aus"

        if self.last_pumpe_ein != ein:
            logger.debug(f"pumpe {ein_aus(self.last_pumpe_ein)} -> {ein_aus(ein)}")

        if (not self.last_pumpe_ein) and ein:
            # Flanke von Pumpe aus -> ein.
            self.pumpe_start_s = now_s

        self.last_pumpe_ein = ein

    def pumpe_und_stabil(self, now_s: float) -> bool:
        """
        Return True, falls geregelt werden darf:
        * Pumpe läuft und stabil
        """
        if not self.last_pumpe_ein:
            logger.debug(f"wait: not pumpe_und_stabil(last_pumpe_ein={self.last_pumpe_ein})")
            return False

        duration_s = now_s - self.pumpe_start_s
        to_wait_s = self._WARTEZEIT_NACH_PUMPE_EIN_s - duration_s
        if to_wait_s > 0.0:
            logger.debug(f"wait: not pumpe_und_stabil({to_wait_s:0.1f}s)")
            # Warten bis stabil
            return False
        # es darf geregelt werden
        return True


class NextControl:
    """
    Nach jedem Stellschritt warten wir, bis
    sich das thermische Gleichgewicht eingestellt hat.
    """

    _CONTROL_LOOP_TIME_INTERVAL_S = 120.0
    """
    Siehe 20240914a_messung_totzeit.ods / log
    """

    def __init__(self):
        self.next_s = 0.0

    def wait(self, now_s: float) -> bool:
        wait_s = now_s - self.next_s
        if wait_s < 0.0:
            logger.debug(f"wait: next_control.wait({-wait_s:0.1f}s)")
            return True
        if wait_s > self._CONTROL_LOOP_TIME_INTERVAL_S:
            # There was a very long pause (the pump was off).
            # Start a new interval.
            self.next_s = now_s + self._CONTROL_LOOP_TIME_INTERVAL_S
            return False
        # We are in a 20s interval
        self.next_s += self._CONTROL_LOOP_TIME_INTERVAL_S
        return False

    def add(self, add_s: float) -> None:
        assert isinstance(add_s, float)
        self.next_s += add_s


# TODO: Obsolete?
class ControllerMischventil(ControllerMischventilSimple):
    _STEILHEIT_MISCHVENTIL_PRO_V = 0.25
    """
    abgeschaetzt anhand Datenblatt, 20240506a_spannung_zu_winkel.ods"""
    STEILHEIT_MISCHVENTIL_C_PRO_V_MIN = 0.5
    """
    Minimalwert damit Regler nicht instabil bei kleinen Temperaturdifferenzen, typisch sind 6 C/V
    """
    _Tfv_TOLERANZ_C = 1.5
    """
    innerhalb dieser plus minus diese Toleranz erfolgt keine Korrektur mit dem Mischer
    """
    _STELLWERT_V_MIN = 2.0 - 0.5
    """ 
    unterhalb von 2V keine Aenderung gemaess Datenblatt, minus 0.5V als Reserve
    """
    _STELLWERT_V_MAX = 8.0 + 0.5
    """
    oberhalb von 8V keine Aenderung gemaess Datenblatt, plus 0.5V als Reserve
    """
    _VOLLE_BEWEGUNG_S = 90.0
    """ 
    gemaess Datenblatt 90 grad in 90 sekunden
    """
    _TOTAL_HUBSPANNUNG_V = 10.0 - 0.5
    _MOTOR_GESCHWINDIGKEIT_V_PRO_S = _TOTAL_HUBSPANNUNG_V / _VOLLE_BEWEGUNG_S
    _ZEIT_FUER_90_GRAD_WINKEL_S = 90
    _FAKTOR_STABILITAET_1 = 0.5
    """
    0..1, je kleiner, desto stabiler und langsamer
    """

    def __init__(self, now_s: float) -> None:
        super().__init__(now_s=now_s)
        # TODO(HandlerPumpe)
        # self.pumpe_anlaufzeit_mischventil = PumpeAnlaufzeitMischventil()
        self.next_control = NextControl()
        self.credit = Credit(now_s=now_s)
        self.last_stellwert_change_s = now_s
        self.last_stellwert_aenderung_V = 0.0

    def get_credit_100(self) -> float | None:
        """
        Return None: If the controller simple or None does not calculate the credit
        """
        return self.credit.mischventil_actuation_credit_100

    def _process_mischventil(self, ctx: "Context", now_s: float) -> None:
        pcbs = ctx.modbus_communication.pcbs_dezentral_heizzentrale
        last_stellwert_V = ctx.hsm_zentral.mischventil_stellwert_V

        self.credit.update_credit(
            now_s=now_s,
            Tfr_C=pcbs.Tfr_C,
            Tsz4_C=pcbs.Tsz4_C,
            Tfv_soll_C=ctx.hsm_zentral.controller_master.handler_last.solltemperatur_Tfv_C,
        )

        logger.debug(
            f"ctx.hsm_zentral.controller_master.handler_anhebung.solltemperatur_Tfv_C={ctx.hsm_zentral.controller_master.handler_last.solltemperatur_Tfv_C:0.1f}, Tfv_C={pcbs.Tfv_C:0.1f}, Tfr_C={pcbs.Tfr_C:0.1f}, Tsz4_C={pcbs.Tsz4_C:0.1f}"
        )

        duration_since_last_stellwert_change_s = now_s - self.last_stellwert_change_s
        abweichung_C = ctx.hsm_zentral.controller_master.handler_last.solltemperatur_Tfv_C - pcbs.Tfv_C
        if duration_since_last_stellwert_change_s < 5 * 60.0:
            if abs(abweichung_C) < self._Tfv_TOLERANZ_C:  # Genuegend genau, nichts machen
                logger.debug(f"abs(abweichung_C:{abweichung_C:0.2f}) < self._Tfv_TOLERANZ_C:{self._Tfv_TOLERANZ_C:0.2f}  # Genuegend genau, nichts machen")
                return

        temperaturdifferenz_eingang_mischventil_C = pcbs.Tsz4_C - pcbs.Tfr_C
        if temperaturdifferenz_eingang_mischventil_C < 1.0:
            # Fehlermeldung: "Tsz4 und Tfr sind fast gleich, Regeln Mischventil ausgesetzt."
            logger.debug(f"temperaturdifferenz_eingang_mischventil_C:{temperaturdifferenz_eingang_mischventil_C:0.2f} < 1.0 # Fehlermeldung: Tsz4 und Tfr sind fast gleich")
            return

        # steilheit_mischventil_C_pro_V: typisch z.B. 6C/V
        steilheit_mischventil_C_pro_V = temperaturdifferenz_eingang_mischventil_C * self._STEILHEIT_MISCHVENTIL_PRO_V
        steilheit_mischventil_C_pro_V = max(steilheit_mischventil_C_pro_V, self.STEILHEIT_MISCHVENTIL_C_PRO_V_MIN)

        stellwert_V = last_stellwert_V + abweichung_C / steilheit_mischventil_C_pro_V * self.credit.faktor * self._FAKTOR_STABILITAET_1
        stellwert_V = min(stellwert_V, self._STELLWERT_V_MAX)
        stellwert_V = max(stellwert_V, self._STELLWERT_V_MIN)

        stellwert_aenderung_V = stellwert_V - last_stellwert_V

        logger.debug(f"stellwert_aenderung_V: {stellwert_aenderung_V:0.3f}")

        # Abnutzung durch jede Stellwert Aenderung
        self.credit.add_mischventil_credit(-4.0 * abs(stellwert_aenderung_V))
        if stellwert_aenderung_V * self.last_stellwert_aenderung_V < 0.0:  # Vorzeichenwechsel
            if abs(stellwert_aenderung_V) > 0.1:
                # Vorzeichenwechsel bei Stellwert kann Oszillation bedeuten
                self.credit.add_mischventil_credit(-5.0)

        self.last_stellwert_aenderung_V = stellwert_aenderung_V

        # Hier wird der Stellwert gesetzt!
        ctx.hsm_zentral.mischventil_stellwert_100 = self.calculate_valve_100(stellwert_V=stellwert_V)
        self.last_stellwert_change_s = now_s
        logger.debug(f"ctx.hsm_zentral.mischventil_stellwert_100: {ctx.hsm_zentral.mischventil_stellwert_100:0.0f}%")

        # zusaetzlich warten bis Mischventil fertig bewegt hat
        self.next_control.add(abs(stellwert_aenderung_V) / self._MOTOR_GESCHWINDIGKEIT_V_PRO_S)

    def _pumpe_und_stabil(self, ctx: "Context", now_s: float) -> bool:
        """
        Note: The Mock will override this method!
        """
        return ctx.hsm_zentral.controller_master.handler_pumpe.pumpe_anlaufzeit_mischventil.pumpe_und_stabil(now_s=now_s)

    def process(self, ctx: "Context", now_s: float) -> None:
        scenario = SCENARIOS.find(ScenarioZentralSolltemperatur)
        if scenario is not None:
            SCENARIOS.remove(scenario)
            ctx.hsm_zentral.controller_master.handler_last.mock_solltemperatur_Tfv_C = scenario.solltemperature_Tfv_C

        ctx.hsm_zentral.relais.relais_0_mischventil_automatik = True
        # TODO(HandlerPumpe)
        # ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt = not self.get_pumpe_ein(ctx=ctx, now_s=now_s)
        ctx.hsm_zentral.relais.relais_7_automatik = True

        # TODO(HandlerPumpe)
        # self.pumpe_anlaufzeit_mischventil.pumpe(
        #     now_s=now_s,
        #     ein=not ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt,
        # )
        # TODO(HandlerPumpe)
        # if not self.pumpe_anlaufzeit_mischventil.pumpe_und_stabil(now_s=now_s):
        if not self._pumpe_und_stabil(ctx=ctx, now_s=now_s):
            return

        if self.next_control.wait(now_s=now_s):
            return

        self._process_mischventil(ctx=ctx, now_s=now_s)

    @staticmethod
    def calculate_valve_100(stellwert_V: float) -> float:
        """
        fuer Grafana:
        """
        valve_100 = 100.0 * (stellwert_V - ControllerMischventil._STELLWERT_V_MIN) / (ControllerMischventil._STELLWERT_V_MAX - ControllerMischventil._STELLWERT_V_MIN)
        # assert -1 < valve_100 <= 101
        return valve_100

    @staticmethod
    def calculate_valve_V(stellwert_100: float) -> float:
        """ """
        # assert -1 < stellwert_100 <= 101
        stellwert_V = stellwert_100 / 100.0 * (ControllerMischventil._STELLWERT_V_MAX - ControllerMischventil._STELLWERT_V_MIN) + ControllerMischventil._STELLWERT_V_MIN
        return stellwert_V


def controller_mischventil_factory() -> ControllerMischventilABC:
    if True:
        return ControllerMischventil(time.monotonic())
    return ControllerMischventilSimple(time.monotonic())
