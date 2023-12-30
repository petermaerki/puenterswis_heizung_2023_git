import time
import dataclasses
from typing import List, Tuple


# class Median:
#     LEN = 3

#     def __init__(self, initial_time_s: float):
#         self.timestamps_s = [initial_time_s]

#     def add(self) -> None:
#         self.timestamps_s.insert(0, time.time())
#         if len(self.timestamps_s) > self.LEN:
#             self.timestamps_s.pop()

#     @property
#     def median_s(self) -> float:
#         """
#         return the median of the last 'MODBUS_FAILED_MEDIAN_LEN' failures.
#         """
#         return self.timestamps_s[len(self.timestamps_s) // 2]

#     @property
#     def last_s(self) -> float:
#         """
#         return the timestamp of the oldest (and lat) entry.
#         """
#         return self.timestamps_s[-1]


class Gauge:
    LEN = 5
    SUCCESS = 1
    FAILED = -1

    def __init__(self):
        self._success = [1]

    def _add(self, value: int) -> None:
        self._success.insert(0, value)
        if len(self._success) > self.LEN:
            self._success.pop()

    def success(self) -> None:
        self._add(self.SUCCESS)

    def failed(self) -> None:
        self._add(self.FAILED)

    @property
    def ok(self) -> float:
        """
        return true if the where more success than failed
        """
        return sum(self._success) > 0


@dataclasses.dataclass(repr=True)
class StatusHaus:
    modbus_success_iregs: List[int] = None
    modbus_gauge: Gauge = dataclasses.field(default_factory=lambda: Gauge())
    # modbus_success_s: Median = dataclasses.field(default_factory=lambda: Median(0.0))
    # modbus_failed_s: Median = dataclasses.field(default_factory=lambda: Median(0.1))

    def modbus_failed(self) -> None:
        self.modbus_gauge.failed()

    def modbus_success(self) -> None:
        self.modbus_gauge.success()

    @property
    def modbus_ok(self) -> bool:
        return self.modbus_gauge.ok


@dataclasses.dataclass(frozen=True, repr=True)
class ConfigHaus:
    nummer: int
    modbus_client_id: int
    addresse: str
    bewohner: str
    bauabschnitt: "ConfigBauabschnitt" = dataclasses.field(default_factory=list)


@dataclasses.dataclass(repr=True)
class Haus:
    config_haus: ConfigHaus
    status_haus: StatusHaus = None

    def __post_init__(self):
        self.status_haus = StatusHaus()
        self.config_haus.bauabschnitt.append_haus(self)


@dataclasses.dataclass(frozen=True, repr=True)
class ConfigBauabschnitt:
    name: str
    haeuser: Tuple[Haus] = dataclasses.field(default_factory=list, repr=False)

    def append_haus(self, haus: Haus):
        self.haeuser.append(haus)
