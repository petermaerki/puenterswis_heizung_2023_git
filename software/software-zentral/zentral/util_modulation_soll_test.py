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
from zentral.util_modulation_soll import ModulationBrenner, ModulationSoll

add_path_software_zero_dezentral()


DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTRESULTS = DIRECTORY_OF_THIS_FILE / "util_modulation_soll_testresults"


@dataclasses.dataclass(frozen=True, repr=True)
class Tick:
    ladung_prozent: float
    comment: str | None = None

    def __post_init__(self):
        assert isinstance(self.ladung_prozent, float)
        assert isinstance(self.comment, str | None)

    @property
    def short(self) -> str:
        s = f" {self.ladung_prozent:5.1f}%"
        if self.comment is not None:
            s += f" {self.comment}"
        return s


@dataclasses.dataclass(frozen=True, repr=True)
class Ttestparam:
    label: str
    modulation0: int
    modulation1: int
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
        modulation0=0,
        modulation1=0,
        ticks=[
            Tick(ladung_prozent=5.0, comment="Kein Einschalten da genug warm."),
            Tick(ladung_prozent=-1.0, comment="Einschalten da kalt."),
            Tick(ladung_prozent=20.0, comment="Keine Änderung da Ladung ok"),
            *3 * [Tick(ladung_prozent=3.0, comment="Increment bis ein Brenner auf 100%")],
            Tick(ladung_prozent=-1.0, comment="Zweiter Brenner einschalten"),
            *3 * [Tick(ladung_prozent=3.0, comment="Increment bis zweiter Brenner auf 100%")],
            *5 * [Tick(ladung_prozent=70.0, comment="Decrement bis beide Brenner auf 30%")],
            *2 * [Tick(ladung_prozent=96.0, comment="Ersten Brenner ausschalten")],
            *2 * [Tick(ladung_prozent=101.0, comment="Zweiten Brenner ausschalten")],
        ],
    ),
]


def run_modulation_soll(testparam: Ttestparam) -> None:
    testparam.filename_txt.parent.mkdir(parents=True, exist_ok=True)

    with testparam.filename_txt.open("w") as f:
        modulation_soll = ModulationSoll(modulation0=testparam.modulation0, modulation1=testparam.modulation1)
        for tick in testparam.ticks:
            modulation_soll.tick(ladung_prozent=tick.ladung_prozent, manual_mode=False)
            f.write(f"{modulation_soll.short} \u2190 {tick.short}\n")


@pytest.mark.parametrize("testparam", _TESTPARAMS, ids=lambda testparam: testparam.pytest_id)
def test_controller_haeuser(testparam: Ttestparam):
    run_modulation_soll(testparam=testparam)


@pytest.mark.parametrize(
    "modulation_prozent,modbus_FAx_UW_TEMP_ON_C,expected_modbus_FAx_REGEL_TEMP_C",
    (
        (100, 76.0, 85.0),
        (65, 76.0, 78.8),
        (30, 76.0, 69.34),
    ),
)
def test_modulation_calculate(modulation_prozent: int, modbus_FAx_UW_TEMP_ON_C: float, expected_modbus_FAx_REGEL_TEMP_C: float):
    brenner = ModulationBrenner(idx0=0, idx0_modulation=ModulationBrenner.get_idx(modulation=modulation_prozent))
    result_C = brenner.calculate_modbus_FAx_REGEL_TEMP_C(modbus_FAx_UW_TEMP_ON_C=modbus_FAx_UW_TEMP_ON_C)
    assert abs(result_C - expected_modbus_FAx_REGEL_TEMP_C) < 0.1, (result_C, expected_modbus_FAx_REGEL_TEMP_C)


def main():
    for testparam in _TESTPARAMS:
        run_modulation_soll(testparam=testparam)


if __name__ == "__main__":
    main()
