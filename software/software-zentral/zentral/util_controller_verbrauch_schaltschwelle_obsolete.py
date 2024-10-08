from __future__ import annotations

import dataclasses

from .util_controller_haus_ladung import HaeuserLadung, HausLadung


@dataclasses.dataclass(frozen=True, repr=True)
class SchaltschwellenResult:
    aus_max_prozent: float
    ein_max_prozent: float
    aus_prozent: float
    ein_prozent: float

    def open_close(self, haus_ladung: HausLadung, anhebung_prozent: float) -> tuple[bool, bool, bool]:
        """
        Return do_close, do_open, do_legionellen_kill
        """
        assert isinstance(haus_ladung, HausLadung)
        assert isinstance(anhebung_prozent, float)

        legionellen_kill_in_progress = False
        do_close = haus_ladung.ladung_prozent > self.aus_prozent
        do_open = haus_ladung.ladung_prozent < self.ein_prozent

        if haus_ladung.next_legionellen_kill_s < 1 * 24 * 3600.0:
            if anhebung_prozent > 5.0:
                if do_close:
                    # if Legionellen fällig in weniger als 1 Tage und Anhebung > 5%:
                    # do_close = False # so lange nicht schliessen bis Legionellen erledigt
                    do_close = False
                    legionellen_kill_in_progress = True

        if haus_ladung.next_legionellen_kill_s < -2 * 24 * 3600.0:
            if do_close:
                # if Legionellen überfällig mehr als 2 Tage:
                # do_close = False # so lange nicht schliessen bis Legionellen erledigt
                do_close = False
                legionellen_kill_in_progress = True

        assert not (do_close and do_open)
        return do_close, do_open, legionellen_kill_in_progress


class VerbrauchLadungSchaltschwellen:
    """
    Diese Klasse entspricht dem Diagramm mit der blauen (einschalten) und der roten (ausschalten) linie.
    sandbox_fuzzy/20240806c_verbrauch_ladung.IPYNB
    """

    hysterese_prozent: float = 20.0
    """kleine Hysterese fuert zu vielen Zyklen im blauen Ventil, dafuer kann die Ladung tief gehalten werden."""
    ladung_maximal_prozent: float = 120.0
    """Die maximal moegliche Ladung. Werte von z.B. 60 bis 130%. Je hoeher, desto laengere Brennpausen aber mehr Speicherverluste."""

    def __init__(self, anhebung_prozent: float, verbrauch_max_W: float) -> None:
        assert isinstance(anhebung_prozent, float)
        assert isinstance(verbrauch_max_W, float)
        assert verbrauch_max_W > 0.0
        assert 0.0 <= anhebung_prozent <= 100.0
        assert verbrauch_max_W >= 0.0

        self.anhebung_prozent = anhebung_prozent
        self.verbrauch_max_W = verbrauch_max_W

    @property
    def anhebung_prozent2(self) -> float:
        v = self.anhebung_prozent * (self.ladung_maximal_prozent - self.hysterese_prozent) / 100.0
        assert 0.0 <= v <= 100.0
        return v

    def diagram(self, verbrauch_prozent: float) -> SchaltschwellenResult:
        def aus_max_prozent() -> float:
            aus_max_links_prozent = 30
            aus_max_min_prozent = 40
            steigung = (self.ladung_maximal_prozent - aus_max_links_prozent) / 100.0
            aus_prozent = verbrauch_prozent * steigung + aus_max_links_prozent
            return max(aus_prozent, aus_max_min_prozent)

        def ein_max_prozent() -> float:
            return aus_max_prozent() - self.hysterese_prozent

        def aus_prozent() -> float:
            aus_prozent = 0 + self.hysterese_prozent + self.anhebung_prozent2
            return min(aus_prozent, aus_max_prozent())

        def ein_prozent() -> float:
            ein_prozent = 0 + self.anhebung_prozent
            return min(ein_prozent, ein_max_prozent())

        r = SchaltschwellenResult(
            aus_max_prozent=aus_max_prozent(),
            ein_max_prozent=ein_max_prozent(),
            aus_prozent=aus_prozent(),
            ein_prozent=ein_prozent(),
        )
        return r

    def get_verbrauch_prozent(self, haus_ladung: HausLadung) -> float:
        if haus_ladung.verbrauch_avg_W is None:
            return 100.0
        verbrauch_prozent = 100.0 * haus_ladung.verbrauch_avg_W / self.verbrauch_max_W
        return max(min(verbrauch_prozent, 100.0), 0.0)

    def veraenderung(self, haus_ladung: HausLadung) -> SchaltschwellenResult:
        """
        Return: do_open, do_schliessen
        do_open: Falls das Haus unter der blauen Linie liegt.
        do_close: Falls das Haus über der roten Linie liegt.
        """

        verbrauch_prozent = self.get_verbrauch_prozent(haus_ladung=haus_ladung)
        return self.diagram(verbrauch_prozent=verbrauch_prozent)


@dataclasses.dataclass(repr=True)
class HauserValveVariante:
    """
    Ein Vorschlag, welche Ventile geöffnet/geschlossen werden sollen.
    """

    haeuser_valve_to_open: list[int] = dataclasses.field(default_factory=list)
    haeuser_valve_to_close: list[int] = dataclasses.field(default_factory=list)

    def to_open(self, haus_ladung: HausLadung) -> None:
        if haus_ladung.valve_open:
            return
        self.haeuser_valve_to_open.append(haus_ladung.nummer)

    def to_close(self, haus_ladung: HausLadung) -> None:
        if not haus_ladung.valve_open:
            return
        self.haeuser_valve_to_close.append(haus_ladung.nummer)

    @property
    def valve_open_change(self) -> int:
        """
        Postive: More valves to_open then to_close
        Negative: More valves to_close then to_open
        """
        return len(self.haeuser_valve_to_open) - len(self.haeuser_valve_to_close)


class Evaluate:
    """
    Evaluiert eine 'anhebung_prozent'
    """

    def __init__(self, anhebung_prozent: float, haeuser_ladung: HaeuserLadung) -> None:
        assert isinstance(anhebung_prozent, float)
        assert isinstance(haeuser_ladung, HaeuserLadung)

        self.hvv = HauserValveVariante(anhebung_prozent=anhebung_prozent)
        vls = VerbrauchLadungSchaltschwellen(
            anhebung_prozent=anhebung_prozent,
            verbrauch_max_W=haeuser_ladung.max_verbrauch_avg_W,
        )
        for haus_ladung in haeuser_ladung:
            r = vls.veraenderung(haus_ladung=haus_ladung)
            do_close, do_open, legionellen_kill_in_progress = r.open_close(haus_ladung=haus_ladung, anhebung_prozent=vls.anhebung_prozent)
            if legionellen_kill_in_progress:
                self.hvv.legionellen_kill_in_progress = True
            if do_open:
                self.hvv.to_open(haus_ladung)
            if do_close:
                self.hvv.to_close(haus_ladung)

        self.valve_open_count = haeuser_ladung.valve_open_count + self.hvv.valve_open_change
