from __future__ import annotations

import dataclasses

from .util_controller_haus_ladung import HaeuserLadung, HausLadung


@dataclasses.dataclass(frozen=True, repr=True)
class SchaltschwellenResult:
    aus_max_prozent: float
    ein_max_prozent: float
    aus_prozent: float
    ein_prozent: float

    def open_close(self, haus_ladung: HausLadung, anhebung_prozent: float) -> tuple[bool, bool]:
        """
        Return do_close, do_open
        """
        assert isinstance(haus_ladung, HausLadung)
        assert isinstance(anhebung_prozent, float)

        do_close = haus_ladung.ladung_Prozent > self.aus_prozent
        do_open = haus_ladung.ladung_Prozent < self.ein_prozent

        if haus_ladung.next_legionellen_kill_s < 1 * 24 * 3600.0:
            if anhebung_prozent > 5.0:
                if do_close:
                    # if Legionellen fällig in weniger als 1 Tage und Anhebung > 5%:
                    # do_close = False # so lange nicht schliessen bis Legionellen erledigt
                    do_close = False

        if haus_ladung.next_legionellen_kill_s < -2 * 24 * 3600.0:
            if do_close:
                # if Legionellen überfällig mehr als 2 Tage:
                # do_close = False # so lange nicht schliessen bis Legionellen erledigt
                do_close = False

        assert not (do_close and do_open)
        return do_close, do_open


class VerbrauchLadungSchaltschwellen:
    """
    Diese Klasse entspricht dem Diagramm mit der blauen (einschalten) und der roten (ausschalten) linie.
    sandbox_fuzzy/20240806c_verbrauch_ladung.IPYNB
    """

    """kleine Hysterese fuert zu vielen Zyklen im blauen Ventil, dafuer kann die Ladung tief gehalten werden."""
    hysterese_prozent: float = 20.0
    """Die maximal moegliche Ladung. Werte von z.B. 60 bis 130%. Je hoeher, desto laengere Brennpausen aber mehr Speicherverluste."""
    ladung_maximal_prozent: float = 120.0

    def __init__(self, anhebung_prozent: float, verbrauch_max_W: float) -> None:
        assert verbrauch_max_W > 0.0
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
        if haus_ladung.verbrauch_W is None:
            return 100.0
        verbrauch_prozent = 100.0 * haus_ladung.verbrauch_W / self.verbrauch_max_W
        return max(min(verbrauch_prozent, 100.0), 0.0)

    def veraenderung(self, haus_ladung: HausLadung) -> SchaltschwellenResult:
        """
        Return: do_open, do_schliessen
        do_open: Falls das Haus unter der blauen Linie liegt.
        do_close: Falls das Haus über der roten Linie liegt.
        """

        verbrauch_prozent = self.get_verbrauch_prozent(haus_ladung=haus_ladung)
        return self.diagram(verbrauch_prozent=verbrauch_prozent)


@dataclasses.dataclass(frozen=True, repr=True)
class HauserValveVariante:
    """
    Ein Vorschlag, welche Ventile geöffnet/geschlossen werden sollen.
    """

    anhebung_prozent: float
    haeuser_valve_to_open: list[str] = dataclasses.field(default_factory=list)
    haeuser_valve_to_close: list[str] = dataclasses.field(default_factory=list)

    def to_open(self, haus_ladung: HausLadung) -> None:
        if haus_ladung.valve_open:
            return
        self.haeuser_valve_to_open.append(haus_ladung.label)

    def to_close(self, haus_ladung: HausLadung) -> None:
        if not haus_ladung.valve_open:
            return
        self.haeuser_valve_to_close.append(haus_ladung.label)

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
            verbrauch_max_W=haeuser_ladung.max_verbrauch_W,
        )
        for haus_ladung in haeuser_ladung:
            r = vls.veraenderung(haus_ladung=haus_ladung)
            do_close, do_open = r.open_close(haus_ladung=haus_ladung, anhebung_prozent=vls.anhebung_prozent)
            if do_open:
                self.hvv.to_open(haus_ladung)
            if do_close:
                self.hvv.to_close(haus_ladung)

        self.valve_open_count = haeuser_ladung.valve_open_count + self.hvv.valve_open_change


@dataclasses.dataclass
class Controller:
    """
    Abbildung der Logik in sandbox_fuzzy/20240806a_diagramm_idee.ods
    """

    last_anhebung_prozent: float
    last_valve_open_count: int

    def process(
        self,
        kessel_ein_1: int,
        ladung_zentral_prozent: float,
        haeuser_ladung: HaeuserLadung,
    ) -> None:
        hvv = self._process(
            kessel_ein_1=kessel_ein_1,
            ladung_zentral_prozent=ladung_zentral_prozent,
            haeuser_ladung=haeuser_ladung,
        )
        for valve_open in hvv.haeuser_valve_to_open:
            hsm_dezental.valve_open = True
        for valve_close in hvv.haeuser_valve_to_close:
            hsm_dezental.valve_close = True

    def _process(
        self,
        kessel_ein_1: int,
        ladung_zentral_prozent: float,
        haeuser_ladung: HaeuserLadung,
    ) -> HauserValveVariante:
        if kessel_ein_1 >= 0:
            if ladung_zentral_prozent > 80.0:
                # Tabelle Zeile 4: Loescht bald
                return self._process_1_2_loescht_bald(haeuser_ladung=haeuser_ladung)
            if ladung_zentral_prozent < -10.0:
                # Tabelle Zeile 6: brenner kommen nicht nach
                return self._process_1_2_brenner_kommen_nicht_nach(haeuser_ladung=haeuser_ladung)

        # Tabelle Zeile 8
        return self._process_leistung_ok(haeuser_ladung=haeuser_ladung)

    def _process_leistung_ok(self, haeuser_ladung: HaeuserLadung) -> HauserValveVariante:
        """
        Tabelle Zeile 8
        """
        evaluate = Evaluate(anhebung_prozent=self.last_anhebung_prozent, haeuser_ladung=haeuser_ladung)
        self.last_anhebung_prozent -= 1.0
        self.last_valve_open_count = evaluate.valve_open_count
        return evaluate.hvv

    def _process_1_2_loescht_bald(self, haeuser_ladung: HaeuserLadung) -> HauserValveVariante:
        """
        # Tabelle Zeile 4: Loescht bald
        """
        return self._find_anhebung(
            haeuser_ladung=haeuser_ladung,
            valve_open_count_soll=self.last_valve_open_count + 1,
        )

    def _process_1_2_brenner_kommen_nicht_nach(self, haeuser_ladung: HaeuserLadung) -> HauserValveVariante:
        """
        Tabelle Zeile 6: brenner kommen nicht nach
        """
        return self._find_anhebung(
            haeuser_ladung=haeuser_ladung,
            valve_open_count_soll=self.last_valve_open_count - 1,
        )

    def find_anhebung_plus_ein_haus(self, haeuser_ladung: HaeuserLadung, anhebung_prozent: float) -> HauserValveVariante:
        while True:
            if anhebung_prozent > 99.0:
                anhebung_prozent = 100.0

            evaluate = Evaluate(
                anhebung_prozent=anhebung_prozent,
                haeuser_ladung=haeuser_ladung,
            )

            if anhebung_prozent > 99.0:
                return evaluate.hvv
            if len(evaluate.hvv.haeuser_valve_to_open) > 0:
                return evaluate.hvv

            anhebung_prozent += 1.0

    def find_anhebung_minus_ein_haus(self, haeuser_ladung: HaeuserLadung, anhebung_prozent: float) -> HauserValveVariante:
        while True:
            if anhebung_prozent < 1.0:
                anhebung_prozent = 0.0

            evaluate = Evaluate(
                anhebung_prozent=float(anhebung_prozent),
                haeuser_ladung=haeuser_ladung,
            )

            if anhebung_prozent < 1.0:
                return evaluate.hvv
            if len(evaluate.hvv.haeuser_valve_to_close) > 0:
                return evaluate.hvv

            anhebung_prozent -= 1.0
