import machine
from onewire import OneWire, OneWireError
from ds18x20 import DS18X20

from util_history import History


class Ds:
    """
    DS is a DS18X20 temperature sensor.
    However, 'ds' in the schematic and here corresponds to a 1wire pin
    which may be connected to multiple DS18X20 temperature sensors.
    """

    MEASUREMENTS_MEDIAN_LEN = const(8)
    MEASUREMENT_FAILED_K = const(0)
    TEMPERATURE_0C_K = const(273.15)
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
        self._measurements_K = [
            self.MEASUREMENT_FAILED_K
        ] * self.MEASUREMENTS_MEDIAN_LEN
        self._measurements_idx = 0
        self.history = History(length=100, percent_ok=90)

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
            self.history.failed()
            return
        try:
            self._ds.convert_temp()
        except OneWireError:
            self._addrs = []
            self.history.failed()

    def _read_temp_K(self) -> float:
        """
        Read all DS18 connected to this 1wire pin.
        Return after we get the first successful reading
        """
        for addr in self._addrs:
            try:
                temp_C = self._ds.read_temp(addr)
                self.history.success()
                return temp_C + self.TEMPERATURE_0C_K
            except OneWireError:
                self.history.failed()
        return self.MEASUREMENT_FAILED_K

    def read_temp(self) -> None:
        """
        Insert a measurement at the beginning of the list.
        Remove a measurement at the end of the list.
        """
        self._measurements_K[self._measurements_idx] = self._read_temp_K()
        self._measurements_idx += 1
        self._measurements_idx %= self.MEASUREMENTS_MEDIAN_LEN

    @property
    def temp_cK(self) -> int:
        """
        return the median
        Unit: cK / int
        0.0 C -> 27315 cK
        25.0 C -> 29815 cK
        """
        s = sorted(self._measurements_K)
        return round(100 * s[len(s) // 2])  # Median

    @property
    def _read_temp_cC(self) -> float:
        return self.temp_cK - self.TEMPERATURE_0C_cK
