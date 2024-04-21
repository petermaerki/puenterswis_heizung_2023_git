import time


class UploadInterval:
    def __init__(self, interval_s: int):
        self._interval_s = interval_s
        self._next_time_s = time.monotonic()

    @property
    def time_over(self) -> bool:
        """
        Returns True every 'interval_s'
        """
        now_s = time.monotonic()
        if now_s < self._next_time_s:
            return False
        self._next_time_s = now_s + self._interval_s
        return True
