import logging
from typing import TYPE_CHECKING

from pymodbus.exceptions import ModbusException

from micropython.portable_modbus_registers import EnumModbusRegisters, IREGS_ALL

from zentral import hsm_dezentral_signal

from zentral.hsm_dezentral_signal import SignalModbusSuccess
from zentral.util_influx import Influx
from zentral.util_modbus_gpio import ModbusIregsAll2
from zentral.util_modbus_wrapper import ModbusWrapper
from zentral.util_scenarios import (
    SCENARIOS,
    ScenarioHausSpTemperatureIncrease,
    ScenarioHausPicoRebootReset,
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
                slave_label=haus.label,
                address=EnumModbusRegisters.SETGET16BIT_GPIO,
                values=[hsm.dezentral_gpio.value],
            )

        except ModbusException:
            return

        return
        try:
            rsp = await self._modbus.read_holding_registers(
                slave=haus.config_haus.modbus_server_id,
                address=EnumModbusRegisters.SETGET16BIT_GPIO,
                count=1,
            )

        except ModbusException:
            haus.status_haus.hsm_dezentral.dispatch(hsm_dezentral_signal.SignalModbusFailed())
            return

        logger.debug(f"{haus.label}: SETGET16BIT_GPIO: {rsp.registers}")

    async def handle_haus(self, haus: "Haus", grafana=Influx) -> bool:
        try:
            rsp = await self._modbus.read_input_registers(
                slave=haus.config_haus.modbus_server_id,
                slave_label=haus.label,
                address=EnumModbusRegisters.SETGET16BIT_ALL_SLOW,
                count=IREGS_ALL.register_count,
            )
        except ModbusException:
            haus.status_haus.hsm_dezentral.dispatch(hsm_dezentral_signal.SignalModbusFailed())
            return False

        modbus_iregs_all2 = ModbusIregsAll2(rsp.registers)

        for scenario in SCENARIOS.iter_by_class_haus(
            cls_scenario=ScenarioHausSpTemperatureIncrease,
            haus=self._haus,
        ):
            modbus_iregs_all2.apply_scenario_temperature_increase(scenario)

        logger.debug(f"{haus.label}: modbus: {modbus_iregs_all2.debug_dict_text}")

        for scenario in SCENARIOS.iter_by_class_haus(
            cls_scenario=ScenarioHausPicoRebootReset,
            haus=self._haus,
        ):
            await self.reboot_reset(haus=haus)

        await grafana.send_modbus_iregs_all(haus, modbus_iregs_all2)
        haus.status_haus.hsm_dezentral.dispatch(SignalModbusSuccess(modbus_iregs_all=modbus_iregs_all2))

        return True

    async def reboot_reset(self, haus: "Haus") -> None:
        try:
            await self._modbus.write_coils(
                slave=haus.config_haus.modbus_server_id,
                slave_label=haus.label,
                address=EnumModbusRegisters.SETGET1BIT_REBOOT_WATCHDOG,
                values=[True],
            )
        except ModbusException:
            haus.status_haus.hsm_dezentral.dispatch(hsm_dezentral_signal.SignalModbusFailed())
