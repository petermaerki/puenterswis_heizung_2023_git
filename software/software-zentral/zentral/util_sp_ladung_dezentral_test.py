import pytest

from zentral.util_sp_ladung_dezentral import LadungBaden, LadungBodenheizung, SpTemperatur
from zentral.util_sp_ladung_zentral import SpLadungZentral


def test_sp_ladung_dezentral():
    tests = (
        (LadungBodenheizung(SpTemperatur(45, 65, 65), temperatur_aussen_C=-8.0), 100.0),
        (LadungBodenheizung(SpTemperatur(30, 40, 65), temperatur_aussen_C=-8.0), 11.538461538461538),
        (LadungBaden(SpTemperatur(45, 65, 65)), 100.0),
    )
    for ladung, expected_ladung_prozent in tests:
        assert abs(ladung.ladung_prozent - expected_ladung_prozent) < 0.1


@pytest.mark.parametrize(
    "Tsz1_C,Tsz2_C,Tsz3_C,Tsz4_C,expected_lower_level_prozent,expected_ladung_prozent",
    (
        (10.0, 10.0, 10.0, 10.0, -50, -31.25),
        (10.0, 10.0, 10.0, 64.9, -50, 9.76),
        (10.0, 10.0, 10.0, 65.1, 10, 10.05),
        (10.0, 10.0, 10.0, 70.0, 10, 12.5),
        (10.0, 10.0, 70.0, 70.0, 40, 42.5),
        (10.0, 70.0, 70.0, 70.0, 70, 72.5),
        (50.0, 70.0, 70.0, 70.0, 70, 77.5),
        (70.0, 70.0, 70.0, 70.0, 100, 104.28),
    ),
)
def test_sp_ladung(
    Tsz1_C: float,
    Tsz2_C: float,
    Tsz3_C: float,
    Tsz4_C: float,
    expected_lower_level_prozent: int,
    expected_ladung_prozent: float,
):  # pylint: disable=too-many-positional-arguments
    ladung = SpLadungZentral(Tsz1_C=Tsz1_C, Tsz2_C=Tsz2_C, Tsz3_C=Tsz3_C, Tsz4_C=Tsz4_C)
    assert ladung.ladung.lower_level_prozent == expected_lower_level_prozent
    assert abs(ladung.ladung_prozent - expected_ladung_prozent) < 0.1, (ladung.ladung_prozent, expected_ladung_prozent)


if __name__ == "__main__":
    test_sp_ladung_dezentral()
