import logging
from typing import TYPE_CHECKING

from hsm import hsm

from zentral.utils_logger import HsmLogger

from zentral.hsm_dezentral_signal import (
    SignalDezentralBase,
    ModbusSuccess,
    ModbusFailed,
)
from zentral.util_history2 import History2

if TYPE_CHECKING:
    from zentral.config_base import Haus
    from zentral.util_modbus_haus import ModbusIregsAll

logger = logging.getLogger(__name__)


class HsmDezentral(hsm.HsmMixin):
    """ """

    def __init__(self, haus: "Haus"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self._haus = haus
        self.set_logger(HsmLogger(label=f"HsmHaus{haus.config_haus.nummer:02d}"))
        self.modbus_history = History2()
        self.modbus_iregs_all: "ModbusIregsAll" = None

    def _handle_modbus(self, signal: SignalDezentralBase) -> bool:
        """
        returns True, if the signal was not handled
        """
        if isinstance(signal, ModbusSuccess):
            self.modbus_iregs_all = signal.modbus_iregs_all
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
