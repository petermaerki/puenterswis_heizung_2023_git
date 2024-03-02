"""
Function codes: See https://en.wikipedia.org/wiki/Modbus
"""

import machine
import util_constants
from hardware import Hardware
from portable_modbus_registers import IREGS_ALL, EnumModbusRegisters, RelaisGpioBits
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
            address=EnumModbusRegisters.SETGET16BIT_RELAIS_GPIO,
            value=0,
            on_get_cb=self._get_relais_gpio,
            on_set_cb=self._set_relais_gpio,
        )
        self._modbus.add_ireg(
            address=EnumModbusRegisters.SETGET16BIT_ALL,
            value=0,
            on_get_cb=self._get_all,
        )

    def _set_reboot_reset(self, reg_type, address, val):
        print(f"Modbus SETGET1BIT_REBOOT_RESET {val=}")
        print("machine.reset()\n\n\n")
        machine.reset()

    def _set_reboot_watchdog(self, reg_type, address, val):
        print(f"Modbus SETGET1BIT_REBOOT_WATCHDOG {val=}")
        self._wdt_disable_feed_cb()

    def _get_relais_gpio(self, reg_type, address, val):
        assert len(val) == 1
        val[0] = self._relais_gpio_value
        print(f"Modbus SETGET16BIT_RELAIS_GPIO {val=}")

    def _set_relais_gpio(self, reg_type, address, val):
        print(f"Modbus SETGET16BIT_RELAIS_GPIO {val=}")
        x = RelaisGpioBits(value=val[0])
        self._hw.PIN_RELAIS.value(x.relais_valve_open)
        self._hw.led_zentrale_blink = x.led_zentrale_blink
        self._hw.led_zentrale_on = x.led_zentrale_on
        if not self._hw.led_zentrale_blink:
            self._hw.PIN_LED_ZENTRALE.value(x.led_zentrale_on)

    @property
    def _relais_gpio_value(self) -> int:
        v = RelaisGpioBits(0)
        v.relais = self._hw.PIN_RELAIS.value()
        v.button_zentrale = not self._hw.PIN_BUTTON_ZENTRALE.value()
        v.set_led_zentrale(
            on=self._hw.PIN_LED_ZENTRALE.value(),
            blink=self._hw.led_zentrale_blink,
        )
        return v.value

    def _get_all(self, reg_type, address, val):
        # print(f"Modbus SETGET16BIT_ALL {val=}")
        assert address == EnumModbusRegisters.SETGET16BIT_ALL
        a = IREGS_ALL
        a.version_hw.set_value(val, util_constants.VERSION_HW)
        a.version_sw.set_value(val, util_constants.VERSION_SW)
        a.reset_cause.set_value(val, machine.reset_cause())
        a.uptime_s.set_value(val, self._hw.uptime_ms // 1000)
        a.errors_modbus.set_value(val, 42)
        a.relais_gpio.set_value(val, self._relais_gpio_value)
        assert len(self._hw.sensors_ds) == a.ds18_temperature_cK.count
        for i, ds in enumerate(self._hw.sensors_ds):
            a.ds18_ok_percent.set_value(val, ds.history.percent, i)
            a.ds18_temperature_cK.set_value(val, ds.temp_cK, i)

        self._wdt_feed_cb()
