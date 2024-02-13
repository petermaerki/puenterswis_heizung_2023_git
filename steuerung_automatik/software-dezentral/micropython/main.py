#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
"""
import machine
import uasyncio as asyncio
import util_constants
from hardware import Hardware
from util_modbus import ModbusRegisters
from util_uart_reader import start_uart_reader
from util_watchdog import Watchdog

import micropython

micropython.alloc_emergency_exception_buf(100)


wdt = Watchdog()
hw = Hardware()
regs = ModbusRegisters(
    hw=hw,
    modbus=hw.modbus,
    wdt_feed_cb=wdt.feed_modbus,
    wdt_disable_feed_cb=wdt.disable_feed,
)


async def task_sensor_ds():
    while True:
        for ds in hw.sensors_ds:
            ds.scan()
            await asyncio.sleep_ms(10)

        for ds in hw.sensors_ds:
            ds.convert_temp()
            await asyncio.sleep_ms(10)

        await asyncio.sleep_ms(750 + 150)  # See Datasheet

        for ds in hw.sensors_ds:
            ds.read_temp()
            await asyncio.sleep_ms(10)

        hw.handle_ds_ok_led()
        wdt.feed_sensors()


async def task_reset_on_dipswitch():
    while True:
        if hw.dip_switch_changed:
            machine.soft_reset()
        await asyncio.sleep_ms(2000)


async def task_modbus_server():
    if not util_constants.DEVELOPMENT:
        await asyncio.sleep_ms(10000)
    await hw.modbus.bind()
    print(f"Modbus address {hw.modbus_server_addr}")
    await hw.modbus.serve_forever()


start_uart_reader(uart=hw.modbus._itf._uart)


asyncio.create_task(task_reset_on_dipswitch())
asyncio.create_task(task_sensor_ds())
asyncio.run(task_modbus_server())
