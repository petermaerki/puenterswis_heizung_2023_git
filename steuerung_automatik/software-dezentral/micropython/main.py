#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Main script

Do your stuff here, this file is similar to the loop() function on Arduino

Create an async Modbus RTU client (slave) which can be requested for data or
set with specific values by a host device.

The RTU communication pins can be choosen freely (check MicroPython device/
port specific limitations).
The register definitions of the client as well as its connection settings like
bus address and UART communication speed can be defined by the user.
"""
import uasyncio as asyncio
import micropython
import machine

from hardware import Hardware
from util_modbus import ModbusRegisters
from util_watchdog import Watchdog

micropython.alloc_emergency_exception_buf(100)


wdt = Watchdog()
hw = Hardware()
regs = ModbusRegisters(hw=hw, modbus=hw.modbus, wdt_feed_cb=wdt.feed_modbus)


async def task_sensor_ds():
    while True:
        for ds in hw.sensors_ds:
            ds.scan()

        for _ in range(10):
            for ds in hw.sensors_ds:
                ds.convert_temp()

            await asyncio.sleep_ms(750 + 150)  # See Datasheet

            for ds in hw.sensors_ds:
                ds.read_temp()

            await asyncio.sleep_ms(100)

            wdt.feed_sensors()


async def task_reset_on_dipswitch():
    while True:
        if hw.dip_switch_changed:
            machine.soft_reset()
        await asyncio.sleep_ms(2000)


async def task_modbus_server():
    await hw.modbus.bind()
    await hw.modbus.serve_forever()


asyncio.create_task(task_reset_on_dipswitch())
asyncio.create_task(task_sensor_ds())
asyncio.run(task_modbus_server())
