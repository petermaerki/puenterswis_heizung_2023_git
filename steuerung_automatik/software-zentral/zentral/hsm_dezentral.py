import logging

from hsm import hsm

from zentral.hsm_dezentral_signal import (
    SignalDezentralBase,
    ModbusSuccess,
    ModbusFailed,
)
from zentral.utils_logger import ZeroLogger
from zentral.util_history2 import History2

logger = logging.getLogger(__name__)


class HsmDezentral(hsm.HsmMixin):
    """ """

    def __init__(self):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self.set_logger(ZeroLogger(self))
        self.modbus_success_values: List[int] = None
        self.modbus_history = History2()

    def _handle_modbus(self, signal: SignalDezentralBase) -> bool:
        """
        returns True, if the signal was not handled
        """
        if isinstance(signal, ModbusSuccess):
            self.modbus_success_values = signal.values
            self.modbus_history.success()
            if self.modbus_history.ok:
                raise hsm.StateChangeException(self.state_ok)
            return True

        if isinstance(signal, ModbusFailed):
            self.modbus_history.failed()
            if not self.modbus_history.ok:
                raise hsm.StateChangeException(self.state_error)
            return True

        return False

    @hsm.init_state
    def state_initializeing(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()

    def state_ok(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()

    def state_error(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()

    @hsm.init_state
    def state_error_lost(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()

    def state_error_defect(self, signal: SignalDezentralBase):
        """ """
        self._handle_modbus(signal=signal)

        raise hsm.DontChangeStateException()
