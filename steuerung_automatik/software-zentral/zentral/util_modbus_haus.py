import os
import asyncio
import logging
from typing import TYPE_CHECKING

from pymodbus.exceptions import ModbusException, ConnectionException

from micropython.portable_modbus_registers import EnumModbusRegisters, IREGS_ALL

from zentral import hsm_dezentral_signal

from zentral.constants import TIMEOUT_AFTER_MODBUS_TRANSFER_S
from zentral.hsm_dezentral_signal import SignalModbusSuccess
from zentral.util_influx import Influx
from zentral.util_modbus_iregs_all import ModbusIregsAll
from zentral.util_modbus_wrapper import ModbusWrapper
from zentral.util_scenarios import (
    SCENARIOS,
    ScenarioHausSpTemperatureIncrease,
)

if TYPE_CHECKING:
    from zentral.config_base import Haus

logger = logging.getLogger(__name__)


class ModbusHaus:
    def __init__(self, modbus: ModbusWrapper, haus: "Haus"):
        assert isinstance(modbus, ModbusWrapper)
        self._modbus = modbus
        self._haus = haus

    async def handle_haus_gpio(self, haus: "Haus") -> None:
        hsm = haus.status_haus.hsm_dezentral

        if hsm.modbus_iregs_all is not None:
            if hsm.dezentral_gpio.changed(hsm.modbus_iregs_all.relais_gpio):
                return

        try:
            rsp = await self._modbus.write_registers(
                slave=haus.config_haus.modbus_server_id,
                address=EnumModbusRegisters.SETGET16BIT_GPIO,
                values=[hsm.dezentral_gpio.value],
            )

        except ModbusException as exc:
            logger.error(f"{haus.label}: {exc!r}")
            await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
            return

        return
        try:
            rsp = await self._modbus.read_holding_registers(
                slave=haus.config_haus.modbus_server_id,
                address=EnumModbusRegisters.SETGET16BIT_GPIO,
                count=1,
            )

        except ModbusException as exc:
            logger.error(f"{haus.label}: {exc!r}")
            haus.status_haus.hsm_dezentral.dispatch(hsm_dezentral_signal.SignalModbusFailed())
            await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
            return

        logger.debug(f"{haus.label}: SETGET16BIT_GPIO: {rsp.registers}")
        await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)

    async def handle_haus(self, haus: "Haus", grafana=Influx) -> bool:
        try:
            rsp = await self._modbus.read_input_registers(
                slave=haus.config_haus.modbus_server_id,
                address=EnumModbusRegisters.SETGET16BIT_ALL_SLOW,
                count=IREGS_ALL.register_count,
            )
        except ConnectionException as exc:
            logger.error(f"{haus.label}: {exc!r}")
            os._exit(42)
        except ModbusException as exc:
            logger.error(f"{haus.label}: {exc!r}")
            haus.status_haus.hsm_dezentral.dispatch(hsm_dezentral_signal.SignalModbusFailed())
            await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
            return False

        modbus_iregs_all = ModbusIregsAll(rsp.registers)

        for scenario in SCENARIOS.iter_by_class_haus(
            cls_scenario=ScenarioHausSpTemperatureIncrease,
            haus=self._haus,
        ):
            modbus_iregs_all.apply_scenario_temperature_increase(scenario)

        await grafana.send_modbus_iregs_all(haus, modbus_iregs_all)
        haus.status_haus.hsm_dezentral.dispatch(SignalModbusSuccess(modbus_iregs_all=modbus_iregs_all))
        logger.debug(f"{haus.label}: Iregsall: {rsp.registers}")
        await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
        return True

    async def reboot_reset(self, haus: "Haus") -> None:
        try:
            await self._modbus.write_coil(
                slave=haus.config_haus.modbus_server_id,
                address=EnumModbusRegisters.SETGET1BIT_REBOOT_WATCHDOG,
                value=True,
            )
        except ModbusException as exc:
            logger.error(f"{haus.label}: {exc!r}")
            haus.status_haus.hsm_dezentral.dispatch(hsm_dezentral_signal.SignalModbusFailed())
            await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
            return

        await asyncio.sleep(TIMEOUT_AFTER_MODBUS_TRANSFER_S)
