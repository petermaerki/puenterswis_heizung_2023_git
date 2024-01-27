import asyncio
import typing

from pymodbus import ModbusException

if typing.TYPE_CHECKING:
    from modbus_software.context import Context

from modbus_software.constants import (
    MODBUS_ADDRESS_BELIMO,
    MODBUS_ADDRESS_RELAIS,
    MODBUS_ADDRESS_ADC,
)

from modbus_software.util_modbus import get_modbus_client
from modbus_software.util_modbus_mischventil import Mischventil
from modbus_software.util_modbus_relais import Relais
from modbus_software.util_modbus_adc import Dac


class ModbusCommunication:
    def __init__(self, context: "Context"):
        self._modbus = get_modbus_client()
        self._context = context

        self.m = Mischventil(self._modbus, MODBUS_ADDRESS_BELIMO)
        self.r = Relais(self._modbus, MODBUS_ADDRESS_RELAIS)
        self.a = Dac(self._modbus, MODBUS_ADDRESS_ADC)

    async def connect(self):
        await self._modbus.connect()

    async def close(self):
        self._modbus.close()

    async def modbus_haueser_loop(self) -> None:
        from util_modbus_haus import ModbusHaus

        for config_haus in self._context.config_bauabschnitt.haeuser:
            modbus_haus = ModbusHaus(modbus=self._modbus, config_haus=config_haus)
            await modbus_haus.handle_haus(config_haus)
            await modbus_haus.handle_haus_relais(config_haus)

            # await self.reboot_reset(haus=haus)

    async def task_modbus(self):
        while True:
            print("")
            await self.modbus_haueser_loop()
            haus = self._context.config_bauabschnitt.haeuser[0].status_haus
            # print(haus.modbus_history.text_history)
            await asyncio.sleep(0.5)
            # await asyncio.sleep(20.0)

            if True:
                await self.a.set_dac()
                await asyncio.sleep(0.5)

            if True:
                try:
                    relative_position = await self.m.relative_position
                    print(f"{relative_position}")
                    absolute_power_kW = await self.m.absolute_power_kW
                    print(f"{absolute_power_kW}")
                except ModbusException as exc:
                    print(f"ERROR: exception in mischventil {exc}")
                await asyncio.sleep(0.5)

            if True:
                try:
                    await self.r.set(
                        list_relays=(
                            True,
                            True,
                            False,
                            False,
                            False,
                            False,
                            False,
                            False,
                        )
                    )
                except ModbusException as exc:
                    print(f"ERROR: exception in relais {exc}")
                await asyncio.sleep(0.5)
