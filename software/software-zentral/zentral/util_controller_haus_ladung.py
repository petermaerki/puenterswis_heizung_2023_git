from __future__ import annotations

import dataclasses
import typing

from zentral.util_fernleitung import EnergieHausreihe_J, Hausreihe

if typing.TYPE_CHECKING:
    from zentral.config_base import Haus

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

    def set_valve(self, valve_open: bool) -> bool:
        """
        return True: If value changed
        """
        dezentral_gpio = self.haus.status_haus.hsm_dezentral.dezentral_gpio
        changed = dezentral_gpio.relais_valve_open != valve_open
        if changed:
            dezentral_gpio.relais_valve_open = valve_open
        return changed

    @property
    def hausreihe(self) -> Hausreihe:
        return self.haus.config_haus.hausreihe

    @property
    def legionellen_kill_required(self) -> bool:
        return self.next_legionellen_kill_s < 0.0

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

    def sort_by_ladung_individuell_und_hausreihe_korrektur(self, hausreihen: EnergieHausreihe_J, hausreihe_korrektur_vorzeichen: float) -> None:
        def f_key(haus_ladung: HausLadung) -> float:
            korrektur_prozent = hausreihe_korrektur_vorzeichen * hausreihen.korrektur_prozent(haus_ladung=haus_ladung)

            # Hausreihe mit warmen Leitungen, also mit positiver Energie: korrektur_prozent ist positiv.
            return haus_ladung.ladung_individuell_prozent + korrektur_prozent

        self.sort(key=f_key)
