class History:
    SUCCESS = 1
    FAILED = 0

    def __init__(self, length=5, init=SUCCESS, percent_ok=50):
        self._array = bytearray((init,) * length)
        self._array_ptr = 0
        self._percent_ok = percent_ok
        self._counter_success = 0
        self._counter_failed = 0

    def _add(self, value: int) -> None:
        self._array[self._array_ptr] = value
        self._array_ptr += 1
        self._array_ptr %= len(self._array)

    def success(self) -> None:
        self._add(self.SUCCESS)
        self._counter_success += 1

    def failed(self) -> None:
        self._add(self.FAILED)
        self._counter_failed += 1

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
    def text_error_counter(self) -> str:
        fail_rate = (
            self._counter_success // self._counter_failed
            if self._counter_failed > 0
            else "-"
        )
        return f"{fail_rate} successful calls per error {self._counter_success}({self._counter_failed})"

    @property
    def text_history(self) -> str:
        return f"{self.ok}  {self.percent}% {self._array}"
