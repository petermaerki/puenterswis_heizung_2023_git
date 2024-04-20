import logging

from zentral.util_modbus_wrapper import ModbusWrapper

logger = logging.getLogger(__name__)


class Dac:
    ADC_ADDRESS = 0

    def __init__(self, modbus: "ModbusWrapper", modbus_address: int):
        assert isinstance(modbus, ModbusWrapper)
        self._modbus = modbus
        self._modbus_address = modbus_address
        self._modbus_label = f"Dac(modbus={self._modbus_address})"

    async def set_dac(self) -> None:
        output = [5000, 5000, 5000, 5000, 5000, 5000, 5000, 5000]

        await self._modbus.write_registers(
            slave=self._modbus_address,
            slave_label=self._modbus_label,
            address=self.ADC_ADDRESS,
            values=output,
        )

        logger.debug("set_adc")
