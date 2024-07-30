class HistoryModbus:
    SUCCESS = 1
    FAILED = 0

    def __init__(self, length=100, init=SUCCESS, percent_ok=50):
        self._array = bytearray((init,) * length)
        self._array_ptr = 0
        self._percent_ok = percent_ok

    def _add(self, value: int) -> None:
        self._array[self._array_ptr] = value
        self._array_ptr += 1
        if self._array_ptr >= len(self._array):
            self._array_ptr = 0

    def success(self) -> None:
        self._add(self.SUCCESS)

    def failed(self) -> None:
        self._add(self.FAILED)

    @property
    def ok(self) -> bool:
        """
        return true if the where more success than failed
        """
        return self.percent > self._percent_ok

    @property
    def percent(self) -> int:
        """
        return a number between 0 (all failed) and 100 (all success)
        """
        return round(100.0 * (sum(self._array) / len(self._array)))

    @property
    def text_history_ex(self) -> str:
        return f"{self.ok}  {self.percent}% {self._array}"

    @property
    def text_history(self) -> str:
        return f"{self.ok} {self.percent}%"
