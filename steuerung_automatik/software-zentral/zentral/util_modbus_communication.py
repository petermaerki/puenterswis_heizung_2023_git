import asyncio
import logging
import typing

from pymodbus import ModbusException
from pymodbus.client import AsyncModbusSerialClient
from zentral.util_influx import InfluxRecords

from zentral.util_modbus_wrapper import ModbusWrapper


from zentral.constants import (
    MODBUS_ADDRESS_BELIMO,
    MODBUS_ADDRESS_RELAIS,
    MODBUS_ADDRESS_ADC,
)

from zentral.util_modbus import get_modbus_client
from zentral.util_modbus_mischventil import Mischventil
from zentral.util_modbus_relais import Relais
from zentral.util_modbus_adc import Dac

if typing.TYPE_CHECKING:
    from context import Context

logger = logging.getLogger(__name__)


class ModbusCommunication:
    def __init__(self, context: "Context"):
        self._context = context
        self._modbus = ModbusWrapper(context=context, modbus_client=self._get_modbus_client())

        self.m = Mischventil(self._modbus, MODBUS_ADDRESS_BELIMO)
        self.r = Relais(self._modbus, MODBUS_ADDRESS_RELAIS)
        self.a = Dac(self._modbus, MODBUS_ADDRESS_ADC)

    def _get_modbus_client(self) -> AsyncModbusSerialClient:
        return get_modbus_client()

    async def connect(self):
        await self._modbus.connect()

    async def close(self):
        await self._modbus.close()

    async def modbus_haueser_loop(self) -> None:
        from zentral.util_modbus_haus import ModbusHaus

        for haus in self._context.config_etappe.haeuser:
            modbus_haus = ModbusHaus(modbus=self._modbus, haus=haus)
            await modbus_haus.handle_haus(haus, self._context.influx)
            await modbus_haus.handle_haus_relais(haus)

            r = InfluxRecords(haus=haus)
            r.add_fields(haus.status_haus.get_influx_fields())
            await self._context.influx.write_records(records=r)

            # await self.reboot_reset(haus=haus)

    async def task_modbus(self):
        while True:
            await self.modbus_haueser_loop()
            _haus = self._context.config_etappe.haeuser[0].status_haus
            # print(haus.modbus_history.text_history)
            await asyncio.sleep(0.5)
            # await asyncio.sleep(20.0)

            if True:
                await self.a.set_dac()
                await asyncio.sleep(0.5)

            if True:
                try:
                    relative_position = await self.m.relative_position
                    logger.debug(f"mischventil: {relative_position}")
                    absolute_power_kW = await self.m.absolute_power_kW
                    logger.debug(f"mischventil: {absolute_power_kW}")
                except ModbusException as exc:
                    logger.error(f"exception in mischventil {exc}")
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
                    logger.error(f"exception in relais {exc}")
                await asyncio.sleep(0.5)
