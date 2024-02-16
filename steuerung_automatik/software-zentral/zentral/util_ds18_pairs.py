import dataclasses
import logging

logger = logging.getLogger(__name__)


DS18_COUNT = 8
DS18_PAIR_COUNT = DS18_COUNT // 2
DS18_OK_PERCENT = 90

DS18_REDUNDANCY_ACCEPTABLE_DIFF_C = 5.0
DS18_REDUNDANCY_WARNING_C = 1.0
DS18_REDUNDANCY_FATAL_C = 20.0
DS18_FALLBACK_C = -100.0


@dataclasses.dataclass(frozen=True)
class DS18:
    i: int
    temperature_C: float
    ds18_ok_percent: int
    """
    0: Never seen
    100: Always seen
    """

    @property
    def is_ok(self) -> bool:
        return self.ds18_ok_percent > DS18_OK_PERCENT


@dataclasses.dataclass()
class DS18_Pair:
    a: DS18
    b: DS18
    error_C: float = None
    temperature_C: float = DS18_FALLBACK_C

    def __post_init__(self):
        a_ok = self.a.is_ok
        b_ok = self.b.is_ok
        a_broken = not a_ok
        b_broken = not b_ok

        if a_broken and b_broken:
            # Both sensors broken
            self.error_C = DS18_REDUNDANCY_FATAL_C
            return

        if a_ok and b_ok:
            # Both ok
            diff_C = self.a.temperature_C - self.b.temperature_C
            if diff_C > abs(DS18_REDUNDANCY_ACCEPTABLE_DIFF_C):
                self.error_C = diff_C
            self.temperature_C = self.a.temperature_C
            return

        # Exactly one sensor broken
        self.error_C = DS18_REDUNDANCY_WARNING_C
        if a_broken:
            self.temperature_C = self.b.temperature_C

    def increment_C(self, delta_C: float) -> None:
        """
        This allows to mock the current reading
        """
        self.temperature_C += delta_C
