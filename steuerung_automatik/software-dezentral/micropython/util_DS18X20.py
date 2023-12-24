import machine
from onewire import OneWire, OneWireError
from ds18x20 import DS18X20


class Ds:
    """
    DS is a DS18X20 temperature sensor.
    However, 'ds' in the schematic and here corresponds to a 1wire pin
    which may be connected to multiple DS18X20 temperature sensors.
    """

    MEASUREMENTS_MEDIAN_LEN = const(8)
    MEASUREMENT_FAILED_mC = const(0)

    def __init__(self, gpio: str):
        self._ds = DS18X20(OneWire(machine.Pin(gpio)))
        """
        Again, this is a 1wire pin which may be connected to multipe DS18 sensors.
        """
        self._addrs = []
        """
        These are the sensors we discovered on this 1wire pin.
        """
        self._measurements_C = [self.MEASUREMENT_FAILED_mC]
        """
        A list of MEASUREMENTS_MEDIAN_LEN measurements.
        """

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
            return
        try:
            self._ds.convert_temp()
        except OneWireError:
            self._addrs = []

    def _read_temp(self) -> float:
        """
        Read all DS18 connected to this 1wire pin.
        Return after we get the first successful reading
        """
        for addr in self._addrs:
            try:
                return self._ds.read_temp(addr)
            except OneWireError:
                pass
        return self.MEASUREMENT_FAILED_mC

    def read_temp(self) -> None:
        """
        Insert a measurement at the beginning of the list.
        Remove a measurement at the end of the list.
        """
        self._measurements_C.insert(0, self._read_temp())

        while len(self._measurements_C) > self.MEASUREMENTS_MEDIAN_LEN:
            self._measurements_C.pop()

    @property
    def temp_mC(self) -> int:
        """
        return the median
        Unit: mC / int
        0.0 -> 0
        25.0 -> 25000
        """
        s = sorted(self._measurements_C)
        median_C = s[len(s) // 2]  # Median
        return round(1000.0 * median_C)
