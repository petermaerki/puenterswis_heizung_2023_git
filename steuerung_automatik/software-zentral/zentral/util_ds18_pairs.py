"""
Error logic

DSx+0 DSx+1 temperature_C error_C
DSa   DSb
17.2  17.2  17.2          None
17.2  25.8  17.2          DS18_REDUNDANCY_ERROR_DIFF_C
err   17.2  17.2          DS18_REDUNDANCY_WARNING_DSa_BROKEN_C
17.2  err   17.2          DS18_REDUNDANCY_WARNING_DSb_BROKEN_C
err   err   None          DS18_REDUNDANCY_FATAL_C
"""

import dataclasses
import logging

logger = logging.getLogger(__name__)


DS18_COUNT = 8
DS18_PAIR_COUNT = DS18_COUNT // 2
DS18_OK_PERCENT = 90
DS18_MEASUREMENT_FAILED_cK = 0
DS18_0C_cK = 27315

DS18_REDUNDANCY_ACCEPTABLE_DIFF_C = 5.0
DS18_REDUNDANCY_ERROR_DIFF_C = 10.0
DS18_REDUNDANCY_WARNING_DSa_BROKEN_C = 1.0
DS18_REDUNDANCY_WARNING_DSb_BROKEN_C = 2.0
DS18_REDUNDANCY_FATAL_C = 20.0


@dataclasses.dataclass(frozen=True)
class DS18:
    i: int
    temperature_C: float
    ds18_ok_percent: int
    """
    0: Never seen
    100: Always seen
    """
    is_ok: bool


@dataclasses.dataclass()
class DS18_Pair:
    a: DS18
    b: DS18
    error_C: float | None = None
    """
    The error-temperature.
    None if no error occured.
    """
    temperature_C: float | None = None
    """
    The effective temperature.
    None if both sensors are broken.
    """
    error_any = True

    def __post_init__(self):
        a_ok = self.a.is_ok
        b_ok = self.b.is_ok
        a_broken = not a_ok
        b_broken = not b_ok

        if a_broken and b_broken:
            # Both sensors broken
            self.error_C = DS18_REDUNDANCY_FATAL_C
            self.temperature_C = None
            return

        if a_ok and b_ok:
            # Both ok
            diff_C = self.a.temperature_C - self.b.temperature_C
            if diff_C > abs(DS18_REDUNDANCY_ACCEPTABLE_DIFF_C):
                self.error_C = DS18_REDUNDANCY_ERROR_DIFF_C
            self.temperature_C = self.a.temperature_C
            self.error_any = False
            return

        # Exactly one sensor broken
        if a_broken:
            self.error_C = DS18_REDUNDANCY_WARNING_DSa_BROKEN_C
            self.temperature_C = self.b.temperature_C
        else:
            self.error_C = DS18_REDUNDANCY_WARNING_DSb_BROKEN_C
            self.temperature_C = self.a.temperature_C

    def increment_C(self, delta_C: float) -> None:
        """
        This allows to mock the current reading
        """
        self.temperature_C += delta_C
