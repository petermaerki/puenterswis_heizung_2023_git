from zentral.util_sp_ladung import LadungBaden, LadungHeizung, SpTemperatur


def test_sp_ladung():
    tests = (
        (LadungHeizung(SpTemperatur(45, 65, 65)), 100.0),
        (LadungHeizung(SpTemperatur(30, 40, 65)), 11.538461538461538),
        (LadungBaden(SpTemperatur(45, 65, 65)), 100.0),
    )
    for ladung, expected_ladung_prozent in tests:
        assert abs(ladung.ladung_prozent - expected_ladung_prozent) < 0.1


if __name__ == "__main__":
    test_sp_ladung()
