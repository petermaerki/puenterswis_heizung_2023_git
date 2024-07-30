import machine
from onewire import OneWire, OneWireError
from ds18x20 import DS18X20


class Ds:
    """
    DS is a DS18X20 temperature sensor.
    However, 'ds' in the schematic and here corresponds to a 1wire pin
    which may be connected to multiple DS18X20 temperature sensors.
    """

    MEASUREMENTS_MEDIAN_LEN = const(10)
    MEASUREMENT_FAILED_cK = const(0)
    TEMPERATURE_0C_cK = const(27315)

    def __init__(self, gpio: str):
        self._ds = DS18X20(OneWire(machine.Pin(gpio)))
        """
        Again, this is a 1wire pin which may be connected to multipe DS18 sensors.
        """
        self._addrs = []
        """
        These are the sensors we discovered on this 1wire pin.
        """
        self._measurements_cK = [self.MEASUREMENT_FAILED_cK] * self.MEASUREMENTS_MEDIAN_LEN
        self._measurements_idx = 0
        # self.history = History(length=100, percent_ok=90)

    def scan(self) -> None:
        """
        Scan the 1wire pin for connected sensors
        """
        self._addrs = self._ds.scan()

    def convert_temp(self) -> None:
        """
        Tell all sensors on the 1wire pin to start measureing.
        """
        if len(self._addrs) == 0:
            # self.history.failed()
            return
        try:
            self._ds.convert_temp()
        except OneWireError:
            self._addrs = []
            # self.history.failed()

    def _read_temp_cK(self) -> float:
        """
        Read all DS18 connected to this 1wire pin.
        Return after we get the first successful reading
        """
        for addr in self._addrs:
            try:
                temp_C = self._ds.read_temp(addr)
                # self.history.success()
                return round(100 * temp_C) + self.TEMPERATURE_0C_cK
            except OneWireError:
                # self.history.failed()
                pass
        return self.MEASUREMENT_FAILED_cK

    def read_temp(self) -> None:
        """
        Insert a measurement at the beginning of the list.
        Remove a measurement at the end of the list.
        """
        self._measurements_idx += 1
        self._measurements_idx %= self.MEASUREMENTS_MEDIAN_LEN
        self._measurements_cK[self._measurements_idx] = self._read_temp_cK()

    def temp_cK(self, slow=True) -> int:
        """
        return the median
        Unit: cK / int
        0.0 C -> 27315 cK
        25.0 C -> 29815 cK
        """
        if slow:
            # Slow is used in Dezentral
            # Use Median: Fault tolerant and slow
            s = sorted(self._measurements_cK)
            return s[len(s) // 2]

        # Fast is used in Zentral
        # Take last value: fast and sensile to sensor read faults.
        return self._measurements_cK[self._measurements_idx]

    @property
    def percent(self) -> int:
        """
        return a number between 0 (all failed) and 100 (all success)
        """
        failed_count = self._measurements_cK.count(self.MEASUREMENT_FAILED_cK)
        return (100 // self.MEASUREMENTS_MEDIAN_LEN) * (self.MEASUREMENTS_MEDIAN_LEN - failed_count)

    @property
    def ok(self) -> bool:
        return self.temp_cK(slow=True) != self.MEASUREMENT_FAILED_cK
