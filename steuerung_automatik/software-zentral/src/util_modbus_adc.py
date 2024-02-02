from pymodbus import ModbusException
from pymodbus.client import AsyncModbusSerialClient


class Dac:
    def __init__(self, modbus: AsyncModbusSerialClient, modbus_address: int):
        self._modbus = modbus
        self._modbus_address = modbus_address

    async def set_dac(self) -> None:
        try:
            adc_address = 0
            output = [5000, 5000, 5000, 5000, 5000, 5000, 5000, 5000]

            response = await self._modbus.write_registers(
                slave=self._modbus_address,
                address=adc_address,
                values=output,
            )
        except ModbusException as exc:
            print(f"ERROR: exception in pymodbus {exc}")
            return

        if response.isError():
            print("ERROR: pymodbus returned an error!")
            raise ModbusException("Hallo")

        print("set_adc")
