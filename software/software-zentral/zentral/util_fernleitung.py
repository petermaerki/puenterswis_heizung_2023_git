from __future__ import annotations

import dataclasses
import typing

if typing.TYPE_CHECKING:
    from zentral.config_base import Haus
    from zentral.util_controller_haus_ladung import HausLadung

_E = 2.7182
"""
Zeitkonstante einer typischen, isolierten Heizleitung
"""

_KAPAZITAET_WASSER_J_kg_K = 4190
_FACTOR_WASSER_METALL_RETOUR = 4.0
"""
Wir berechnen nur das Wasser auf dem Hinweg.
Effektiv ist aber auch Metall und das Wasser auf dem Rückweg betroffen.
"""

FAKTOR_HAUSREIHE_PROZENT_J = 20.0 / (15.0 * 3600 * 1000)
"""
20%/15kWh
"""


def abklingen_1_0(verstrichene_Zeit_s: float) -> float:
    assert verstrichene_Zeit_s >= 0.0
    tau_s = 4.0 * 3600.0
    return _E ** -(verstrichene_Zeit_s / tau_s)


def energie_bonus_leitungssegment_J(wasser_kg: float, verstrichene_Zeit_s: float) -> float:
    heiss_C = 68.0
    kalt_C = 25.0
    energie_heiss_J = (heiss_C - kalt_C) * wasser_kg * _KAPAZITAET_WASSER_J_kg_K
    energie_J = energie_heiss_J * (abklingen_1_0(verstrichene_Zeit_s=verstrichene_Zeit_s) * 2.0 - 1.0)
    return _FACTOR_WASSER_METALL_RETOUR * energie_J


def test() -> None:
    for verstrichene_Zeit_s in [t * 3600 for t in [0, 1, 2, 3, 4, 10]]:
        print(f"Zeit {verstrichene_Zeit_s} s  Energie {energie_bonus_leitungssegment_J(wasser_kg=30.0, verstrichene_Zeit_s=verstrichene_Zeit_s)/1000.0/3600.0:0.1f} kWh")


@dataclasses.dataclass(repr=True, order=True)
class Hausreihe:
    label: str
    """
    C, D, E, F, G
    """
    grafana: int
    """
    1, 2, 3, 4
    """
    einspeisung: Hausreihe | None
    wasser_kg: float
    _last_hot_s: float = 0.0
    haeuser: list[Haus] = dataclasses.field(default_factory=list, hash=False)
    influx_reihe: str = ""
    """
    puent_F1_18-22
    <etappe>_<label><grafana>_<erstes_haus>-<letztes_haus>
    """

    def __hash__(self):
        return ord(self.label)

    def update_influx_reihe(self) -> None:
        if len(self.haeuser) == 0:
            # Could happen in case of unit test
            return
        self.haeuser.sort()
        haus_first = self.haeuser[0]
        haus_last = self.haeuser[-1]
        self.influx_reihe = f"{haus_first.config_haus.etappe.tag}_{self.label}{self.grafana}_{haus_first.config_haus.nummer}-{haus_last.config_haus.nummer}"

    def _bonus_segment_J(self, now_s: float) -> float:
        return energie_bonus_leitungssegment_J(wasser_kg=self.wasser_kg, verstrichene_Zeit_s=self._verstrichene_Zeit_s(now_s=now_s))

    def _verstrichene_Zeit_s(self, now_s: float) -> float:
        return now_s - self._last_hot_s

    def bonus_J(self, now_s: float) -> float:
        """
        Bonus über alle Segmente bis zur Heizung
        """
        hausreihe: Hausreihe | None = self
        _bonus_J = 0.0
        while hausreihe is not None:
            _bonus_J += hausreihe._bonus_segment_J(now_s=now_s)
            hausreihe = hausreihe.einspeisung
        return _bonus_J

    def set_leitung_warm(self, now_s: float) -> None:
        """
        Alle Leitungssegment bis zur Heizung als warm markieren
        """
        hausreihe: Hausreihe | None = self
        while hausreihe is not None:
            hausreihe._last_hot_s = now_s
            hausreihe = hausreihe.einspeisung


class Hausreihen(dict[str, Hausreihe]):
    def add(self, label: str, grafana: int, wasser_kg: float) -> None:
        self[label] = Hausreihe(
            label=label,
            grafana=grafana,
            einspeisung=None,
            wasser_kg=wasser_kg,
        )

    def calculate(self, now_s: float) -> EnergieHausreihe_J:
        return EnergieHausreihe_J({r: (r.bonus_J(now_s=now_s)) for r in self.values()})

    def update_influx_reihe(self) -> None:
        for hr in self.values():
            hr.update_influx_reihe()


class EnergieHausreihe_J(dict[Hausreihe, float]):
    def korrektur_prozent(self, haus_ladung: "HausLadung") -> float:
        """
        Umrechnung EnergieHausreihe_J in hausreihe_korrektur_prozent
        """
        return self[haus_ladung.hausreihe] * FAKTOR_HAUSREIHE_PROZENT_J


if __name__ == "__main__":
    test()
