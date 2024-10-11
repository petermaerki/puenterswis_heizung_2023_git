from __future__ import annotations

import dataclasses

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


@dataclasses.dataclass(repr=True, order=True, unsafe_hash=True)
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
            _bonus_J += self._bonus_segment_J(now_s=now_s)
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

    def calculate(self, now_s: float, emergency_preventer_bonus: dict[Hausreihe, float] | None = None) -> EnergieHausreihe_J:
        if emergency_preventer_bonus is None:
            emergency_preventer_bonus = {}
        return EnergieHausreihe_J({r: (emergency_preventer_bonus.get(r, 1.0) * r.bonus_J(now_s=now_s)) for r in self.values()})


class EnergieHausreihe_J(dict[Hausreihe, float]):
    pass


if __name__ == "__main__":
    test()
