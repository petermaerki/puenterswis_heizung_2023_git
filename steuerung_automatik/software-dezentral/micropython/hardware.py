import time
import machine

from umodbus.asynchronous.serial import AsyncModbusRTU

from util_constants import DAY_MS, WEEK_MS
from util_DS18X20 import Ds

UART_MODBUS_ID = 0
GPIO_MODBUS_DI = 0
GPIO_MODBUS_RO = 1
GPIO_MODBUS_DE = 2

GPIO_MODBUS_ADDRS = (
    "GPIO8",
    "GPIO9",
    "GPIO10",
    "GPIO11",
    "GPIO12",
    "GPIO13",
    "GPIO14",
    "GPIO15",
)
PIN_MODBUS_ADDR = [
    machine.Pin(gpio, machine.Pin.PULL_DOWN) for gpio in GPIO_MODBUS_ADDRS
]

GPIO_DS = (
    "GPIO29",
    "GPIO28",
    "GPIO27",
    "GPIO26",
    "GPIO25",
    "GPIO24",
    "GPIO23",
    "GPIO22",
)


class Hardware:
    def __init__(self):
        self._timer_callbacks = []
        self.PIN_RELAIS = machine.Pin(3, machine.Pin.OUT)
        self.PIN_RELAIS.off()
        # Make sure we release the modbus!
        machine.Pin(GPIO_MODBUS_DE, machine.Pin.OUT).off()
        self._ticks_boot_ms = time.ticks_ms()
        self._modbus_server_addr = self.dip_switch_addr
        self.modbus = AsyncModbusRTU(
            addr=self._modbus_server_addr,
            uart_id=UART_MODBUS_ID,
            pins=(GPIO_MODBUS_DI, GPIO_MODBUS_RO),  # (TX, RX)
            ctrl_pin=GPIO_MODBUS_DE,
            baudrate=9600,
            data_bits=8,
            stop_bits=1,
            parity=None,
        )

        self.sensors_ds = [Ds(gpio) for gpio in GPIO_DS]

    @property
    def dip_switch_changed(self) -> bool:
        new_addr = self.dip_switch_addr
        changed = new_addr != self._modbus_server_addr
        if changed:
            print(
                f"Dip Switch changed from {self._modbus_server_addr} to {new_addr}: reset()"
            )
        return changed

    @property
    def _uptime_ms(self) -> int:
        """
        Return the uptime, wrap around after some time.
        See: https://docs.micropython.org/en/latest/library/time.html#time.ticks_ms
        """
        return time.ticks_diff(time.ticks_ms(), self._ticks_boot_ms)

    @property
    def wrap_uptime_ms(self) -> int:
        """
        wrap_uptime_ms will start from 0 when the RP2 starts or soft-resets.
        After one week, the time will wrap down by one day.
        """
        while True:
            uptime_ms = self._uptime_ms
            if uptime_ms < WEEK_MS:
                return uptime_ms
            # Wrap the uptime down by DAY_MS
            self._ticks_boot_ms = time.ticks_add(self.ticks_boot_ms, DAY_MS)

    @property
    def dip_switch_addr(self) -> int:
        """
        Read the dipswitch and return the modbus address
        """
        addr = 0
        for pin in PIN_MODBUS_ADDR:
            addr *= 2
            if pin.value():
                addr += 1
        return addr
