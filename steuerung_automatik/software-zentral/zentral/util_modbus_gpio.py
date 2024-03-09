# scripts/example/simple_rtu_client.py
import asyncio

from pymodbus import ModbusException
from zentral.constants import MODBUS_ADDRESS_RELAIS

from zentral.util_modbus_wrapper import ModbusWrapper


class Gpio:
    COIL_ADDRESS = 0
    RELAIS_COUNT = 8

    def __init__(self, modbus: ModbusWrapper, modbus_address: int):
        assert isinstance(modbus, ModbusWrapper)
        self._modbus = modbus
        self._modbus_address = modbus_address

    async def relais_set_obsolete(self):
        for coils in ([1, 0, 0, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0, 0, 1]):
            response = await self._modbus.write_coils(
                slave=MODBUS_ADDRESS_RELAIS,
                address=0,
                values=coils,
            )
            print(response)

            response = await self._modbus.read_coils(
                slave=MODBUS_ADDRESS_RELAIS,
                address=0,
                count=8,
            )
            print(response)
            await asyncio.sleep(0.5)

    async def set(self, list_gpio: tuple[bool]) -> None:
        assert isinstance(list_gpio, (list, tuple))
        assert len(list_gpio) == self.RELAIS_COUNT
        response = await self._modbus.write_coils(
            slave=self._modbus_address,
            address=self.COIL_ADDRESS,
            values=list_gpio,
        )
        if response.isError():
            print("ERROR: pymodbus returned an error!")
            raise ModbusException("Hallo")
