import logging

from zentral.controller_mischventil import ControllerMischventil
from zentral.util_modbus_wrapper import ModbusWrapper

logger = logging.getLogger(__name__)


class Dac:
    DAC_ADDRESS = 0

    def __init__(self, modbus: "ModbusWrapper", modbus_address: int):
        assert isinstance(modbus, ModbusWrapper)
        self._modbus = modbus
        self._modbus_address = modbus_address
        self._modbus_label = f"Dac(modbus={self._modbus_address})"

    async def set_dac_100(self, output_100: float) -> None:
        output_V = ControllerMischventil.calculate_valve_V(stellwert_100=output_100)
        await self.set_dac(output_V=output_V)

    async def set_dac(self, output_V: float) -> None:
        outputs_mV = 8 * [int(1000 * output_V)]

        await self._modbus.write_registers(
            slave=self._modbus_address,
            slave_label=self._modbus_label,
            address=self.DAC_ADDRESS,
            values=outputs_mV,
        )

        logger.debug("set_dac")
