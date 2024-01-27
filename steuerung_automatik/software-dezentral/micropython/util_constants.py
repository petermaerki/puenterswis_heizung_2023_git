def to_version(version):
    assert len(version) == 3
    return 10_000 * version[0] + 100 * version[1] + version[2]


VERSION_HW = to_version((1, 0, 0))
VERSION_SW = to_version((0, 1, 0))

DEVELOPMENT = True

DAY_MS = const(24 * 60 * 60 * 1000)
WEEK_MS = const(7 * DAY_MS)
