import logging
from typing import TYPE_CHECKING, List

from micropython.portable_modbus_registers import IREGS_ALL, GpioBits

from zentral.util_ds18_pairs import DS18, DS18_COUNT, DS18_PAIR_COUNT, DS18_0C_cK, DS18_MEASUREMENT_FAILED_cK, DS18_Pair
from zentral.util_scenarios import SpPosition
from zentral.util_sp_ladung import LadungMinimum, SpTemperatur

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

DS18_LIMIT_OK_PERCENT = 50
"""
The modbus registers 'is_ok' and 'ok_percent' are somehow redundant.
If a 'ok_percent' goes below this value, we overwrite 'is_ok' to False.
"""


class ModbusIregsAll:
    def __init__(self, registers: List[float]):
        assert IREGS_ALL.register_count == len(registers)

        self.version_hw = IREGS_ALL.version_hw.get_value(registers)
        self.version_sw = IREGS_ALL.version_sw.get_value(registers)
        self.uptime_s = IREGS_ALL.uptime_s.get_value(registers)
        self.reset_cause = IREGS_ALL.reset_cause.get_value(registers)
        self.errors_modbus = IREGS_ALL.errors_modbus.get_value(registers)
        self._gpio = IREGS_ALL.relais_gpio.get_value(registers)

        self.relais_gpio = GpioBits(self._gpio)

        def get_DS18(i: int) -> DS18:
            assert 0 <= i < DS18_COUNT
            ds18_temperature_cK = IREGS_ALL.ds18_temperature_cK.get_value(registers, i)
            ds18_ok_percent = IREGS_ALL.ds18_ok_percent.get_value(registers, i)
            is_ok = ds18_temperature_cK != DS18_MEASUREMENT_FAILED_cK
            if ds18_ok_percent < DS18_LIMIT_OK_PERCENT:
                is_ok = False
            return DS18(
                i=i,
                temperature_C=(ds18_temperature_cK - DS18_0C_cK) / 100.0,
                ds18_ok_percent=ds18_ok_percent,
                is_ok=is_ok,
            )

        def get_DS18_Pair(i) -> DS18_Pair:
            assert 0 <= i < DS18_PAIR_COUNT
            return DS18_Pair(a=get_DS18(2 * i), b=get_DS18(2 * i + 1))

        self.pairs_ds18 = [get_DS18_Pair(i) for i in range(DS18_PAIR_COUNT)]
        # Hallo: [10000, 100, 1, 1200, 42, 0, 0, 0, 29359, 29365, 29378, 29346, 29352, 29359, 0, 0, 100, 100, 100, 100, 100, 100]
        # print(f"Hallo: {registers}")

    def get_ds18_pair(self, position: SpPosition) -> DS18_Pair:
        return self.pairs_ds18[position.ds18_pair_index]

    @property
    def debug_temperatureC(self) -> str:
        return " ".join([f"{x.temperature_C:0.1f}C" for x in self.pairs_ds18])

    @property
    def debug2_temperatureC(self) -> str:
        return " ".join([f"{x.a.temperature_C:0.1f}/{x.b.temperature_C:0.1f}C" for x in self.pairs_ds18])

    @property
    def debug_temperatureC_percent(self) -> str:
        return " ".join([f"{x.a.temperature_C:0.1f}/{x.b.temperature_C:0.1f}C({x.a.ds18_ok_percent}/{x.b.ds18_ok_percent}%)" for x in self.pairs_ds18])

    @property
    def sp_temperatur(self) -> SpTemperatur:
        temperature_unten = self.pairs_ds18[SpPosition.UNTEN.ds18_pair_index]
        temperature_mitte = self.pairs_ds18[SpPosition.MITTE.ds18_pair_index]
        temperature_oben = self.pairs_ds18[SpPosition.OBEN.ds18_pair_index]

        error = temperature_unten.error_any or temperature_mitte.error_any or temperature_oben.error_any
        if error:
            return None

        return SpTemperatur(
            unten_C=temperature_unten.temperature_C,
            mitte_C=temperature_mitte.temperature_C,
            oben_C=temperature_oben.temperature_C,
        )

    def ladung_minimum(self, temperatur_aussen_C) -> LadungMinimum:
        sp_temperature = self.sp_temperatur
        if sp_temperature is None:
            return None
        return LadungMinimum(sp_temperature, temperatur_aussen_C=temperatur_aussen_C)

    def _version_to_verbose(self, version: int) -> str:
        """
        See: micropython/util_constants.py
        """
        return f"{version//10000}.{version//100%100}.{version%100}"

    @property
    def version_sw_verbose(self) -> str:
        return self._version_to_verbose(self.version_sw)

    @property
    def version_hw_verbose(self) -> str:
        return self._version_to_verbose(self.version_hw)
