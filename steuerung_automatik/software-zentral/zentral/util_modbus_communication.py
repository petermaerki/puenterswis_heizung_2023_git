import os
import logging
import typing

from pymodbus import ModbusException
from pymodbus.client import AsyncModbusSerialClient
from zentral.hsm_zentral_signal import SignalDrehschalter
from zentral.util_influx import InfluxRecords

from zentral.util_modbus_wrapper import ModbusWrapper


from zentral.constants import (
    MODBUS_ADDRESS_BELIMO,
    MODBUS_ADDRESS_RELAIS,
    MODBUS_ADDRESS_DAC,
)

from zentral.util_modbus import get_modbus_client
from zentral.util_modbus_mischventil import Mischventil
from zentral.util_modbus_gpio import Gpio
from zentral.util_modbus_dac import Dac
from zentral.util_scenarios import SCENARIOS, ScenarioMischventilModbusSystemExit, ScenarioZentralDrehschalterManuell

if typing.TYPE_CHECKING:
    from context import Context

logger = logging.getLogger(__name__)


class ModbusCommunication:
    def __init__(self, context: "Context"):
        self._context = context
        self._modbus = ModbusWrapper(context=context, modbus_client=self._get_modbus_client())

        self.m = Mischventil(self._modbus, MODBUS_ADDRESS_BELIMO)
        self.r = Gpio(self._modbus, MODBUS_ADDRESS_RELAIS)
        self.a = Dac(self._modbus, MODBUS_ADDRESS_DAC)

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
        class Drehschalter:
            """
            Drehschalter off is indicated by the waveshare-relais-module
            not beeing powered:
            There whill be 'no_response'.
            However, we wait for 10 consecutively 'no_response' to distinguish
            between flakyness and power off.
            We propagate a signal to hsm-zentral.
            """

            REQUIRED_NO_RESPONSES = 10

            def __init__(self, hsm_zentral: "Context"):
                self._hsm_zentral = hsm_zentral
                self._no_response_counter = 0

            def ok(self) -> None:
                self._no_response_counter = 0
                self._hsm_dispatch()

            def no_response(self) -> None:
                self._no_response_counter += 1
                self._hsm_dispatch()

            def _hsm_dispatch(self):
                manuell = self._no_response_counter > self.REQUIRED_NO_RESPONSES
                self._hsm_zentral.dispatch(SignalDrehschalter(manuell=manuell))

        drehschalter = Drehschalter(hsm_zentral=self._context.hsm_zentral)

        while True:
            if True:
                await self.modbus_haueser_loop()

            self._context.hsm_zentral.controller_process(ctx=self._context)

            if True:
                try:
                    await self.a.set_dac()
                except ModbusException as e:
                    logger.warning(f"Dac: {e}")

            if True:
                if SCENARIOS.remove_if_present(ScenarioMischventilModbusSystemExit):
                    raise SystemExit(f"ScenarioMischventilModbusSystemExit({self.m._modbus_label})")
                try:
                    if True:
                        all_registers = await self.m.all_registers
                        logger.debug(f"mischventil: {all_registers=}")
                    if False:
                        series = await self.m.series_3words
                        logger.info(f"mischventil: {series=}")
                    if False:
                        relative_position = await self.m.relative_position
                        logger.info(f"mischventil: {relative_position=}")
                    if False:
                        absolute_power_kW = await self.m.absolute_power_kW
                        logger.info(f"mischventil: {absolute_power_kW=}")

                    if False:
                        zentral_cooling_energie_J = await self.m.zentral_cooling_energie_J
                        logger.info(f"mischventil: {zentral_cooling_energie_J=}")
                except ModbusException as e:
                    logger.warning(f"Mischventil: {e}")

            if True:
                try:
                    if SCENARIOS.is_present(ScenarioZentralDrehschalterManuell):
                        raise ModbusException(ScenarioZentralDrehschalterManuell.__name__)

                    relais = self._context.hsm_zentral.relais
                    await self.r.set(
                        list_gpio=(
                            relais.relais_0_mischventil_automatik,
                            False,
                            False,
                            False,
                            False,
                            False,
                            not relais.relais_6_pumpe_ein,
                            relais.relais_7_automatik,
                        )
                    )
                    drehschalter.ok()
                except ModbusException as e:
                    drehschalter.no_response()
                    logger.warning(f"Relais: {e}")

            # await asyncio.sleep(5.0)

    async def task_modbus(self):
        await self._task_modbus()
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
