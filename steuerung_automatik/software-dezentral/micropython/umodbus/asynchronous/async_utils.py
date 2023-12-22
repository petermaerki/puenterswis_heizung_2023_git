#!/usr/bin/env python3
#
# Copyright (c) 2019, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#

# system packages
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time


async def hybrid_sleep(time_us: int) -> None:
    """
    Sleeps for the given time using both asyncio and the time library.

    :param      time_us     The total time to sleep, in microseconds
    :type       int
    """

    sleep_ms, sleep_us = int(time_us / 1000), (time_us % 1000)
    if sleep_ms > 0:
        await asyncio.sleep_ms(sleep_ms)
    if sleep_us > 0:
        # sleep using inbuilt time library since asyncio
        # too slow for switching times of this magnitude
        time.sleep_us(sleep_us)
