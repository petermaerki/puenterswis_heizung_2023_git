import dataclasses
from typing import List, Tuple
from src.hsm_dezentral import HsmDezentral


class StatusHaus:
    def __init__(self):
        self.hsm_dezentral = HsmDezentral()

        # modbus_success_s: Median = dataclasses.field(default_factory=lambda: Median(0.0))
        # modbus_failed_s: Median = dataclasses.field(default_factory=lambda: Median(0.1))

    # def modbus_failed(self) -> None:
    #     # self.modbus_failed_s.add()
    #     self.modbus_history.failed()

    # def modbus_success(self) -> None:
    #     # self.modbus_success_s.add()
    #     self.modbus_history.success()

    # @property
    # def modbus_ok(self) -> bool:
    #     return self.modbus_history.ok
    #     # return self.modbus_success_s.last_s > self.modbus_failed_s.last_s


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
