"""
A)
  List of incr,decr,ladung_prozent: Übergänge anzeigen
B)
  List of events
    Zeit, inc/dec, ladung_prozent
C)
  List of (zeit, ladung_prozent)
"""

import dataclasses
import pathlib

import pytest

from zentral.constants import add_path_software_zero_dezentral
from zentral.util_modulation_soll import Modulation, ModulationBrenner, ModulationSoll
from zentral.util_pytest_git import assert_git_unchanged

add_path_software_zero_dezentral()


DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTRESULTS = DIRECTORY_OF_THIS_FILE / "util_modulation_soll_testresults"


@dataclasses.dataclass(frozen=True, repr=True)
class Tick:
    modulation_erhoehen: bool = False
    modulation_reduzieren: bool = False
    brenner_zuenden: bool = False
    brenner_loeschen: bool = False
    comment: str | None = None

    def __post_init__(self):
        assert isinstance(self.modulation_erhoehen, bool)
        assert isinstance(self.modulation_reduzieren, bool)
        assert isinstance(self.brenner_zuenden, bool)
        assert isinstance(self.brenner_loeschen, bool)
        assert isinstance(self.comment, str | None)

    @property
    def short(self) -> str:
        s = ""
        if self.modulation_erhoehen:
            s += "m+"
        if self.modulation_reduzieren:
            s += "m-"
        if self.brenner_zuenden:
            s += "b+"
        if self.brenner_loeschen:
            s += "b-"
        if self.comment is not None:
            s += f" {self.comment}"
        return s


@dataclasses.dataclass(frozen=True, repr=True)
class Ttestparam:
    label: str
    modulation0: Modulation
    modulation1: Modulation
    ticks: list[Tick]

    @property
    def pytest_id(self) -> str:
        return self.label

    @property
    def filename_stem(self) -> pathlib.Path:
        f = f"test_{self.label}"
        return DIRECTORY_TESTRESULTS / f

    @property
    def filename_txt(self) -> pathlib.Path:
        return self.filename_stem.with_suffix(".txt")


_TESTPARAMS = [
    Ttestparam(
        label="Around-the-world",
        modulation0=Modulation.OFF,
        modulation1=Modulation.OFF,
        ticks=[
            Tick(modulation_erhoehen=True, comment="Modulation nicht erhoehen, da noch kein Brenner brennt"),
            Tick(brenner_zuenden=True, comment="Erster Brenner zuenden."),
            *5 * [Tick(modulation_erhoehen=True, comment="Modulation des ersten Brenners erhöhen bis 100%")],
            *5 * [Tick(modulation_reduzieren=True, comment="Modulation des ersten Brenners absenken")],
            *3 * [Tick(brenner_zuenden=True, comment="Zweiten Brenner zuenden.")],
            *5 * [Tick(modulation_erhoehen=True, comment="Modulation beider Brenner erhöhen bis 100%")],
            *5 * [Tick(modulation_reduzieren=True, comment="Modulation beider Brenner reduzieren auf 30%")],
            *6 * [Tick(modulation_erhoehen=True, comment="Modulation beider Brenner erhöhen bis 100%")],
            *6 * [Tick(brenner_loeschen=True, comment="Alle Brenner loeschen.")],
        ],
    ),
]


def run_modulation_soll(testparam: Ttestparam) -> None:
    testparam.filename_txt.parent.mkdir(parents=True, exist_ok=True)

    with testparam.filename_txt.open("w") as f:
        modulation_soll = ModulationSoll(modulation0=testparam.modulation0, modulation1=testparam.modulation1)
        for tick in testparam.ticks:
            modulation_soll.actiontimer.cancel()

            if tick.modulation_erhoehen:
                modulation_soll.modulation_erhoehen()
            if tick.modulation_reduzieren:
                modulation_soll.modulation_reduzieren()
            if tick.brenner_zuenden:
                modulation_soll.brenner_zuenden()
            if tick.brenner_loeschen:
                modulation_soll.brenner_loeschen()
            f.write(f"{modulation_soll.short}  \u2190  {tick.short}\n")

    assert_git_unchanged(testparam.filename_txt)


@pytest.mark.parametrize("testparam", _TESTPARAMS, ids=lambda testparam: testparam.pytest_id)
def test_modulation_soll(testparam: Ttestparam):
    run_modulation_soll(testparam=testparam)


@pytest.mark.parametrize(
    "modulation_prozent,modbus_FAx_UW_TEMP_ON_C,expected_modbus_FAx_REGEL_TEMP_C",
    (
        (Modulation.MAX, 76.0, 85.0),
        (Modulation.MEDIUM, 76.0, 78.8),
        (Modulation.MIN, 76.0, 69.34),
    ),
)
def test_modulation_calculate(modulation_prozent: Modulation, modbus_FAx_UW_TEMP_ON_C: float, expected_modbus_FAx_REGEL_TEMP_C: float):
    brenner = ModulationBrenner(idx0=0, modulation=modulation_prozent)
    result_C = brenner.calculate_modbus_FAx_REGEL_TEMP_C(modbus_FAx_UW_TEMP_ON_C=modbus_FAx_UW_TEMP_ON_C)
    assert abs(result_C - expected_modbus_FAx_REGEL_TEMP_C) < 0.1, (result_C, expected_modbus_FAx_REGEL_TEMP_C)


def test_modulation_erhoehen() -> None:
    m = Modulation.OFF
    m = m.erhoeht
    assert m is Modulation.MIN
    m = m.erhoeht
    assert m is Modulation.MEDIUM
    m = m.erhoeht
    assert m is Modulation.MAX
    m = m.erhoeht
    assert m is Modulation.MAX


def test_modulation_absenken() -> None:
    m = Modulation.MAX
    m = m.abgesenkt
    assert m is Modulation.MEDIUM
    m = m.abgesenkt
    assert m is Modulation.MIN
    m = m.abgesenkt
    assert m is Modulation.OFF
    m = m.abgesenkt
    assert m is Modulation.OFF


def main():
    for testparam in _TESTPARAMS:
        run_modulation_soll(testparam=testparam)


if __name__ == "__main__":
    main()
