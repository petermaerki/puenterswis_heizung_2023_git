import dataclasses
import logging
import time
import typing

from hsm import hsm

from zentral.constants import WHILE_HARGASSNER
from zentral.controller_base import ControllerABC
from zentral.controller_mischventil import ControllerMischventil
from zentral.controller_simple import controller_factory
from zentral.hsm_zentral_signal import SignalDrehschalter, SignalError, SignalHardwaretestBegin, SignalHardwaretestEnd, SignalZentralBase
from zentral.util_logger import HsmLoggingLogger
from zentral.util_modbus_mischventil import MischventilRegisters
from zentral.util_modbus_oekofen import OekofenRegisters
from zentral.util_modbus_pcb_dezentral_heizzentrale import MissingModbusDataException
from zentral.util_scenarios import SCENARIOS, ScenarioOverwriteMischventil, ScenarioOverwriteRelais0Automatik, ScenarioOverwriteRelais6PumpeEin

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)

STATE_ERROR_RECOVER_S = 60.0
"""
In 'state_error':
After x s of absense of an 'SignalError', we will initialize again.
"""

INIT_STATE_DREHSCHALTERAUTO_REGELN = True
"""
True: state_ok_drehschalterauto_regeln
False: state_ok_drehschalterauto_manuell
"""

_UPTIME_MODBUS_SILENT_S = 20.0


@dataclasses.dataclass
class Relais:
    relais_0_mischventil_automatik = False

    relais_2_brenner1_sperren = False
    relais_3_waermeanforderung_beide = False
    relais_4_brenner2_sperren = False
    relais_5_keine_funktion = False

    relais_6_pumpe_ein = False
    """
    While HARGASSNER: Der Wert is invertiert!
    """
    relais_7_automatik = False

    @property
    def relais_6_pumpe_ein_overwrite(self) -> tuple[bool, bool]:
        """
        Same as 'self.relais_6_pumpe_ein' but
        may be overwritten by 'ScenarioOverwriteRelais6PumpeEin'.
        return overwrite, value
        """
        sc = SCENARIOS.find(ScenarioOverwriteRelais6PumpeEin)
        if sc is not None:
            sc.decrement()
            return True, sc.pumpe_ein
        return False, self.relais_6_pumpe_ein

    @property
    def relais_0_mischventil_automatik_overwrite(self) -> tuple[bool, bool]:
        """
        Same as 'self.relais_0_mischventil_automatik' but
        may be overwritten by 'ScenarioOverwriteRelais0Automatik'.
        return overwrite, value
        """
        sc = SCENARIOS.find(ScenarioOverwriteRelais0Automatik)
        if sc is not None:
            sc.decrement()
            return True, sc.automatik
        return False, self.relais_0_mischventil_automatik


class HsmZentral(hsm.HsmMixin):
    """ """

    def __init__(self, ctx: "Context"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self.ctx = ctx
        self.add_logger(HsmLoggingLogger("HsmZentral"))
        self.relais = Relais()
        self.mischventil_stellwert_100 = ControllerMischventil.calculate_valve_100(stellwert_V=0.0)
        self.solltemperatur_Tfv: float = 0.0
        self.controller: ControllerABC | None = None
        self.grundzustand_manuell()
        self.modbus_mischventil_registers: MischventilRegisters | None = None
        self.modbus_oekofen_registers: OekofenRegisters | None = None
        self._programm_start_s = time.monotonic()
        self._state_error_last_error_s: float = 0.0

    @property
    def uptime_s(self) -> float:
        return time.monotonic() - self._programm_start_s

    @property
    def mischventil_stellwert_V(self) -> float:
        return ControllerMischventil.calculate_valve_V(stellwert_100=self.mischventil_stellwert_100)

    @property
    def mischventil_stellwert_100_overwrite(self) -> tuple[bool, float]:
        """
        Same as 'self.mischventil_stellwert_100' but
        may be overwritten by 'ScenarioOverwriteMischventil'.
        return overwrite, value
        """
        sc = SCENARIOS.find(ScenarioOverwriteMischventil)
        if sc is not None:
            sc.decrement()
            return True, sc.stellwert_100
        return False, self.mischventil_stellwert_100

    def controller_process(self, ctx: "Context") -> None:
        if not self.is_state(self.state_hardwaretest):
            if self.controller is not None:
                try:
                    self.controller.process(ctx=ctx, now_s=time.monotonic())
                except MissingModbusDataException as e:
                    if self.uptime_s > _UPTIME_MODBUS_SILENT_S:
                        raise hsm.StateChangeException(self.state_error, why=f"{e!r}!")
                    logger.warning(f"uptime={self.uptime_s:0.1f}s < _UPTIME_MODBUS_SILENT_S: {e!r}")

    def grundzustand_manuell(self) -> None:
        self.controller = None
        self.relais.relais_0_mischventil_automatik = False
        self.relais.relais_6_pumpe_ein = True
        self.relais.relais_7_automatik = False

        for haus in self.ctx.config_etappe.haeuser:
            assert haus.status_haus is not None
            if WHILE_HARGASSNER:
                haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = True
            else:
                haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = False

    def _drehschalter_switch_state(self) -> typing.NoReturn:
        """
        Je nachdem wie der Drehschalter gestellt ist, muss in
        state_ok_drehschaltermanuell / state_ok_drehschalterauto
        gewechselt werden
        """
        if self.ctx.modbus_communication.drehschalter.is_manuell:
            raise hsm.StateChangeException(self.state_ok_drehschaltermanuell)
        else:
            raise hsm.StateChangeException(self.state_ok_drehschalterauto)

    def _handle_signal(self, signal: SignalZentralBase) -> None:
        if isinstance(signal, SignalHardwaretestBegin):
            raise hsm.StateChangeException(self.state_hardwaretest)
        if isinstance(signal, SignalError):
            self._state_error_last_error_s = time.monotonic()
            raise hsm.StateChangeException(self.state_error, why=signal.why)

    def entry_error(self, signal: SignalZentralBase):
        self.grundzustand_manuell()

    @hsm.value(0)
    def state_error(self, signal: SignalZentralBase):
        """ """
        self._handle_signal(signal=signal)

        def restart_if_errors_gone():
            timelapse_without_error_s = time.monotonic() - self._state_error_last_error_s
            assert timelapse_without_error_s >= 0.0
            if timelapse_without_error_s > STATE_ERROR_RECOVER_S:
                msg = f"No SignalError occured during {timelapse_without_error_s:0.0f}s. Exit the application, the service will restart it."
                raise SystemExit(msg)
                # raise hsm.StateChangeException(self.state_initializing, why=msg)

        restart_if_errors_gone()

        raise hsm.DontChangeStateException()

    @hsm.value(1)
    @hsm.init_state
    def state_initializing(self, signal: SignalZentralBase):
        """ """
        self._handle_signal(signal=signal)
        if isinstance(signal, SignalDrehschalter):
            self._drehschalter_switch_state()
        raise hsm.DontChangeStateException()

    def entry_hardwaretest(self, signal: SignalZentralBase):
        self.grundzustand_manuell()
        assert self.controller is None
        if isinstance(signal, SignalHardwaretestBegin):
            self.relais.relais_7_automatik = signal.relais_7_automatik

    @hsm.value(2)
    def state_hardwaretest(self, signal: SignalZentralBase):
        """ """
        if isinstance(signal, SignalHardwaretestBegin):
            self.relais.relais_7_automatik = signal.relais_7_automatik
        if isinstance(signal, SignalHardwaretestEnd):
            self._drehschalter_switch_state()
        raise hsm.DontChangeStateException()

    @hsm.value(3)
    def state_ok(self, signal: SignalZentralBase):
        """ """
        self._handle_signal(signal=signal)
        raise hsm.DontChangeStateException()

    def entry_ok_drehschaltermanuell(self, signal: SignalZentralBase):
        self.grundzustand_manuell()

    @hsm.value(4)
    @hsm.init_state
    def state_ok_drehschaltermanuell(self, signal: SignalZentralBase):
        """ """
        if isinstance(signal, SignalDrehschalter):
            self._drehschalter_switch_state()

    def entry_ok_drehschalterauto(self, signal: SignalZentralBase):
        self.controller = controller_factory()

    @hsm.value(5)
    def state_ok_drehschalterauto(self, signal: SignalZentralBase):
        """ """
        if isinstance(signal, SignalDrehschalter):
            self._drehschalter_switch_state()

    def entry_ok_drehschalterauto_manuell(self, signal: SignalZentralBase):
        self.grundzustand_manuell()

    @hsm.value(6)
    def state_ok_drehschalterauto_manuell(self, signal: SignalZentralBase):
        """ """
        pass

    @hsm.value(7)
    @hsm.init_state
    def state_ok_drehschalterauto_regeln(self, signal: SignalZentralBase):
        """ """
        pass
