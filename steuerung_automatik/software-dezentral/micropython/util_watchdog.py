import time
import machine


class Watchdog:
    # The maximum value for timeout is 8388 ms.
    WDT_TIMEOUT_MAX_MS = const(8388)
    MODBUS_WATCHDOG_MS = const(120_000)

    def __init__(self):
        self._modbus_last_ms = time.ticks_ms()
        self._wdt = machine.WDT(timeout=WDT_TIMEOUT_MAX_MS)

    def feed_sensors(self) -> None:
        """
        Feed the watchdog
        """
        if self._modbus_happy:
            self._wdt.feed()

    @property
    def _modbus_happy(self) -> bool:
        """
        return True if modbus watchdog was recently feed.
        """
        modbus_last_feed_ms = time.ticks_diff(time.ticks_ms(), self._modbus_last_ms)
        return modbus_last_feed_ms < self.MODBUS_WATCHDOG_MS

    def feed_modbus(self) -> None:
        self._modbus_last_ms = time.ticks_ms()
