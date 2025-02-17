from __future__ import annotations

import dataclasses
from enum import IntEnum
from typing import Dict, List, Union

from zentral.constants import ETAPPE_TAG_BOCHS, ETAPPE_TAG_PUENT, HsmZentralStartupMode
from zentral.hsm_dezentral import HsmDezentral
from zentral.util_fernleitung import Hausreihe, Hausreihen
from zentral.util_sp_ladung_dezentral import SpTemperatur
from zentral.util_uploadinterval import UploadInterval

MODBUS_OFFSET_HAUS = 100


class StatusHaus:
    def __init__(self, haus: "Haus"):
        self.hsm_dezentral = HsmDezentral(haus=haus)
        self.interval_haus_temperatures = UploadInterval(interval_s=1 * 60)

    def get_influx_fields(self) -> Dict[str, float]:
        return {}


@dataclasses.dataclass(frozen=True, repr=True, order=True)
class ConfigHaus:
    nummer: int = dataclasses.field(hash=True, compare=True)
    addresse: str = dataclasses.field(hash=False, compare=False)
    bewohner: str = dataclasses.field(hash=False, compare=False)
    etappe: "ConfigEtappe" = dataclasses.field(hash=False, compare=False)
    mbus_address: str = dataclasses.field(hash=False, compare=False)
    hausreihe: Hausreihe = dataclasses.field(hash=False, compare=False)

    @property
    def haus_maerki(self) -> bool:
        "Haus Maerki kann Wärme rückspeisen"
        return self.nummer == 13

    @property
    def haus_seinet(self) -> bool:
        "Haus Seinet kann Wärme von haus_maerki aufnehmen"
        return self.nummer == 12

    @property
    def modbus_server_id(self) -> int:
        return self.nummer + MODBUS_OFFSET_HAUS

    @property
    def haus_idx0(self) -> int:
        assert self.etappe.lowest_haus_nummer is not None
        idx0 = self.nummer - self.etappe.lowest_haus_nummer
        assert idx0 >= 0
        return idx0

    @property
    def influx_offset05(self) -> float:
        """
        A offset in the range from 0.0 to 0.5 for each haus.
        In Grafana, all häuser will be visible line by line.
        """
        offset_total = 0.5
        anzahl_haeuser = len(self.etappe.dict_haeuser)
        return self.haus_idx0 * offset_total / max(1, (anzahl_haeuser - 1))


@dataclasses.dataclass(repr=True, order=True)
class Haus:
    config_haus: ConfigHaus = dataclasses.field(hash=True, compare=False)
    status_haus_or_None: Union[StatusHaus, None] = dataclasses.field(default=None, hash=False, compare=False)

    def __post_init__(self):
        self.config_haus.etappe.append_haus(self)
        self.status_haus_or_None = StatusHaus(self)
        self.config_haus.hausreihe.haeuser.append(self)

    def __hash__(self):
        return self.config_haus.nummer

    @property
    def status_haus(self) -> StatusHaus:
        assert self.status_haus_or_None is not None
        return self.status_haus_or_None

    @property
    def label(self) -> str:
        return f"Haus {self.config_haus.nummer}(modbus={self.config_haus.modbus_server_id})"

    @property
    def influx_tag(self) -> str:
        return f"haus_{self.config_haus.nummer:02d}"

    def get_sp_temperatur(self) -> SpTemperatur | None:
        """
        Return SpTemperatur
        Return None:
          * If hsm_dezentral != state_ok
          * I other contidtions fail
        """
        hsm_dezentral = self.status_haus.hsm_dezentral
        if not hsm_dezentral.is_state(hsm_dezentral.state_ok):
            return None
        modbus_iregs_all = hsm_dezentral.modbus_iregs_all
        if modbus_iregs_all is None:
            return None
        sp_temperatur = modbus_iregs_all.sp_temperatur
        if sp_temperatur is None:
            return None
        return sp_temperatur


@dataclasses.dataclass(repr=True)
class ConfigEtappe:
    tag: str
    name: str
    hausreihen: Hausreihen
    dict_haeuser: Dict[int, Haus] = dataclasses.field(default_factory=dict, repr=False)
    haus_enum: IntEnum | None = None
    lowest_haus_nummer: int | None = None
    hsm_mode: HsmZentralStartupMode = HsmZentralStartupMode.AutoSimple

    @property
    def is_puent(self) -> bool:
        """
        Wird nur in der Inbetriebnahme verwendet.
        Sind beide Heizungen umgebaut: Dieses property löschen!
        """
        return self.tag == ETAPPE_TAG_PUENT

    @property
    def is_bochs(self) -> bool:
        """
        Wird nur in der Inbetriebnahme verwendet.
        Sind beide Heizungen umgebaut: Dieses property löschen!
        """
        return self.tag == ETAPPE_TAG_BOCHS

    @property
    def brenner_einzeln_leistung_W(self) -> float:
        """
        Wir haben PESK41, also 41 kW. Leistung durch Verstopfen von Rohren reduziert auf 36 kW?
        Gemessen und geschätzt: 30kW
        """
        return 30000.0

    def append_haus(self, haus: Haus):
        assert self.lowest_haus_nummer is None
        self.dict_haeuser[haus.config_haus.nummer] = haus
        self.haus_enum = IntEnum(  # type: ignore[misc]
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

    def get_haus_by_modbus_server_id(self, modbus_server_id: int) -> Haus:
        assert self.lowest_haus_nummer is not None

        for haus in self.dict_haeuser.values():
            if haus.config_haus.modbus_server_id == modbus_server_id:
                return haus
        raise AttributeError(f"Haus mit modbus_server_id {modbus_server_id} nicht gefunden")
