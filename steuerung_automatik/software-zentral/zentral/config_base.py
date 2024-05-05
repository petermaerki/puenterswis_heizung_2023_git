import dataclasses
from typing import Dict, List, Union
from enum import IntEnum

from zentral.constants import HsmZentralStartupMode
from zentral.hsm_dezentral import HsmDezentral
from zentral.util_uploadinterval import UploadInterval


class StatusHaus:
    def __init__(self, haus: "Haus"):
        self.hsm_dezentral = HsmDezentral(haus=haus)
        self.interval_haus_temperatures = UploadInterval(interval_s=1 * 60)

    def get_influx_fields(self) -> Dict[str, float]:
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
    etappe: "ConfigEtappe" = dataclasses.field(hash=False, compare=False)

    @property
    def modbus_server_id(self) -> int:
        return self.nummer + 100

    @property
    def haus_idx0(self) -> int:
        idx0 = self.nummer - self.etappe.lowest_haus_nummer
        assert idx0 >= 0
        return idx0

    # def __hash__(self):
    #     return self.haus.nummer

    @property
    def influx_offset08(self) -> float:
        """
        A offset in the range from 0.0 to 0.8 for each haus.
        In Grafana, all häuser will be visible line by line.
        """
        offset_total = 0.8
        anzahl_haeuser = len(self.etappe.dict_haeuser)
        return self.haus_idx0 * offset_total / max(1, (anzahl_haeuser - 1))


@dataclasses.dataclass(repr=True, order=True)
class Haus:
    config_haus: ConfigHaus = dataclasses.field(hash=True, compare=False)
    # status_haus: StatusHaus = dataclasses.field(default_factory=lambda: StatusHaus(), hash=False, compare=False)
    status_haus: Union[StatusHaus, None] = dataclasses.field(default=None, hash=False, compare=False)

    def __post_init__(self):
        self.config_haus.etappe.append_haus(self)
        self.status_haus = StatusHaus(self)

    def __hash__(self):
        return self.config_haus.nummer

    @property
    def label(self) -> str:
        return f"Haus {self.config_haus.nummer}(modbus={self.config_haus.modbus_server_id})"

    @property
    def influx_tag(self) -> str:
        return f"haus_{self.config_haus.nummer:02d}"


@dataclasses.dataclass(repr=True)
class ConfigEtappe:
    tag: str
    name: str
    dict_haeuser: Dict[int, Haus] = dataclasses.field(default_factory=dict, repr=False)
    haus_enum: IntEnum | None = None
    lowest_haus_nummer: int | None = None
    hsm_mode: HsmZentralStartupMode = HsmZentralStartupMode.AutoSimple

    def append_haus(self, haus: Haus):
        assert self.lowest_haus_nummer is None
        self.dict_haeuser[haus.config_haus.nummer] = haus
        self.haus_enum = IntEnum(
            "haus_enum",
            {f"HAUS_{h.config_haus.nummer}": h.config_haus.nummer for h in self.dict_haeuser.values()},
        )

    def init(self) -> None:
        assert self.lowest_haus_nummer is None

        self.lowest_haus_nummer = 1000
        for haus in self.dict_haeuser.values():
            self.lowest_haus_nummer = min(self.lowest_haus_nummer, haus.config_haus.nummer)

    @property
    def haeuser(self) -> List[Haus]:
        return sorted(self.dict_haeuser.values())

    @property
    def hausnummern(self) -> List[int]:
        return sorted([haus.config_haus.nummer for haus in self.dict_haeuser.values()])

    def get_haus_by_nummer(self, nummer: int) -> Haus:
        assert self.lowest_haus_nummer is not None

        try:
            return self.dict_haeuser[nummer]
        except KeyError as ex:
            raise AttributeError(f"Haus mit nummer {nummer} nicht gefunden") from ex

    def get_haus_by_modbus_server_id(self, modbus_server_id: int) -> Haus:
        assert self.lowest_haus_nummer is not None

        for haus in self.dict_haeuser.values():
            if haus.config_haus.modbus_server_id == modbus_server_id:
                return haus
        raise AttributeError(f"Haus mit modbus_server_id {modbus_server_id} nicht gefunden")
