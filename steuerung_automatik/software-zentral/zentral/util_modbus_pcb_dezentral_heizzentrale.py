import logging

from zentral.util_modbus_wrapper import ModbusWrapper

logger = logging.getLogger(__name__)


class PcbDezentralHeizzentrale:
    def __init__(self, modbus: "ModbusWrapper", modbus_address: int):
        assert isinstance(modbus, ModbusWrapper)
        self._modbus = modbus
        self._modbus_address = modbus_address
        self._modbus_label = f"PcbDezentralHeizzentrale(modbus={self._modbus_address})"

        self.Tszo_C: float = 65.0
        self.Tfr_C: float = 25.0
        self.Tfv_C: float = 25.0
