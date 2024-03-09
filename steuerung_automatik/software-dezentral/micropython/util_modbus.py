"""
Function codes: See https://en.wikipedia.org/wiki/Modbus
"""

import machine
import util_constants
from hardware import Hardware
from portable_modbus_registers import IREGS_ALL, EnumModbusRegisters, GpioBits
from umodbus.asynchronous.serial import AsyncModbusRTU


class ModbusRegisters:
    def __init__(self, hw: Hardware, modbus: AsyncModbusRTU, wdt_feed_cb, wdt_disable_feed_cb):
        self._hw = hw
        self._modbus = modbus
        self._wdt_feed_cb = wdt_feed_cb
        self._wdt_disable_feed_cb = wdt_disable_feed_cb

        self._modbus.add_coil(
            address=EnumModbusRegisters.SETGET1BIT_REBOOT_RESET,
            value=0,
            on_set_cb=self._set_reboot_reset,
        )
        self._modbus.add_coil(
            address=EnumModbusRegisters.SETGET1BIT_REBOOT_WATCHDOG,
            value=0,
            on_set_cb=self._set_reboot_watchdog,
        )
        self._modbus.add_hreg(
            address=EnumModbusRegisters.SETGET16BIT_GPIO,
            value=0,
            on_get_cb=self._get_gpios,
            on_set_cb=self._set_gpios,
        )
        self._modbus.add_ireg(
            address=EnumModbusRegisters.SETGET16BIT_ALL_SLOW,
            value=0,
            on_get_cb=self._get_all,
        )
        self._modbus.add_ireg(
            address=EnumModbusRegisters.SETGET16BIT_ALL_FAST,
            value=0,
            on_get_cb=self._get_all,
        )

    def _set_reboot_reset(self, reg_type, address, val):
        # print(f"Modbus SETGET1BIT_REBOOT_RESET {val=}")
        print("machine.reset()\n\n\n")
        machine.reset()

    def _set_reboot_watchdog(self, reg_type, address, val):
        # print(f"Modbus SETGET1BIT_REBOOT_WATCHDOG {val=}")
        self._wdt_disable_feed_cb()

    def _get_gpios(self, reg_type, address, val):
        assert len(val) == 1
        val[0] = self._gpios
        # print(f"Modbus SETGET16BIT_GPIO {val=}")

    def _set_gpios(self, reg_type, address, val):
        # print(f"Modbus SETGET16BIT_GPIO {val=}")
        bits = GpioBits(value=val[0])
        self._hw.PIN_RELAIS.value(bits.relais_valve_open)
        self._hw.led_zentrale_blink = bits.led_zentrale_blink
        self._hw.led_zentrale_on = bits.led_zentrale_on
        if not self._hw.led_zentrale_blink:
            self._hw.PIN_LED_ZENTRALE.value(bits.led_zentrale_on)

    @property
    def _gpios(self) -> int:
        v = GpioBits(0)
        v.relais = self._hw.PIN_RELAIS.value()
        v.button_zentrale = not self._hw.PIN_BUTTON_ZENTRALE.value()
        v.set_led_zentrale(
            on=self._hw.led_zentrale_on,
            blink=self._hw.led_zentrale_blink,
        )
        return v.value

    def _get_all(self, reg_type, address, val):
        # print(f"Modbus SETGET16BIT_ALL_SLOW {val=}")
        assert address in (EnumModbusRegisters.SETGET16BIT_ALL_SLOW, EnumModbusRegisters.SETGET16BIT_ALL_FAST)
        a = IREGS_ALL
        a.version_hw.set_value(val, util_constants.VERSION_HW)
        a.version_sw.set_value(val, util_constants.VERSION_SW)
        a.reset_cause.set_value(val, machine.reset_cause())
        a.uptime_s.set_value(val, self._hw.uptime_ms // 1000)
        a.errors_modbus.set_value(val, 42)
        a.relais_gpio.set_value(val, self._gpios)
        assert len(self._hw.sensors_ds) == a.ds18_temperature_cK.count
        slow = address == EnumModbusRegisters.SETGET16BIT_ALL_SLOW
        for i, ds in enumerate(self._hw.sensors_ds):
            a.ds18_ok_percent.set_value(val, ds.percent, i)
            a.ds18_temperature_cK.set_value(val, ds.temp_cK(slow=slow), i)

        self._wdt_feed_cb()
