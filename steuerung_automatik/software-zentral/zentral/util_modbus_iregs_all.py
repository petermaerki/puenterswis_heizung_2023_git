import logging
from typing import List, TYPE_CHECKING


from micropython.portable_modbus_registers import IREGS_ALL
from zentral.util_constants_haus import DS18_PAIR_POSITIONS_HAUS


from zentral.util_ds18_pairs import DS18, DS18_PAIR_COUNT, DS18_Pair
from zentral.util_scenarios import (
    ScenarioHausSpTemperatureIncrease,
    SpPosition,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ModbusIregsAll:
    def __init__(self, registers: List[float]):
        assert IREGS_ALL.register_count == len(registers)

        # def get_multiple(ireg: Ireg):
        #     return [ireg.get_value(registers, i=i) for i in range(ireg.count)]

        self.version_hw = IREGS_ALL.version_hw.get_value(registers)
        self.version_sw = IREGS_ALL.version_sw.get_value(registers)
        self.uptime_s = IREGS_ALL.uptime_s.get_value(registers)
        self.errors_modbus = IREGS_ALL.errors_modbus.get_value(registers)
        self.relais_gpio = IREGS_ALL.relais_gpio.get_value(registers)
        # self.ds18_temperature_cK = get_multiple(IREGS_ALL.ds18_temperature_cK)
        # assert len(self.ds18_temperature_cK) == DS18_COUNT
        # self.ds18_ok_percent = get_multiple(IREGS_ALL.ds18_ok_percent)
        # assert len(self.ds18_ok_percent) == DS18_COUNT

        # def get_DS18(i) -> DS18:
        #     ds18_temperature_cK = IREGS_ALL.ds18_temperature_cK.get_value(registers, i)
        #     ds18_ok_percent = IREGS_ALL.ds18_ok_percent.get_value(registers, i)
        #     return DS18(i=i, temperature_K=100.0 * ds18_temperature_cK, ds18_ok_percent=ds18_ok_percent)

        # self.ds18 = [get_DS18(i) for i in range(DS18_COUNT)]

        # self.pairs_ds18 = [DS18_Pair(a=self.ds18[2 * i], b=self.ds18[2 * i + 1]) for i in range(DS18_PAIR_COUNT)]
        # print("Hallo")

        def get_DS18(i) -> DS18:
            ds18_temperature_cK = IREGS_ALL.ds18_temperature_cK.get_value(registers, i)
            ds18_ok_percent = IREGS_ALL.ds18_ok_percent.get_value(registers, i)
            return DS18(i=i, temperature_C=ds18_temperature_cK / 100.0 - 273.15, ds18_ok_percent=ds18_ok_percent)

        def get_DS18_Pair(i) -> DS18_Pair:
            return DS18_Pair(a=get_DS18(2 * i), b=get_DS18(2 * i + 1))

        self.pairs_ds18 = [get_DS18_Pair(i) for i in range(DS18_PAIR_COUNT)]
        # Hallo: [10000, 100, 1, 1200, 42, 0, 0, 0, 29359, 29365, 29378, 29346, 29352, 29359, 0, 0, 100, 100, 100, 100, 100, 100]
        # print(f"Hallo: {registers}")

    def get_ds18_pair(self, position: SpPosition) -> DS18_Pair:
        i = DS18_PAIR_POSITIONS_HAUS[position]
        return self.pairs_ds18[i]

    def apply_scenario(self, scenario) -> bool:
        assert isinstance(scenario, ScenarioHausSpTemperatureIncrease)

        ds18_pair = self.get_ds18_pair(position=scenario.position)
        ds18_pair.increment_C(scenario.delta_C)
