from zentral.util_sp_ladung_dezentral import LadungBaden, LadungBodenheizung, SpTemperatur


def test_sp_ladung_dezentral():
    tests = (
        (LadungBodenheizung(SpTemperatur(45, 65, 65), temperatur_aussen_C=-8.0), 100.0),
        (LadungBodenheizung(SpTemperatur(30, 40, 65), temperatur_aussen_C=-8.0), 11.538461538461538),
        (LadungBaden(SpTemperatur(45, 65, 65)), 100.0),
    )
    for ladung, expected_ladung_prozent in tests:
        assert abs(ladung.ladung_prozent - expected_ladung_prozent) < 0.1


if __name__ == "__main__":
    test_sp_ladung_dezentral()
