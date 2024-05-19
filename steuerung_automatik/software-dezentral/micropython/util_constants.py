def to_version(version):
    assert len(version) == 3
    return 10_000 * version[0] + 100 * version[1] + version[2]


DEVELOPMENT = False

VERSION_HW = to_version((1, 0, 0))
VERSION_SW = to_version((0, 1, 4 + (50 if DEVELOPMENT else 0)))

DAY_MS = 24 * 60 * 60 * 1000
WEEK_MS = 7 * DAY_MS
