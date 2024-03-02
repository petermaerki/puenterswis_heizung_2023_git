import time
import machine

from umodbus.asynchronous.serial import AsyncModbusRTU

from util_constants import DEVELOPMENT
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
PIN_MODBUS_ADDR = [machine.Pin(gpio, machine.Pin.PULL_DOWN) for gpio in GPIO_MODBUS_ADDRS]

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
    LIMIT_UPTIME_MS = (1200 if DEVELOPMENT else 12 * 60 * 60) * 1000

    def __init__(self):
        self._ticks_boot_ms = time.ticks_ms()

        """
        If None, LIMIT_UPTIME_S has been reached.
        """
        self.PIN_RELAIS = machine.Pin(3, machine.Pin.OUT)
        self.PIN_RELAIS.off()
        self.PIN_DS_OK_LED = machine.Pin(20, machine.Pin.OUT)
        self.PIN_DS_OK_LED.off()
        self.PIN_BUTTON_ZENTRALE = machine.Pin(4, machine.Pin.IN)
        self.PIN_LED_ZENTRALE = machine.Pin(6, machine.Pin.OUT)
        self.PIN_DS_OK_LED.on()

        self.led_zentrale_blink = False
        self.led_zentrale_on = False

        def cb_led_zentrale_blink(t):
            if self.led_zentrale_blink:
                self.PIN_LED_ZENTRALE.toggle()

        machine.Timer(period=500, mode=machine.Timer.PERIODIC, callback=cb_led_zentrale_blink)

        # Make sure we release the modbus!
        machine.Pin(GPIO_MODBUS_DE, machine.Pin.OUT).off()
        self.modbus_server_addr = self.dip_switch_addr
        self.modbus = AsyncModbusRTU(
            addr=self.modbus_server_addr,
            uart_id=UART_MODBUS_ID,
            pins=(GPIO_MODBUS_DI, GPIO_MODBUS_RO),  # (TX, RX)
            ctrl_pin=GPIO_MODBUS_DE,
            baudrate=9600,
            data_bits=8,
            stop_bits=1,
            parity=None,
        )

        self.sensors_ds = [Ds(gpio) for gpio in GPIO_DS]

    def handle_ds_ok_led(self) -> None:
        """
        The 'DS OK' LED should be on when all temperature sensors
        in use work find.
        """
        # The first two sensors are not in use
        DS_NOT_IN_USE = 2
        ds_ok = True
        for ds in self.sensors_ds[DS_NOT_IN_USE:]:
            if not ds.history.last_ok:
                ds_ok = False
        self.PIN_DS_OK_LED.value(ds_ok)

    @property
    def dip_switch_changed(self) -> bool:
        new_addr = self.dip_switch_addr
        changed = new_addr != self.modbus_server_addr
        if changed:
            print(f"Dip Switch changed from {self.modbus_server_addr} to {new_addr}: reset()")
        return changed

    @property
    def uptime_ms(self) -> int:
        """
        'uptime_ms()' will start from 0 when the RP2 starts or soft-resets.
        The time will be limited to LIMIT_UPTIME_S.
        """
        if self._ticks_boot_ms is None:
            return self.LIMIT_UPTIME_MS

        # See: https://docs.micropython.org/en/latest/library/time.html#time.ticks_ms
        uptime_ms = time.ticks_diff(time.ticks_ms(), self._ticks_boot_ms)

        if uptime_ms < self.LIMIT_UPTIME_MS:
            return uptime_ms

        self._ticks_boot_ms = None
        return self.LIMIT_UPTIME_MS

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
