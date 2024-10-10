import logging
import time
from typing import TYPE_CHECKING

from micropython.portable_modbus_registers import IREGS_ALL, EnumModbusRegisters
from pymodbus.exceptions import ModbusException

from zentral import hsm_dezentral_signal
from zentral.constants import DEZENTRAL_VERSION_SW_FIXED_RELAIS_VALVE_OPEN, ModbusExceptionNoResponseReceived
from zentral.hsm_dezentral_signal import SignalModbusSuccess
from zentral.util_influx import Influx
from zentral.util_modbus_gpio import ModbusIregsAll2
from zentral.util_modbus_wrapper import ModbusWrapper
from zentral.util_scenarios import SCENARIOS, ScenarioHaeuserValveOpen, ScenarioHausModbusNoResponseReceived, ScenarioHausPicoRebootReset, ScenarioHausValveOpenCloseOthers

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

        scenario_valve = SCENARIOS.find(cls_scenario=ScenarioHausValveOpenCloseOthers)
        if scenario_valve is not None:
            hsm.dezentral_gpio.relais_valve_open = bool(scenario_valve.haus_nummer == haus.config_haus.nummer)

        if SCENARIOS.find(cls_scenario=ScenarioHaeuserValveOpen) is not None:
            hsm.dezentral_gpio.relais_valve_open = True

        if hsm.modbus_iregs_all is not None:
            if hsm.modbus_iregs_all.version_sw >= DEZENTRAL_VERSION_SW_FIXED_RELAIS_VALVE_OPEN:
                # Remove above 'if' and this comment when all dezental are updated with this version.
                changed = hsm.dezentral_gpio.changed(hsm.modbus_iregs_all.relais_gpio)
                if False:
                    text1 = f"local {hsm.dezentral_gpio.value} <-> remote {hsm.modbus_iregs_all.relais_gpio.value}"
                    text2 = "  changed" if changed else "  unchanged"
                    print(f"{haus.label:19} relais_valve_open={hsm.dezentral_gpio.relais_valve_open} ({text1}) {text2}")
                if not changed:
                    return

        try:
            _rsp = await self._modbus.write_registers(
                slave=haus.config_haus.modbus_server_id,
                slave_label=haus.label,
                address=EnumModbusRegisters.SETGET16BIT_GPIO,
                values=[hsm.dezentral_gpio.value],
            )
        except ModbusException as e:
            logger.warning(f"{haus.label}: TODO {e}")

    async def handle_haus(self, haus: "Haus", grafana: Influx, temperatur_aussen_C: float) -> bool:
        try:
            for _ in SCENARIOS.iter_by_class_haus(ScenarioHausModbusNoResponseReceived, haus=haus):
                raise ModbusExceptionNoResponseReceived(ScenarioHausModbusNoResponseReceived.__name__)

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

        logger.debug(f"{haus.label}: modbus: {modbus_iregs_all2.debug_dict_text}")

        for scenario in SCENARIOS.iter_by_class_haus(
            cls_scenario=ScenarioHausPicoRebootReset,
            haus=self._haus,
        ):
            await self.reboot_reset(haus=haus)

        if modbus_iregs_all2.relais_gpio.relais_valve_open:
            self._haus.config_haus.hausreihe.set_leitung_warm(now_s=time.monotonic())

        await grafana.send_modbus_iregs_all(haus, modbus_iregs_all2, temperatur_aussen_C)
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
