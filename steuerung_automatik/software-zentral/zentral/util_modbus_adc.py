from pymodbus import ModbusException

from zentral.util_modbus_wrapper import ModbusWrapper


class Dac:
    ADC_ADDRESS = 0

    def __init__(self, modbus: "ModbusWrapper", modbus_address: int):
        assert isinstance(modbus, ModbusWrapper)
        self._modbus = modbus
        self._modbus_address = modbus_address

    async def set_dac(self) -> None:
        try:
            output = [5000, 5000, 5000, 5000, 5000, 5000, 5000, 5000]

            response = await self._modbus.write_registers(
                slave=self._modbus_address,
                address=self.ADC_ADDRESS,
                values=output,
            )
        except ModbusException as exc:
            print(f"ERROR: exception in pymodbus {exc}")
            return

        if response.isError():
            print("ERROR: pymodbus returned an error!")
            raise ModbusException("Hallo")

        print("set_adc")
