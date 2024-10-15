from __future__ import annotations

import dataclasses
import typing

from zentral.util_fernleitung import EnergieHausreihe_J, Hausreihe

if typing.TYPE_CHECKING:
    from zentral.config_base import Haus
    from zentral.context import Context

_LADUNG_DEZENTRAL_MAX_PROZENT = 80.0
"""
Die folgenden Konstanten haben einen grossen Einfluss. 
Es geht um die Ladung der dezentralen Speicher wenn ein Brenner brennt und der zentrale Speicher zu warm ist. 
Jetzt wird Energie in die dezentralen Speicher gepumpt bis die individuelle Ladung der dezentralen Speicher 100% ist.
Werden die Häuser höher geladen, so steigen die Verluste.
Mehr Verluste in den dezentralen Speichern weil wärmer.
Mehr Verluste weil das rücklaufende Wasser von den Speichern wärmer ist und daher der Wirkungsgrad vom Brenner sinkt.
_LADUNG_DEZENTRAL_MAX_PROZENT kann z.B. von 70.0 bis 110% gewählt werden.
"""

_INDIVIDUELL_MAX_PROZENT = 100.0 * _LADUNG_DEZENTRAL_MAX_PROZENT / 100.0
"""
Haus mit maximalem Verbrauch: Individuell 100% entspricht so vielen Prozent Ladung.
"""

_INDIVIDUELL_MIN_PROZENT = 40.0 * _LADUNG_DEZENTRAL_MAX_PROZENT / 100.0
"""
Haus mit mimimalem Verbrauch: Individuell 100% entspricht so vielen Prozent Ladung.
"""


@dataclasses.dataclass(repr=True, frozen=True)
class HausLadung:
    haus: Haus
    verbrauch_avg_W: float
    max_verbrauch_avg_W: float
    ladung_prozent: float
    valve_open: bool
    next_legionellen_kill_s: float

    def __post_init__(self) -> None:
        assert self.haus.__class__.__name__ == "Haus"
        assert isinstance(self.verbrauch_avg_W, float)
        assert isinstance(self.ladung_prozent, float)
        assert isinstance(self.valve_open, bool)
        assert isinstance(self.next_legionellen_kill_s, float)
        assert self.verbrauch_avg_W >= -1e-6

    def set_valve(self, valve_open: bool) -> None:
        self.haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = valve_open

    @property
    def hausreihe(self) -> Hausreihe:
        return self.haus.config_haus.hausreihe

    @property
    def legionellen_kill_soon(self) -> bool:
        return self.next_legionellen_kill_s < 1 * 24 * 3600.0

    @property
    def legionellen_kill_urgent(self) -> bool:
        return self.next_legionellen_kill_s < -2 * 24 * 3600.0

    @property
    def ladung_individuell_prozent(self) -> float:
        return self.ladung_prozent * 100.0 / (self.verbrauch_avg_W / self.max_verbrauch_avg_W * (_INDIVIDUELL_MAX_PROZENT - _INDIVIDUELL_MIN_PROZENT) + _INDIVIDUELL_MIN_PROZENT)


class HaeuserLadung(list[HausLadung]):
    @property
    def effective_valve_open_count(self) -> int:
        return len([h for h in self if h.valve_open])

    def sort_by_ladung_indiviuell(self) -> None:
        def f_key(haus_ladung: HausLadung) -> float:
            return haus_ladung.ladung_individuell_prozent

        self.sort(key=f_key)

    def sort_by_haeuserreihe(self, hausreihen: EnergieHausreihe_J) -> None:
        def f_key(haus_ladung: HausLadung) -> tuple[float, float]:
            return -hausreihen[haus_ladung.hausreihe], haus_ladung.ladung_individuell_prozent

        self.sort(key=f_key)

    _EMERGENCY_PREVENTER_KALT_C = 60.0
    """
    * >80% Das Haus wird nicht mehr berücksichtigt für einen Ladung
    * <0% beginnt die Emergency Ladung

    60.0% wurde gewählt, da noch ein gewisser Abstand zu 80% besteht.
    Hier lohnt es sich, das Ventil zu öffnen um Nachzuladen
    """

    def calculate_emergency_preventer_bonus(self, ctx: "Context") -> dict[Hausreihe, float]:
        """
        Example:
          Hausreihe D: Bonus 2.0
          Hausreihe E: Bonus 1.0
        """
        # Zähle kalte Haeuser pro Hausreihe
        hausreihen_kalte_haeuser = {hr: 0 for hr in ctx.config_etappe.hausreihen.values()}
        for haus_ladung in self:
            if haus_ladung.ladung_individuell_prozent < self._EMERGENCY_PREVENTER_KALT_C:
                hausreihen_kalte_haeuser[haus_ladung.hausreihe] += 1

        def bonus(kalte_haeuser: int) -> float:
            """
            Die ganze Reihe soll 'komplett' warm sein, so eine emergency fuer diese Hausreihe
            fuer die nächsten Stunden verhindert und andere Hausreihen können 'in Ruhe' geheizt
            werden.
            """
            if kalte_haeuser == 1:
                return 4.0  # Grosser Bonus
            if kalte_haeuser == 2:
                return 2.0  # Kleiner Bonus
            return 1.0  # Kein Bonus

        return {hr: bonus(kalte_haeuser) for hr, kalte_haeuser in hausreihen_kalte_haeuser.items()}

    def sort_by_haeuserreihe_emergency_preventer(self, ctx: "Context", now_s: float) -> None:
        """
        1. Kriterium: emergency_preventer_bonus
           Hausreihen mit nur keinem oder zwei kalten Haeusern werden prifilegiert behandelt.
        2. EnergieHausreihe_J
        3. ladung_individuell_prozent
        """
        emergency_preventer_bonus = self.calculate_emergency_preventer_bonus(ctx=ctx)
        hausreihen = ctx.config_etappe.hausreihen.calculate(now_s=now_s, emergency_preventer_bonus=emergency_preventer_bonus)

        def f_key(haus_ladung: HausLadung) -> tuple[float, float]:
            return -hausreihen[haus_ladung.hausreihe], haus_ladung.ladung_individuell_prozent

        self.sort(key=f_key)
