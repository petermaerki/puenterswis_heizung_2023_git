# scripts/example/simple_rtu_client.py
import asyncio
import pprint
from typing import List

from pymodbus import ModbusException

from zentral.constants import MODBUS_ADDRESS_RELAIS
from zentral.util_constants_haus import SpPosition
from zentral.util_modbus_iregs_all import ModbusIregsAll
from zentral.util_modbus_wrapper import ModbusWrapper


class Gpio:
    COIL_ADDRESS = 0
    RELAIS_COUNT = 8

    def __init__(self, modbus: ModbusWrapper, modbus_address: int):
        assert isinstance(modbus, ModbusWrapper)
        self._modbus = modbus
        self._modbus_address = modbus_address
        self._modbus_label = f"Gpio(modbus={self._modbus_address})"

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
            slave_label=self._modbus_label,
            address=self.COIL_ADDRESS,
            values=list_gpio,
        )
        if response.isError():
            print("ERROR: pymodbus returned an error!")
            raise ModbusException("Hallo")


class ModbusIregsAll2(ModbusIregsAll):
    def __init__(self, registers: List[float]):
        super().__init__(registers=registers)
        self._registers = registers

    @property
    def debug_dict(self) -> dict:
        dict_regs = {
            "all": self._registers,
            "utime_s": self.uptime_s,
            "version_hw": self.version_hw,
            "version_sw": self.version_sw,
            "errors_modbus": self.errors_modbus,
            "reset_cause": self.reset_cause,
            "relais_gpio.button_zentrale": self.relais_gpio.button_zentrale,
            "relais_gpio.relais_valve_open": self.relais_gpio.relais_valve_open,
            "relais_gpio.led_zentrale_on": self.relais_gpio.led_zentrale_on,
            "relais_gpio.led_zentrale_blink": self.relais_gpio.led_zentrale_blink,
        }

        for p in SpPosition:
            pair_ds18 = self.pairs_ds18[p.ds18_pair_index]
            dict_regs[f"{p.tag}_error_C"] = pair_ds18.error_C
            if pair_ds18.error_any:
                continue
            dict_regs[f"{p.tag}_temperature_C"] = pair_ds18.temperature_C

        return dict_regs

    @property
    def debug_dict_text(self) -> str:
        return pprint.pformat(self.debug_dict, indent=2, width=1024, compact=False, sort_dicts=True, underscore_numbers=False)
