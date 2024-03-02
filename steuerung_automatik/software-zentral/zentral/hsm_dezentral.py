import time
import logging
from typing import TYPE_CHECKING

from hsm import hsm

from micropython.portable_modbus_registers import RelaisGpioBits
from zentral.util_constants_haus import SpPosition

from zentral.hsm_dezentral_signal import (
    SignalDezentralBase,
    SignalModbusSuccess,
    SignalModbusFailed,
)
from zentral.hsm_zentral_signal import SignalHardwaretestEnd, SignalHardwaretestBegin
from zentral.util_history2 import History2
from zentral.utils_logger import HsmLoggingLogger

if TYPE_CHECKING:
    from zentral.config_base import Haus
    from zentral.util_modbus_haus import ModbusIregsAll
    from zentral.context import Context

logger = logging.getLogger(__name__)


class HsmDezentral(hsm.HsmMixin):
    """ """

    def __init__(self, haus: "Haus"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self._haus = haus
        self._context: "Context" = None
        self.add_logger(HsmLoggingLogger(label=f"HsmHaus{haus.config_haus.nummer:02}"))
        self.modbus_history = History2()
        self.modbus_iregs_all: "ModbusIregsAll" = None
        self.relais_gpio = RelaisGpioBits(0)
        self._time_begin_s = 0.0

    @property
    def timer_duration_s(self) -> float:
        return time.monotonic() - self._time_begin_s

    def timer_start(self) -> None:
        self._time_begin_s = time.monotonic()

    def _handle_modbus(self, signal: SignalDezentralBase) -> bool:
        """
        returns True, if the signal was not handled
        """
        if isinstance(signal, SignalModbusSuccess):
            self.modbus_iregs_all = signal.modbus_iregs_all
            self._update_dezentral_led_blink()
            self.modbus_history.success()
            if self.modbus_iregs_all.relais_gpio.button_zentrale:
                raise hsm.StateChangeException(self.state_error_hardwaretest)
            if self.modbus_history.ok:
                raise hsm.StateChangeException(self.state_ok)
            return True

        if isinstance(signal, SignalModbusFailed):
            self.modbus_history.failed()
            if not self.modbus_history.ok:
                raise hsm.StateChangeException(self.state_error)
            return True

        return False

    def _update_dezentral_led_blink(self) -> None:
        assert self.modbus_iregs_all is not None

        def failure() -> bool:
            for p in SpPosition:
                pair_ds18 = self.modbus_iregs_all.pairs_ds18[p.ds18_pair_index]
                if pair_ds18.error_any:
                    return True
            return False

        self.relais_gpio.set_led_zentrale(on=False, blink=failure())

    @hsm.value(0)
    @hsm.init_state
    def state_initializeing(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()

    @hsm.value(1)
    def state_ok(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()

    @hsm.value(2)
    def state_error(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()

    @hsm.value(3)
    @hsm.init_state
    def state_error_lost(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()

    @hsm.value(4)
    def state_error_defect(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()

    def entry_error_hardwaretest(self, signal: SignalDezentralBase):
        self.timer_start()
        self.relais_gpio.set_led_zentrale(on=True, blink=False)
        self.relais_gpio.relais_valve_open = False
        self._context.hsm_zentral.dispatch(signal=SignalHardwaretestBegin(relais_7_automatik=False))

    def exit_error_hardwaretest(self, signal: SignalDezentralBase):
        self._context.hsm_zentral.dispatch(signal=SignalHardwaretestEnd())

    @hsm.value(5)
    def state_error_hardwaretest(self, signal: SignalDezentralBase):
        pass

    @hsm.value(6)
    @hsm.init_state
    def state_error_hardwaretest_01(self, signal: SignalDezentralBase):
        """
        erwartet: Zentral: Liest Modbus, gpio Taste ist gesetzt
        * Zentral: Eintrag influx
        * Zentral: Modbus Dezentral: 'LED ZENTRALE' ein
        * Zentral: Modbus Dezentral: Relais valve_open: aus
        * Zentral: Modbus Zentral: Relais 7 automatik: aus
        * Zentral: pause 10s
        """
        if self.timer_duration_s > 10.0:
            self._context.hsm_zentral.dispatch(signal=SignalHardwaretestBegin(relais_7_automatik=True))
            raise hsm.StateChangeException(self.state_error_hardwaretest_02)
        raise hsm.DontChangeStateException()

    @hsm.value(7)
    def state_error_hardwaretest_02(self, signal: SignalDezentralBase):
        """
        * Zentral: Modbus Zentral: Relais 7 automatik: an
        * erwartet: Dezentral: Zentrale schliesst blaues Ventil.
        * erwartet: Dezentral: Relais 'Automatik', roter Indikator.
        * Zentral: pause 10s
        """
        if self.timer_duration_s > 20.0:
            self.relais_gpio.relais_valve_open = True
            raise hsm.StateChangeException(self.state_error_hardwaretest_03)
        raise hsm.DontChangeStateException()

    @hsm.value(8)
    def state_error_hardwaretest_03(self, signal: SignalDezentralBase):
        """
        * Zentral: Modbus Dezentral: Relais valve_open: an
        * erwartet: Dezentral: Zentrale öffnet blaues Ventil.
        * erwartet: Dezentral: Relais 'Valve_open' und 'Automatik' roter Indikator.
        * Zentral: pause 10s
        """
        if self.timer_duration_s > 30.0:
            raise hsm.StateChangeException(self.state_ok)
        raise hsm.DontChangeStateException()
