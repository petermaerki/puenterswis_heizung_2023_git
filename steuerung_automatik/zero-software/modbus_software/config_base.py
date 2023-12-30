import dataclasses
from typing import List, Tuple

from util_history2 import History2

@dataclasses.dataclass(repr=True)
class StatusHaus:
    modbus_success_iregs: List[int] = None
    modbus_history: History2 = dataclasses.field(default_factory=lambda: History2())
    # modbus_success_s: Median = dataclasses.field(default_factory=lambda: Median(0.0))
    # modbus_failed_s: Median = dataclasses.field(default_factory=lambda: Median(0.1))


@dataclasses.dataclass(frozen=True, repr=True)
class ConfigHaus:
    nummer: int
    modbus_client_id: int
    addresse: str
    bewohner: str
    bauetappe: "ConfigBauetappe" = dataclasses.field(default_factory=list)


@dataclasses.dataclass(repr=True)
class Haus:
    config_haus: ConfigHaus
    status_haus: StatusHaus = None

    def __post_init__(self):
        self.status_haus = StatusHaus()
        self.config_haus.bauetappe.append_haus(self)


@dataclasses.dataclass(frozen=True, repr=True)
class ConfigBauetappe:
    name: str
    haeuser: Tuple[Haus] = dataclasses.field(default_factory=list, repr=False)

    def append_haus(self, haus: Haus):
        self.haeuser.append(haus)
