from zentral.util_persistence import Persistence, TimeBaseMock


def test_persistence():
    # Setup without file
    time_base_mock = TimeBaseMock()
    Persistence.get_filename(tag="test").unlink(missing_ok=True)

    p = Persistence(tag="test", period_s=100, time_base=time_base_mock)
    # The file could not be read: get_data() will return None
    assert p.get_data() is None

    # dirty but time not over: File NOT written.
    p.push_data(data=[1])
    time_base_mock.now_s += 90.0
    p.push_data(data=2)
    assert not p.filename.exists()

    # dirty and time not over: File not written.
    time_base_mock.now_s += 20.0
    p.save()
    assert not p.filename.exists()

    # dirty and time over: File written.
    time_base_mock.now_s += 90.0
    p.save()
    expected = {
        "data": 2,
        "history": ["2024-07-17_20-57-17 110s over"],
        "version": 1.0,
    }
    p.expect(expected)

    # not dirty: File unchanged
    time_base_mock.now_s += 500.0
    p.save()
    p.expect(expected)

    # file dirty, but no 'save()' yet: File unchanged
    time_base_mock.now_s += 110
    p.push_data(data=3)
    p.expect(expected)

    # file dirty, time over, but no 'save()' yet: File unchanged
    time_base_mock.now_s += 130
    p.expect(expected)

    # file dirty, time over. 'save()' will write the file with new data
    p.save()
    expected = {
        "data": 3,
        "history": [
            "2024-07-17_20-57-17 110s over",
            "2024-07-17_21-09-37 130s over",
        ],
        "version": 1.0,
    }
    p.expect(expected)

    # 'save(force)' but not dirty: File unchanged
    p.save(force=True)
    p.expect(expected)

    # 'save(force)' but not dirty as push_data() pushed same data: File unchanged
    p.push_data(data=3)
    p.save(force=True)
    p.expect(expected)

    # 'save(force)' but dirty: File written
    p.push_data(data=4)
    p.save(force=True)
    expected = {
        "data": 4,
        "history": [
            "2024-07-17_20-57-17 110s over",
            "2024-07-17_21-09-37 130s over",
            "2024-07-17_21-09-37 forced",
        ],
        "version": 1.0,
    }
    p.expect(expected)

    # Read file and verify contents
    p_loaded = Persistence(tag="test", period_s=100, time_base=time_base_mock)
    assert p.get_data() == 4
    expected_history = [
        "2024-07-17_20-57-17 110s over",
        "2024-07-17_21-09-37 130s over",
        "2024-07-17_21-09-37 forced",
        "2024-07-17_21-09-37 file loaded",
    ]
    p_loaded.expect_history(expected_history)


if __name__ == "__main__":
    test_persistence()
