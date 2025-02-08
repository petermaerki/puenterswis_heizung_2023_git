import logging
import time
from typing import TYPE_CHECKING

from hsm import hsm  # type: ignore[import]
from micropython.portable_modbus_registers import GpioBits

from zentral.constants import DEZENTRAL_VERSION_SW_FIXED_RELAIS_VALVE_OPEN
from zentral.hsm_dezentral_signal import SignalDezentralBase, SignalModbusFailed, SignalModbusSuccess
from zentral.hsm_zentral_signal import SignalHardwaretestBegin, SignalHardwaretestEnd
from zentral.util_constants_haus import SpPosition
from zentral.util_controller_haus_ladung import HausLadung
from zentral.util_history_modbus import HistoryModbus
from zentral.util_history_verbrauch_haus import VerbrauchHaus
from zentral.util_logger import HsmLoggingLogger
from zentral.util_mbus import MBusMeasurement
from zentral.util_modbus_gpio import ModbusIregsAll2
from zentral.util_persistence import Persistence
from zentral.util_sp_ladung_dezentral import LadungMinimum, SpTemperatur

if TYPE_CHECKING:
    from zentral.config_base import Haus
    from zentral.context import Context
    from zentral.hsm_zentral import HsmZentral

logger = logging.getLogger(__name__)


class HsmDezentral(hsm.HsmMixin):
    """ """

    def __init__(self, haus: "Haus"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self._haus = haus
        self._context: "Context" | None = None
        self.add_logger(HsmLoggingLogger(label=f"HsmHaus{haus.config_haus.nummer:02}"))
        self.modbus_history = HistoryModbus()
        self.modbus_iregs_all: ModbusIregsAll2 | None = None
        self.mbus_measurement: MBusMeasurement | None = None
        self.dezentral_gpio = GpioBits(0)
        """
        Why this variable? 
        Couldn't it be a property to self.modbus_iregs_all.relais_gpio.relais_valve_open ?

        There is some code:
          changed = hsm.dezentral_gpio.changed(hsm.modbus_iregs_all.relais_gpio)
        It looks like that we have to update 'self.dezentral_gpio' which then will update via modbus.
        """
        self._persistence = Persistence(tag=f"verbrauch_{haus.influx_tag}", period_s=60.0)
        self.verbrauch = VerbrauchHaus(persistence=self._persistence)
        self._time_begin_s = 0.0

    @property
    def haus(self) -> "Haus":
        return self._haus

    @property
    def context(self) -> "Context":
        assert self._context is not None
        return self._context

    @property
    def hsm_zentral(self) -> "HsmZentral":
        return self.context.hsm_zentral

    @property
    def timer_duration_s(self) -> float:
        return time.monotonic() - self._time_begin_s

    @property
    def sp_temperatur(self) -> SpTemperatur | None:
        modbus_iregs_all = self.modbus_iregs_all
        if modbus_iregs_all is None:
            return None
        return modbus_iregs_all.sp_temperatur

    @property
    def haus_ladung(self) -> HausLadung | None:
        sp_temperatur = self.sp_temperatur
        if sp_temperatur is None:
            return None

        max_verbrauch_avg_W = self.context.hsm_zentral.max_verbrauch_avg_W
        if max_verbrauch_avg_W is None:
            return None

        TaussenU_C = self.context.modbus_communication.pcbs_dezentral_heizzentrale.TaussenU_C
        ladung_minimum = LadungMinimum(
            sp_temperatur=sp_temperatur,
            temperatur_aussen_C=TaussenU_C,
        )

        assert self.verbrauch.verbrauch_avg_W is not None
        return HausLadung(
            haus=self.haus,
            verbrauch_avg_W=max(0.0, self.verbrauch.verbrauch_avg_W),
            max_verbrauch_avg_W=max_verbrauch_avg_W,
            ladung_prozent=ladung_minimum.ladung_prozent,
            valve_open=self.dezentral_gpio.relais_valve_open,
            next_legionellen_kill_s=self.next_legionellen_kill_s,
        )

    def timer_start(self) -> None:
        self._time_begin_s = time.monotonic()

    def save_persistence(self, why: str) -> None:
        self._persistence.save(force=True, why=why)

    @property
    def sp_energie_absolut_J(self) -> float | None:
        """
        return None, falls noch keine Modbus Daten empfangen wurden
        """
        if self.modbus_iregs_all is None:
            return None
        assert self.modbus_iregs_all.sp_temperatur is not None
        return self.modbus_iregs_all.sp_temperatur.energie_absolut_J

    @property
    def next_legionellen_kill_s(self) -> float:
        return self.context._persistence_legionellen.get_next_legionellen_kill_s(haus_influx_tag=self._haus.influx_tag)

    async def handle_history_verbrauch(self) -> None:
        await self.verbrauch.update_valve(hsm_dezentral=self, context=self.context)

    def _handle_modbus(self, signal: SignalDezentralBase) -> bool:
        """
        returns True, if the signal was not handled
        """
        if isinstance(signal, SignalModbusSuccess):
            # Has to be called periodically
            self._persistence.save()

            self.modbus_iregs_all = signal.modbus_iregs_all
            if self.modbus_iregs_all.version_sw < DEZENTRAL_VERSION_SW_FIXED_RELAIS_VALVE_OPEN:
                # In older software 'relais_valve_open' is always read as 0.
                # We override with the local value
                self.modbus_iregs_all.relais_gpio.relais_valve_open = self.dezentral_gpio.relais_valve_open
            self._update_dezentral_led_blink()
            self.modbus_history.success()
            if self.modbus_iregs_all.relais_gpio.button_zentrale:
                raise hsm.StateChangeException(self.state_hardwaretest, why="modbus_iregs_all.relais_gpio.button_zentrale")
            if self.any_ds18_fatal_error:
                raise hsm.StateChangeException(self.state_error, why="any_ds18_fatal_error")
            if self.modbus_history.ok:
                raise hsm.StateChangeException(self.state_ok, why="modbus_history")
            return True

        if isinstance(signal, SignalModbusFailed):
            self.modbus_history.failed()
            if not self.modbus_history.ok:
                raise hsm.StateChangeException(self.state_error, why="not self.modbus_history.ok")
            return True

        return False

    @property
    def any_ds18_fatal_error(self) -> bool:
        """
        Return True: If any of the ds18pairs (unten, mitte oben) has an error
        """
        if self.modbus_iregs_all is None:
            return False

        # print(self.modbus_iregs_all.debug_temperatureC_percent)
        for p in SpPosition:
            if p is SpPosition.UNUSED:
                continue
            pair_ds18 = self.modbus_iregs_all.pairs_ds18[p.ds18_pair_index]
            if pair_ds18.error_any:
                return True
        return False

    def _update_dezentral_led_blink(self) -> None:
        self.dezentral_gpio.set_led_zentrale(on=False, blink=self.any_ds18_fatal_error)

    @hsm.value(0)
    @hsm.init_state
    def state_initializing(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()

    def entry_ok(self, signal: SignalDezentralBase):
        if self.modbus_iregs_all is None:
            return
        logger.info(f"{self.haus.label}: version sw={self.modbus_iregs_all.version_sw_verbose} hw={self.modbus_iregs_all.version_hw_verbose}")

    @hsm.value(1)
    def state_ok(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()

    def exit_ok(self, signal: SignalDezentralBase):
        self.modbus_iregs_all = None

    def entry_error(self, signal: SignalDezentralBase):
        self.dezentral_gpio.relais_valve_open = True

    @hsm.value(2)
    def state_error(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()

    def entry_hardwaretest(self, signal: SignalDezentralBase):
        self.timer_start()
        self.hsm_zentral.dispatch(signal=SignalHardwaretestBegin(relais_7_automatik=False))
        self.dezentral_gpio.set_led_zentrale(on=True, blink=False)
        self.dezentral_gpio.relais_valve_open = False

    def exit_hardwaretest(self, signal: SignalDezentralBase):
        self.hsm_zentral.dispatch(signal=SignalHardwaretestEnd())

    @hsm.value(3)
    def state_hardwaretest(self, signal: SignalDezentralBase):
        pass

    @hsm.value(4)
    @hsm.init_state
    def state_hardwaretest_01(self, signal: SignalDezentralBase):
        """
        erwartet: Zentral: Liest Modbus, gpio Taste ist gesetzt
        * Zentral: Eintrag influx
        * Zentral: Modbus Dezentral: 'LED ZENTRALE' ein
        * Zentral: Modbus Dezentral: Relais valve_open: aus
        * Zentral: Modbus Zentral: Relais 7 automatik: aus
        * Zentral: pause 10s
        """
        if self.timer_duration_s > 40.0:
            self.hsm_zentral.dispatch(signal=SignalHardwaretestBegin(relais_7_automatik=True))
            raise hsm.StateChangeException(self.state_hardwaretest_02)
        raise hsm.DontChangeStateException()

    @hsm.value(5)
    def state_hardwaretest_02(self, signal: SignalDezentralBase):
        """
        * Zentral: Modbus Zentral: Relais 7 automatik: an
        * erwartet: Dezentral: Zentrale schliesst blaues Ventil.
        * erwartet: Dezentral: Relais 'Automatik', roter Indikator.
        * Zentral: pause 10s
        """
        if self.timer_duration_s > 40.0 + 40.0:
            self.dezentral_gpio.relais_valve_open = True
            raise hsm.StateChangeException(self.state_hardwaretest_03)
        raise hsm.DontChangeStateException()

    @hsm.value(6)
    def state_hardwaretest_03(self, signal: SignalDezentralBase):
        """
        * Zentral: Modbus Dezentral: Relais valve_open: an
        * erwartet: Dezentral: Zentrale öffnet blaues Ventil.
        * erwartet: Dezentral: Relais 'Valve_open' und 'Automatik' roter Indikator.
        * Zentral: pause 10s
        """
        if self.timer_duration_s > 40.0 + 40.0 + 40.0:
            raise hsm.StateChangeException(self.state_ok, why="Hardwaretest over")
        raise hsm.DontChangeStateException()
