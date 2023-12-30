"""
Function codes: See https://en.wikipedia.org/wiki/Modbus
"""
import machine
from hardware import Hardware

from umodbus.asynchronous.serial import AsyncModbusRTU

from portable_modbus_registers import EnumModbusRegisters, IregsAll
import util_constants


class ModbusRegisters:
    def __init__(self, hw: Hardware, modbus: AsyncModbusRTU, wdt_feed_cb):
        self._hw = hw
        self._modbus = modbus
        self._wdt_feed_cb = wdt_feed_cb
        self.iregs_all = IregsAll()

        self._modbus.add_hreg(
            address=EnumModbusRegisters.HREG_RELAIS_GPIO,
            value=0,
            on_set_cb=self._set_relais_gpio,
            on_get_cb=self._get_relais_gpio,
        )
        self._modbus.add_ireg(
            address=EnumModbusRegisters.IREGS_ALL,
            value=0,
            on_get_cb=self._get_all,
        )

    def _set_relais_gpio(self, reg_type, address, val):
        print(f"Relais set {val=}")
        value = val[0]
        self._hw.PIN_RELAIS.value(value)

    def _get_relais_gpio(self, reg_type, address, val):
        print(f"Relais get {val=}")
        val[0] = self._hw.PIN_RELAIS.value()

    def _get_all(self, reg_type, address, val):
        assert address == EnumModbusRegisters.IREGS_ALL
        a = self.iregs_all
        a.version_hw.set_value(val, util_constants.VERSION_HW)
        a.version_sw.set_value(val, util_constants.VERSION_SW)
        a.reset_cause.set_value(val, machine.reset_cause())
        a.uptime_s.set_value(val, self._hw.uptime_ms // 1000)
        a.errors_modbus.set_value(val, 42)
        a.relais_gpio.set_value(val, self._hw.PIN_RELAIS.value())
        assert len(self._hw.sensors_ds) == a.temperature_cK.count
        for i, ds in enumerate(self._hw.sensors_ds):
            a.errors_ds18.set_value(val, ds.history.percent, i)
            a.temperature_cK.set_value(val, ds.temp_cK, i)

        self._wdt_feed_cb()
