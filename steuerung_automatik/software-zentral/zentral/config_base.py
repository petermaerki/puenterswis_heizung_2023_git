import dataclasses
from typing import Dict, Optional, Tuple
from enum import IntEnum

from zentral.hsm_dezentral import HsmDezentral


class StatusHaus:
    def __init__(self, haus: "Haus"):
        self.hsm_dezentral = HsmDezentral(haus=haus)

    def get_grafana_fields(self) -> Dict[str, float]:
        return {}

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
    addresse: str = dataclasses.field(hash=False, compare=False)
    bewohner: str = dataclasses.field(hash=False, compare=False)
    bauetappe: "ConfigEtappe" = dataclasses.field(hash=False, compare=False)

    @property
    def modbus_server_id(self) -> int:
        return self.nummer + 100

    # def __hash__(self):
    #     return self.haus.nummer


@dataclasses.dataclass(repr=True, order=True)
class Haus:
    config_haus: ConfigHaus = dataclasses.field(hash=True, compare=False)
    # status_haus: StatusHaus = dataclasses.field(default_factory=lambda: StatusHaus(), hash=False, compare=False)
    status_haus: Optional[StatusHaus] = dataclasses.field(default=None, hash=False, compare=False)

    def __post_init__(self):
        self.config_haus.bauetappe.append_haus(self)
        self.status_haus = StatusHaus(self)

    def __hash__(self):
        return self.config_haus.nummer

    @property
    def label(self) -> str:
        return f"Haus {self.config_haus.nummer}(modbus={self.config_haus.modbus_server_id})"

    @property
    def grafana_tag(self) -> str:
        return f"haus_{self.config_haus.nummer:02d}"


@dataclasses.dataclass(repr=True)
class ConfigEtappe:
    tag: str
    name: str
    dict_haeuser: Dict[int, Haus] = dataclasses.field(default_factory=dict, repr=False)
    haus_enum: IntEnum | None = None

    def append_haus(self, haus: Haus):
        self.dict_haeuser[haus.config_haus.nummer] = haus
        self.haus_enum = IntEnum(
            "haus_enum",
            {f"HAUS_{h.config_haus.nummer}": h.config_haus.nummer for h in self.dict_haeuser.values()},
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
        raise AttributeError(f"Haus mit modbus_server_id {modbus_server_id} nicht gefunden")
