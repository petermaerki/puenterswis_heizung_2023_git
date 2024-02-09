import dataclasses
from typing import Dict, Tuple
from enum import IntEnum
from zentral.hsm_dezentral import HsmDezentral


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


@dataclasses.dataclass(frozen=True, repr=True, order=True)
class ConfigHaus:
    nummer: int = dataclasses.field(hash=True, compare=True)
    modbus_server_id: int = dataclasses.field(hash=False, compare=False)
    addresse: str = dataclasses.field(hash=False, compare=False)
    bewohner: str = dataclasses.field(hash=False, compare=False)
    bauabschnitt: "ConfigBauabschnitt" = dataclasses.field(hash=False, compare=False)

    # def __hash__(self):
    #     return self.haus.nummer


@dataclasses.dataclass(repr=True, order=True)
class Haus:
    config_haus: ConfigHaus = dataclasses.field(hash=True, compare=False)
    status_haus: StatusHaus = dataclasses.field(
        default_factory=lambda: StatusHaus(), hash=False, compare=False
    )

    def __post_init__(self):
        # self.status_haus = StatusHaus()
        self.config_haus.bauabschnitt.append_haus(self)

    def __hash__(self):
        return self.config_haus.nummer


@dataclasses.dataclass(repr=True)
class ConfigBauabschnitt:
    name: str
    dict_haeuser: Dict[int, Haus] = dataclasses.field(default_factory=dict, repr=False)
    haus_enum: IntEnum | None = None

    def append_haus(self, haus: Haus):
        self.dict_haeuser[haus.config_haus.nummer] = haus
        self.haus_enum = IntEnum(
            "haus_enum",
            {
                f"HAUS_{h.config_haus.nummer}": h.config_haus.nummer
                for h in self.dict_haeuser.values()
            },
        )

    @property
    def haeuser(self) -> Tuple[Haus]:
        return sorted(self.dict_haeuser.values())

    def get_haus_by_nummer(self, nummer: int) -> Haus:
        for haus in self.haeuser:
            if haus.config_haus.nummer == nummer:
                return haus
        raise AttributeError(f"Haus mit nummer {nummer} nicht gefunden")

    def get_haus_by_modbus_server_id(self, modbus_server_id: int) -> Haus:
        for haus in self.haeuser:
            if haus.config_haus.modbus_server_id == modbus_server_id:
                return haus
        raise AttributeError(
            f"Haus mit modbus_server_id {modbus_server_id} nicht gefunden"
        )
