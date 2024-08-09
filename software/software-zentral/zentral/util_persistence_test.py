from zentral.util_persistence import Persistence, TimeBaseMock
from zentral.util_persistence_legionellen import PersistenceLegionellen

_TAG = "test"
_PERIOD_S = 100
_TAG_LEGIONELLEN = "test_legionellen"


def test_persistence():
    # Setup without file
    time_base_mock = TimeBaseMock()
    p = Persistence(tag=_TAG, period_s=_PERIOD_S, time_base=time_base_mock)
    p.filename.unlink(missing_ok=True)

    p = Persistence(tag=_TAG, period_s=_PERIOD_S, time_base=time_base_mock)
    # The file could not be read: get_data() will return None
    assert p.get_data() is None
    p.expect_not_dirty()

    # dirty but time not over: File NOT written.
    p.push_data(data=[1])
    time_base_mock.now_s += _PERIOD_S / 4
    p.push_data(data=2)
    p.expect_dirty()
    assert not p.filename.exists()

    # dirty and time not over: File not written.
    time_base_mock.now_s += _PERIOD_S / 4
    p.expect_dirty()
    assert not p.save()
    assert not p.filename.exists()

    # dirty and time over: File written.
    time_base_mock.now_s += _PERIOD_S
    p.expect_dirty_time_over()
    p.save()
    p.expect_not_dirty()
    expected = {
        "data": 2,
        "history": ["2024-07-17_20-56-27 150s over"],
        "version": 1.0,
    }
    p.expect(expected)

    # not dirty: File unchanged
    time_base_mock.now_s += 500.0
    p.save()
    p.expect_not_dirty()
    p.expect(expected)

    # file dirty, but no 'save()' yet: File unchanged
    time_base_mock.now_s += 110
    p.push_data(data=3)
    p.expect_dirty()
    p.expect(expected)

    # file dirty, time over, but no 'save()' yet: File unchanged
    time_base_mock.now_s += 130
    p.expect_dirty_time_over()
    p.expect(expected)

    # file dirty, time over. 'save()' will write the file with new data
    assert p.save()
    p.expect_not_dirty()
    expected = {
        "data": 3,
        "history": [
            "2024-07-17_20-56-27 150s over",
            "2024-07-17_21-08-47 130s over",
        ],
        "version": 1.0,
    }
    p.expect(expected)

    # 'save(force)' but not dirty: File unchanged
    p.save(force=True)
    p.expect(expected)

    # 'save(force)' but not dirty as push_data() pushed same data: File unchanged
    p.push_data(data=3)
    assert not p.save(force=True)
    p.expect(expected)

    # 'save(force)' but dirty: File written
    p.push_data(data=4)
    assert p.save(force=True, why="forced")
    expected = {
        "data": 4,
        "history": [
            "2024-07-17_20-56-27 150s over",
            "2024-07-17_21-08-47 130s over",
            "2024-07-17_21-08-47 forced",
        ],
        "version": 1.0,
    }
    p.expect(expected)

    # Read file and verify contents
    p_loaded = Persistence(tag="test", period_s=100, time_base=time_base_mock)
    assert p.get_data() == 4
    expected_history = [
        "2024-07-17_20-56-27 150s over",
        "2024-07-17_21-08-47 130s over",
        "2024-07-17_21-08-47 forced",
        "2024-07-17_21-08-47 file loaded",
    ]
    p_loaded.expect_history(expected_history)
    p_loaded.expect_not_dirty()


def test_persistence_legionellen():
    # Start test without file
    p = PersistenceLegionellen(tag=_TAG_LEGIONELLEN)
    p.persistence.filename.unlink(missing_ok=True)

    time_base_mock = TimeBaseMock()
    time_base_mock.now_s += 12.0
    p = PersistenceLegionellen(tag=_TAG_LEGIONELLEN, time_base=time_base_mock)
    p.persistence.expect_dirty()
    p.set_last_legionellen_killed_s("haus5")
    p.persistence.expect_dirty()

    haus4_s = p.get_last_legionellen_killed_s("haus4")
    assert haus4_s == 0.0
    haus5_s = p.get_last_legionellen_killed_s("haus5")
    assert haus5_s >= 12.0
    assert not p.save(force=False)
    time_base_mock.now_s += p.persistence.period_s
    assert p.save(force=False)

    p.set_last_legionellen_killed_s("haus6")
    p.persistence.expect_dirty()
    assert not p.save(force=False)
    time_base_mock.now_s += p.persistence.period_s + 2.0
    p.persistence.expect_dirty_time_over()
    assert p.save(force=False)


if __name__ == "__main__":
    test_persistence()
