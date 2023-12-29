import time
import dataclasses
from typing import List, Tuple


class Median:
    LEN = 3

    def __init__(self, initial_time_s: float):
        self.timestamps_s = [initial_time_s]

    def add(self) -> None:
        self.timestamps_s.insert(0, time.time())
        if len(self.timestamps_s) > self.LEN:
            self.timestamps_s.pop()

    @property
    def median_s(self) -> float:
        """
        return the median of the last 'MODBUS_FAILED_MEDIAN_LEN' failures.
        """
        return self.timestamps_s[len(self.timestamps_s) // 2]


    @property
    def last_s(self) -> float:
        """
        return the timestamp of the oldest (and lat) entry.
        """
        return self.timestamps_s[-1]

@dataclasses.dataclass(repr=True)
class StatusHaus:
    modbus_success_iregs: List[int] = None
    modbus_success_s: Median = dataclasses.field(default_factory=lambda: Median(0.0))
    modbus_failed_s: Median = dataclasses.field(default_factory=lambda: Median(0.1))

    def modbus_failed(self) -> None:
        self.modbus_failed_s.add()

    def modbus_success(self) -> None:
        self.modbus_success_s.add()

    @property
    def modbus_ok(self) -> bool:
        return self.modbus_success_s.last_s > self.modbus_failed_s.last_s


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
