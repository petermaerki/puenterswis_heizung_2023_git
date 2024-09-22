from __future__ import annotations

import typing

from zentral.constants import DIRECTORY_PERSISTENCE

if typing.TYPE_CHECKING:
    pass


class PersistenceMischventil:
    TAG = "mischventil"
    FILENAME = DIRECTORY_PERSISTENCE / f"data_{TAG}.json"

    @classmethod
    def read(cls, stellwert_100_default: float) -> float:
        """
        Load data from persistence file.
        """
        try:
            data = cls.FILENAME.read_text()
            return float(data)
        except FileNotFoundError:
            return stellwert_100_default

    @classmethod
    def save(cls, stellwert_100: float) -> None:
        assert isinstance(stellwert_100, float)
        cls.FILENAME.write_text(repr(stellwert_100))
