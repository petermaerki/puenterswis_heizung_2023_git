import dataclasses
import logging
import time
import typing

from hsm import hsm  # type: ignore[import]

from zentral.controller_base import ControllerMischventilABC
from zentral.controller_master import ControllerMaster
from zentral.controller_master_none import ControllerMasterNone
from zentral.controller_master_valveopen import ControllerMasterValveOpenIterator
from zentral.controller_mischventil import ControllerMischventil
from zentral.controller_mischventil_simple import ControllerMischventilNone
from zentral.hsm_zentral_signal import SignalDrehschalter, SignalError, SignalHardwaretestBegin, SignalHardwaretestEnd, SignalZentralBase
from zentral.util_controller_haus_ladung import HaeuserLadung
from zentral.util_logger import HsmLoggingLogger
from zentral.util_modbus_mischventil import MischventilRegisters
from zentral.util_modbus_oekofen import OekofenRegisters
from zentral.util_modbus_pcb_dezentral_heizzentrale import MissingModbusDataException
from zentral.util_persistence_mischventil import PersistenceMischventil
from zentral.util_scenarios import SCENARIOS, ScenarioMasterValveOpenIterator, ScenarioOverwriteMischventil, ScenarioOverwriteRelais0Automatik, ScenarioOverwriteRelais6PumpeGesperrt

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)

STATE_ERROR_RECOVER_S = 60.0
"""
In 'state_error':
After x s of absense of an 'SignalError', we will initialize again.
"""


_UPTIME_MODBUS_SILENT_S = 20.0


@dataclasses.dataclass
class Relais:
    relais_0_mischventil_automatik = False
    relais_1_elektro_notheizung = False
    relais_2_brenner1_sperren = True
    relais_3_brenner1_anforderung = False
    """
    relais_3_waermeanforderung_beide
    """
    relais_4_brenner2_sperren = True
    relais_5_brenner2_anforderung = False
    """
    relais_5_keine_funktion
    """
    relais_6_pumpe_gesperrt = False
    relais_7_automatik = False

    @property
    def relais_6_pumpe_gesperrt_overwrite(self) -> tuple[bool, bool]:
        """
        Same as 'self.relais_6_pumpe_gesperrt' but
        may be overwritten by 'ScenarioOverwriteRelais6PumpeEin'.
        return overwrite, value
        """
        sc = SCENARIOS.find(ScenarioOverwriteRelais6PumpeGesperrt)
        if sc is not None:
            return True, sc.pumpe_gesperrt
        return False, self.relais_6_pumpe_gesperrt

    @property
    def relais_0_mischventil_automatik_overwrite(self) -> tuple[bool, bool]:
        """
        Same as 'self.relais_0_mischventil_automatik' but
        may be overwritten by 'ScenarioOverwriteRelais0Automatik'.
        return overwrite, value
        """
        sc = SCENARIOS.find(ScenarioOverwriteRelais0Automatik)
        if sc is not None:
            return True, sc.automatik
        return False, self.relais_0_mischventil_automatik


class HsmZentral(hsm.HsmMixin):
    """ """

    def __init__(self, ctx: "Context"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self.ctx = ctx
        self.add_logger(HsmLoggingLogger("HsmZentral"))
        self.relais = Relais()
        # ControllerMischventil.calculate_valve_100(stellwert_V=0.0)
        self.mischventil_stellwert_100: float = PersistenceMischventil.read(stellwert_100_default=50.0)
        self._programm_start_s = time.monotonic()
        self.controller_mischventil: ControllerMischventilABC = ControllerMischventilNone(now_s=self._programm_start_s)
        self.controller_master: ControllerMaster
        self._set_controller_master_none()
        self.grundzustand_manuell()
        self.modbus_mischventil_registers: MischventilRegisters | None = None
        self.modbus_oekofen_registers: OekofenRegisters | None = None
        """
        None: If not modbus communication!
        """
        self._state_error_last_error_s: float = 0.0
        self.max_verbrauch_avg_W: float | None = None

    @property
    def uptime_s(self) -> float:
        return time.monotonic() - self._programm_start_s

    def is_drehschalterauto_regeln(self) -> bool:
        return self.is_state(self.state_ok_drehschalterauto)

    def is_initializing(self) -> bool:
        return self.is_state(self.state_initializing)

    def is_error_or_drehschaltermanuell(self) -> bool:
        if self.is_state(self.state_error):
            return True
        return self.is_state(self.state_ok_drehschaltermanuell)

    @property
    def haeuser_all_valves_closed(self) -> bool:
        """
        Return True: If a least one Haus requires energy (valve is open)
        """
        for haus in self.ctx.config_etappe.haeuser:
            modbus_iregs_all = haus.status_haus.hsm_dezentral.modbus_iregs_all
            if modbus_iregs_all is None:
                continue
            if modbus_iregs_all.relais_gpio.relais_valve_open:
                return False
        return True

    @property
    def is_haeuser_ladung_emergency(self) -> bool:
        v = self.haeuser_ladung_minimum_prozent
        if v is None:
            return False
        return v < 0.0

    def update_max_verbrauch_avg_W(self) -> None:
        self.max_verbrauch_avg_W = 0.0
        for haus in self.ctx.config_etappe.haeuser:
            verbrauch_avg_W = haus.status_haus.hsm_dezentral.verbrauch.verbrauch_avg_W
            assert verbrauch_avg_W is not None
            self.max_verbrauch_avg_W = max(self.max_verbrauch_avg_W, verbrauch_avg_W)

    @property
    def tuple_haeuser_ladung_minimum_prozent(self) -> tuple[float | None, float | None]:
        """
        Return (min, avg)

        Bestimmt die tiefste Ladung aller Häuser.
        Häuser, die über modbus NICHT erreichbar sind, werden ignoriert.
        return None: Falls keine Modbusdaten des Aussenfühlers bekannt.
        """
        try:
            temperatur_aussen_C = self.ctx.modbus_communication.pcbs_dezentral_heizzentrale.TaussenU_C
        except MissingModbusDataException:
            return None, None

        list_prozent: list[float] = []
        for haus in self.ctx.config_etappe.haeuser:
            modbus_iregs_all = haus.status_haus.hsm_dezentral.modbus_iregs_all
            if modbus_iregs_all is None:
                continue
            ladung_minimum = modbus_iregs_all.ladung_minimum(temperatur_aussen_C=temperatur_aussen_C)
            if ladung_minimum is None:
                continue
            list_prozent.append(ladung_minimum.ladung_prozent)

        if len(list_prozent) == 0:
            return None, None

        return min(list_prozent), sum(list_prozent) / len(list_prozent)

    @property
    def haeuser_ladung_minimum_prozent(self) -> float | None:
        """
        Bestimmt die durchschnittliche Ladung aller Häuser.
        """
        minimum, _avg = self.tuple_haeuser_ladung_minimum_prozent
        return minimum

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
            return True, sc.stellwert_100
        return False, self.mischventil_stellwert_100

    def _log_info_controller_master(self) -> None:
        logger.info(f"controller_master {self.controller_master.__class__.__name__}")

    def _set_controller_master_default(self) -> None:
        self._set_controller_master()

    def _set_controller_master_none(self) -> None:
        self.controller_master = ControllerMasterNone(ctx=self.ctx, now_s=time.monotonic())
        self._log_info_controller_master()

    def _set_controller_master(self) -> None:
        self.controller_master = ControllerMaster(ctx=self.ctx, now_s=time.monotonic())
        self._log_info_controller_master()

    def set_controller_master_valve_open_iterator(self, scenario: ScenarioMasterValveOpenIterator) -> None:
        assert isinstance(scenario, ScenarioMasterValveOpenIterator)
        self.controller_master = ControllerMasterValveOpenIterator(ctx=self.ctx, now_s=time.monotonic(), scenario=scenario)
        self._log_info_controller_master()

    @property
    def is_controller_master_valve_iterator(self) -> bool:
        return isinstance(self.controller_master, ControllerMasterValveOpenIterator)

    async def controller_process(self, ctx: "Context") -> None:
        if self.controller_master.done():
            self._set_controller_master_default()

        if self.is_state(self.state_hardwaretest):
            return

        self.controller_master.process(now_s=time.monotonic())

        try:
            self.controller_mischventil.process(ctx=ctx, now_s=time.monotonic())
        except MissingModbusDataException as e:
            if self.uptime_s > _UPTIME_MODBUS_SILENT_S:
                raise hsm.StateChangeException(self.state_error, why=f"{e!r}!")
            logger.warning(f"uptime={self.uptime_s:0.1f}s < _UPTIME_MODBUS_SILENT_S: {e!r}")

    def get_haeuser_ladung(self) -> HaeuserLadung:
        haeuser_ladung = HaeuserLadung()

        for haus in self.ctx.config_etappe.haeuser:
            haus_ladung = haus.status_haus.hsm_dezentral.haus_ladung
            if haus_ladung is None:
                continue
            haeuser_ladung.append(haus_ladung)

        return haeuser_ladung

    def grundzustand_manuell(self) -> None:
        now_s = time.monotonic()
        self.controller_mischventil = ControllerMischventilNone(now_s=now_s)
        self.controller_master = ControllerMasterNone(ctx=self.ctx, now_s=now_s)
        self.relais.relais_0_mischventil_automatik = False
        self.relais.relais_6_pumpe_gesperrt = True
        self.relais.relais_7_automatik = False

        for haus in self.ctx.config_etappe.haeuser:
            haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = False

    def _drehschalter_switch_state(self) -> typing.NoReturn:
        """
        Je nachdem wie der Drehschalter gestellt ist, muss in
        state_ok_drehschaltermanuell / state_ok_drehschalterauto
        gewechselt werden
        """
        if self.ctx.modbus_communication.drehschalter.is_manuell:
            raise hsm.StateChangeException(self.state_ok_drehschaltermanuell)
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

    def entry_ok(self, signal: SignalZentralBase):
        self.grundzustand_manuell()

    @hsm.value(3)
    def state_ok(self, signal: SignalZentralBase):
        """ """
        self._handle_signal(signal=signal)
        raise hsm.DontChangeStateException()

    @hsm.value(4)
    @hsm.init_state
    def state_ok_drehschaltermanuell(self, signal: SignalZentralBase):
        """ """
        if isinstance(signal, SignalDrehschalter):
            self._drehschalter_switch_state()

    def entry_ok_drehschalterauto(self, signal: SignalZentralBase):
        def controller_mischventil_factory() -> ControllerMischventilABC:
            return ControllerMischventil(time.monotonic())
            # return ControllerMischventilSimple(time.monotonic())

        self.controller_mischventil = controller_mischventil_factory()
        self._set_controller_master_default()

    @hsm.value(5)
    def state_ok_drehschalterauto(self, signal: SignalZentralBase):
        """ """
        if isinstance(signal, SignalDrehschalter):
            self._drehschalter_switch_state()
