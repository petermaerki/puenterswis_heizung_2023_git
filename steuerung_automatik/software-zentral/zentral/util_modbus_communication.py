import logging
import os
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
from zentral.util_modbus_gpio import Gpio
from zentral.util_modbus_dac import Dac
from zentral.util_scenarios import SCENARIOS, ScenarioMischventilModbusSystemExit

if typing.TYPE_CHECKING:
    from context import Context

logger = logging.getLogger(__name__)


class ModbusCommunication:
    def __init__(self, context: "Context"):
        self._context = context
        self._modbus = ModbusWrapper(context=context, modbus_client=self._get_modbus_client())

        self.m = Mischventil(self._modbus, MODBUS_ADDRESS_BELIMO)
        self.r = Gpio(self._modbus, MODBUS_ADDRESS_RELAIS)
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
            success = await modbus_haus.handle_haus(haus, self._context.influx)
            if success:
                await modbus_haus.handle_haus_gpio(haus)

            if False:
                r = InfluxRecords(haus=haus)
                r.add_fields(fields=haus.status_haus.get_influx_fields())
                await self._context.influx.write_records(records=r)

            # await modbus_haus.reboot_reset(haus=haus)

    async def _task_modbus(self):
        while True:
            await self.modbus_haueser_loop()

            if True:
                try:
                    await self.a.set_dac()
                except ModbusException:
                    pass

            if True:
                if SCENARIOS.remove_if_present(ScenarioMischventilModbusSystemExit):
                    raise SystemExit(f"ScenarioMischventilModbusSystemExit({self.m._modbus_label})")

                try:
                    relative_position = await self.m.relative_position
                    logger.debug(f"mischventil: {relative_position}")
                    absolute_power_kW = await self.m.absolute_power_kW
                    logger.debug(f"mischventil: {absolute_power_kW}")
                except ModbusException:
                    pass

            if True:
                try:
                    relais = self._context.hsm_zentral.relais
                    await self.r.set(
                        list_gpio=(
                            False,
                            False,
                            False,
                            False,
                            False,
                            False,
                            False,
                            relais.relais_7_automatik,
                        )
                    )
                except ModbusException:
                    pass

            # await asyncio.sleep(5.0)

    async def task_modbus(self):
        try:
            await self._task_modbus()
        except Exception as e:
            logger.warning(f"Terminating app: Unexpected {e!r}")
            await self._context.close_and_flush_influx()
            os._exit(43)
        except SystemExit as e:
            logger.warning(f"Terminating app: {e!r}")
            await self._context.close_and_flush_influx()
            os._exit(42)
