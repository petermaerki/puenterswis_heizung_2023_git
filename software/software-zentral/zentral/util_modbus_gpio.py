import pprint
from typing import List

from zentral.util_constants_haus import SpPosition
from zentral.util_modbus_iregs_all import ModbusIregsAll


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
            if p is SpPosition.UNUSED:
                continue
            pair_ds18 = self.pairs_ds18[p.ds18_pair_index]
            dict_regs[f"{p.tag}_error_C"] = pair_ds18.error_C
            if pair_ds18.error_any:
                continue
            dict_regs[f"{p.tag}_temperature_C"] = pair_ds18.temperature_C

        return dict_regs

    @property
    def debug_dict_text(self) -> str:
        return pprint.pformat(self.debug_dict, indent=2, width=1024, compact=False, sort_dicts=True, underscore_numbers=False)
