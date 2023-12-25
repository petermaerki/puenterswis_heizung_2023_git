"""
Function codes: See https://en.wikipedia.org/wiki/Modbus
"""
from hardware import Hardware

from umodbus.asynchronous.serial import AsyncModbusRTU

from portable_modbus_registers import EnumModbusRegisters


class ModbusRegisters:
    def __init__(self, hw: Hardware, modbus: AsyncModbusRTU, wdt_feed_cb):
        self._hw = hw
        self._modbus = modbus
        self._wdt_feed_cb = wdt_feed_cb
        self._modbus.add_ireg(
            address=EnumModbusRegisters.IREGS_UPTIME_S,
            value=2345,
            on_get_cb=self._get_uptime_s,
        )
        self._modbus.add_coil(
            address=EnumModbusRegisters.COILS_RELAIS,
            value=0,
            on_get_cb=self._get_relais,
            on_set_cb=self._set_relais,
        )
        self._modbus.add_ireg(
            address=EnumModbusRegisters.IREGS_TEMP_C,
            value=[0] * len(hw.sensors_ds),
            on_get_cb=self._get_temp_cK,
        )

    def _get_uptime_s(self, reg_type, address, val):
        val[0] = self._hw.uptime_ms // 1000

    def _set_relais(self, reg_type, address, val):
        print(f"Relais set {val=}")
        value = val[0]
        self._hw.PIN_RELAIS.value(value)

    def _get_relais(self, reg_type, address, val):
        print(f"Relais get {val=}")
        val[0] = self._hw.PIN_RELAIS.value()

    def _get_temp_cK(self, reg_type, address, val):
        assert address == EnumModbusRegisters.IREGS_TEMP_C
        assert len(val) == len(self._hw.sensors_ds)
        for i, ds in enumerate(self._hw.sensors_ds):
            val[i] = ds.temp_cK
        print(f"temp_mC get{val=}")
        self._wdt_feed_cb()
