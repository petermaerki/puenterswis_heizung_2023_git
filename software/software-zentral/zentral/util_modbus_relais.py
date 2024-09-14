from pymodbus import ModbusException

from zentral.util_modbus_wrapper import ModbusWrapper


class ModbusRelais:
    COIL_ADDRESS = 0
    RELAIS_COUNT = 8

    def __init__(self, modbus: ModbusWrapper, modbus_address: int):
        assert isinstance(modbus, ModbusWrapper)
        self._modbus = modbus
        self._modbus_address = modbus_address
        self._modbus_label = f"Gpio(modbus={self._modbus_address})"

    async def set(self, list_gpio: tuple[bool]) -> None:
        assert isinstance(list_gpio, (list, tuple))
        assert len(list_gpio) == self.RELAIS_COUNT
        response = await self._modbus.write_coils(
            slave=self._modbus_address,
            slave_label=self._modbus_label,
            address=self.COIL_ADDRESS,
            values=list_gpio,
        )
        if response.isError():
            print("ERROR: pymodbus returned an error!")
            raise ModbusException("Hallo")
