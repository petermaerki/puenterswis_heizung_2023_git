from __future__ import annotations
import dataclasses
from .util_controller_haus_ladung import HausLadung, HaeuserLadung


@dataclasses.dataclass
class SchaltschwellenResult:
    aus_max_prozent: float
    ein_max_prozent: float
    aus_prozent: float
    ein_prozent: float

    def open_close(self, ladung_prozent: float) -> tuple[bool, bool]:
        """
        Return do_close, do_open
        """
        do_close = ladung_prozent > self.aus_prozent
        do_open = ladung_prozent < self.ein_prozent
        # print(f'Die Ladung von {self.ladung_prozent} ist groesser als die Schwelle aus {self.aus}: Haus ausschalten, valve zu')
        # print(f'Die Ladung von {self.ladung_prozent} ist kleiner als  die Schwelle ein {self.ein}: Haus einschalten, valve auf')
        assert not (do_close and do_open)
        return do_close, do_open


class VerbrauchLadungSchaltschwellen:
    """
    Diese Klasse entspricht dem Diagramm mit der blauen (einschalten) und der roten (ausschalten) linie.
    sandbox_fuzzy/20240806c_verbrauch_ladung.IPYNB
    """

    hysterese: float = 20.0
    aus_max_rechts: float = 100.0

    def __init__(self, anhebung_prozent: float, verbrauch_max_W: float) -> None:
        assert self.aus_max_rechts == 100.0
        assert verbrauch_max_W > 0.0
        self.anhebung_prozent = anhebung_prozent
        self.verbrauch_max_W = verbrauch_max_W

    @property
    def anhebung_prozent2(self) -> float:
        v = self.anhebung_prozent * (self.aus_max_rechts - self.hysterese) / 100.0
        assert 0.0 <= v <= 100.0
        return v

    def diagram(self, verbrauch_prozent: float) -> SchaltschwellenResult:
        def aus_max_prozent() -> float:
            aus_max_links = 30
            aus_max_min = 40
            steigung = (self.aus_max_rechts - aus_max_links) / 100.0
            aus = verbrauch_prozent * steigung + aus_max_links
            return max(aus, aus_max_min)

        def ein_max_prozent() -> float:
            return aus_max_prozent() - self.hysterese

        def aus_prozent() -> float:
            aus = 0 + self.hysterese + self.anhebung_prozent2
            return min(aus, aus_max_prozent())

        def ein_prozent() -> float:
            ein = 0 + self.anhebung_prozent
            return min(ein, ein_max_prozent())

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


@dataclasses.dataclass
class HauserValveVariante:
    """
    Ein Vorschlag, welche Ventile geöffnet/geschlossen werden sollen.
    """

    haeuser_valve_open: list[str] = dataclasses.field(default_factory=list)
    haeuser_valve_close: list[str] = dataclasses.field(default_factory=list)

    def oeffnen(self, haus_ladung: HausLadung) -> None:
        if haus_ladung.valve_open:
            return
        self.haeuser_valve_open.append(haus_ladung.label)

    def schliessen(self, haus_ladung: HausLadung) -> None:
        if haus_ladung.valve_open:
            self.haeuser_valve_open.append(haus_ladung.label)

    @property
    def ventile_geoeffnet_count(self) -> int:
        return len(self.haeuser_valve_open) - len(self.haeuser_valve_close)


class Evaluate:
    """
    Evaluiert eine 'anhebung_prozent'
    """

    def __init__(self, anhebung_prozent: float, haeuser_ladung: HaeuserLadung) -> None:
        self.hvv = HauserValveVariante()
        vr = VerbrauchLadungSchaltschwellen(anhebung_prozent=anhebung_prozent)
        for haus_ladung in haeuser_ladung:
            do_open, do_schliessen = vr.veraenderung(haus_ladung=haus_ladung)
            if do_open:
                self.hvv.oeffnen(haus_ladung)
            if do_schliessen:
                self.hvv.schliessen(haus_ladung)

        self.valve_open_count = (
            haeuser_ladung.valve_open_count + self.hvv.ventile_geoeffnet_count
        )


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
        for valve_open in hvv.haeuser_valve_open:
            hsm_dezental.valve_open = True
        for valve_close in hvv.haeuser_valve_close:
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
                return self._process_1_2_brenner_kommen_nicht_nach(
                    haeuser_ladung=haeuser_ladung
                )

        # Tabelle Zeile 8
        return self._process_leistung_ok(haeuser_ladung=haeuser_ladung)

    def _process_leistung_ok(
        self, haeuser_ladung: HaeuserLadung
    ) -> HauserValveVariante:
        """
        Tabelle Zeile 8
        """
        evaluate = Evaluate(
            anhebung_prozent=self.last_anhebung_prozent, haeuser_ladung=haeuser_ladung
        )
        self.last_anhebung_prozent -= 1.0
        self.last_valve_open_count = evaluate.valve_open_count
        return evaluate.hvv

    def _process_1_2_loescht_bald(
        self, haeuser_ladung: HaeuserLadung
    ) -> HauserValveVariante:
        """
        # Tabelle Zeile 4: Loescht bald
        """
        return self._find_anhebung(
            haeuser_ladung=haeuser_ladung,
            valve_open_count_soll=self.last_valve_open_count + 1,
        )

    def _process_1_2_brenner_kommen_nicht_nach(
        self, haeuser_ladung: HaeuserLadung
    ) -> HauserValveVariante:
        """
        Tabelle Zeile 6: brenner kommen nicht nach
        """
        return self._find_anhebung(
            haeuser_ladung=haeuser_ladung,
            valve_open_count_soll=self.last_valve_open_count - 1,
        )

    def _find_anhebung(
        self, haeuser_ladung: HaeuserLadung, valve_open_count_soll: int
    ) -> HauserValveVariante:

        for anhebung_prozent in range(100):
            evaluate = Evaluate(
                anhebung_prozent=anhebung_prozent,
                haeuser_ladung=haeuser_ladung,
            )
            if evaluate.valve_open_count >= valve_open_count_soll:
                self.last_valve_open_count = evaluate.valve_open_count
                return evaluate.hvv

        raise ValueError("Programming error: No solution found")
