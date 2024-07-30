import _thread
from math import ceil
import asyncio

USE_CORE2 = const(False)


class UartRx:
    def __init__(self):
        self.uart_rx_ready = asyncio.ThreadSafeFlag()
        self.uart_rx_data = None

    def set(self, data: bytes):
        self.uart_rx_data = data
        self.uart_rx_ready.set()

    async def wait(self) -> bytes:
        await self.uart_rx_ready.wait()
        assert self.uart_rx_data is not None
        return self.uart_rx_data


uart_rx = UartRx()


def main_core2(uart):
    duration_char_ms = 11 / 9600
    timeout_char_ms = ceil(1.5 * 1000 * duration_char_ms)
    timeout_ms = ceil(4.5 * 1000 * duration_char_ms)
    print(f"DEBUG: main_core2: started. {timeout_char_ms=} {timeout_ms=}")

    while True:
        # data = hw.modbus._itf._uart.read()
        data = uart.read()
        if data is None:
            continue
        if len(data) == 1:
            # This happens after each request. Why?
            continue
        # print(f"{data=} {len(data)}")
        uart_rx.set(data=data)
    return

    # Make sure we release the modbus!
    machine.Pin(hardware.GPIO_MODBUS_DE, machine.Pin.OUT).off()

    uart = machine.UART(
        hardware.UART_MODBUS_ID,
        baudrate=9600,
        bits=8,
        stop=1,
        parity=None,
        tx=hardware.GPIO_MODBUS_DI,
        rx=hardware.GPIO_MODBUS_RO,
        timeout=timeout_ms,
        timeout_char=timeout_char_ms,
    )
    while True:
        data = uart.read()
        if data is None:
            continue
        print(f"{data=} {len(data)}")


def start_uart_reader(uart):
    if USE_CORE2:
        # main_core2(True)
        _thread.start_new_thread(main_core2, (uart,))
