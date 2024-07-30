import json
import pathlib
import time
from typing import Any

from zentral.constants import DIRECTORY_PERSISTENCE

VERSION = 1.0
_TAG_VERSION = "version"
_TAG_HISTORY = "history"
_TAG_DATA = "data"

_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"


class FileParseException(Exception):
    pass


class TimeBase:
    @property
    def monotonic_s(self) -> float:
        return time.monotonic()

    @property
    def timestamp(self) -> str:
        return time.strftime(_TIMESTAMP_FORMAT, time.localtime())


class TimeBaseMock(TimeBase):
    def __init__(self) -> None:
        self._now_s = 0.0

    @property
    def now_s(self) -> float:
        return self._now_s

    @now_s.setter
    def now_s(self, now_s: float) -> None:
        self._now_s = now_s

    @property
    def monotonic_s(self) -> float:
        return self._now_s

    @property
    def timestamp(self) -> str:
        return time.strftime(_TIMESTAMP_FORMAT, time.localtime(1721242437.4851625 + self._now_s))


class Persistence:
    def __init__(self, tag: str, period_s: float = 120.0, time_base: TimeBase | None = None) -> None:
        """
        Read the persistence_file.
        See _load_file()
        """
        self.period_s = period_s
        self.tag = tag
        if time_base is None:
            self._time_base = TimeBase()
        else:
            self._time_base = time_base
        self._dirty_s: float | None = None
        self._data: Any = None
        self._history: list[str] = []
        self._load_file()

    @staticmethod
    def get_filename(tag: str) -> pathlib.Path:
        return DIRECTORY_PERSISTENCE / f"data_{tag}.json"

    @property
    def filename(self) -> pathlib.Path:
        return self.get_filename(self.tag)

    def expect(self, expected_dict_file: dict) -> None:
        assert isinstance(expected_dict_file, dict)
        with self.filename.open("r") as fp:
            dict_file = json.load(fp=fp)
        if dict_file == expected_dict_file:
            return
        print(f"file_contents:\n{dict_file}")
        print(f"expected_file_contents:\n{expected_dict_file}")
        assert False

    def expect_history(self, expected_history: list) -> None:
        assert isinstance(expected_history, list)
        if self._history == expected_history:
            return
        print(f"history:\n{self._history}")
        print(f"expected_history:\n{expected_history}")
        assert False

    def push_data(self, data: Any) -> None:
        if self._data == data:
            return
        self._data = data
        self._dirty_s = self._time_base.monotonic_s

    def get_data(self) -> Any:
        assert self._dirty_s is None, "Call get_data() BEFORE data has been written!"
        return self._data

    def save(self, force: bool = False, why: str = "forced") -> None:
        """
        Store the data, but not before 'period_s'.
        """
        if self._dirty_s is None:
            return
        if force:
            self._add_history(why=why)
        else:
            unsaved_s = self._time_base.monotonic_s - self._dirty_s
            if unsaved_s < self.period_s:
                return
            self._add_history(f"{unsaved_s:0.0f}s over")

        # Save file
        with self.filename.open("w") as fp:
            dict_file = {
                _TAG_VERSION: VERSION,
                _TAG_HISTORY: self._history,
                _TAG_DATA: self._data,
            }
            json.dump(obj=dict_file, sort_keys=True, indent=4, fp=fp)
        self._dirty_s = None

    def _load_file(self) -> None | Any:
        """
        Load a file from the filesystem.
        return None: If there was no file.
        return data: If success
        """
        assert self._dirty_s is None, "Call _load_file() BEFORE data has been written!"
        try:
            with self.filename.open("r") as fp:
                dict_file = json.load(fp=fp)
        except FileNotFoundError:
            return None
        self._data = dict_file[_TAG_DATA]
        self._history = dict_file[_TAG_HISTORY]
        version = dict_file[_TAG_VERSION]
        if VERSION != version:
            raise FileParseException(f"Expected version {VERSION} but read {version}!")
        self._add_history("file loaded")
        return self._data

    def _add_history(self, why: str) -> None:
        if len(self._history) > 100:
            # Make sure that the history does not get too long
            self._history = []
        history_text = f"{self._time_base.timestamp} {why}"
        self._history.append(history_text)
