from __future__ import annotations

import time
import typing

from zentral.util_persistence import Persistence, TimeBase

if typing.TYPE_CHECKING:
    pass

LEGIONELLEN_KILLED_C = 60.0
LEGIONELLEN_KILL_INTERVAL_S = 7 * 24 * 3600
"""
Entscheid 2024-03-27
Mindestens einmal in der Woche Temperatur in der Mitte auf 60C. Peter Schaer, Peter Maerki
"""


class PersistenceLegionellen:
    def __init__(self, tag="legionellen", time_base: TimeBase | None = None) -> None:
        self.persistence = Persistence(tag=tag, period_s=3600.0, time_base=time_base)
        """
        persistence-data:
        dict[str, float]
        str: haus.influx_tag
        float: time.time() als das letzte Mal LEGIONELLEN_KILLED_C erreicht wurde.
        """
        self._load_data()

    def _load_data(self) -> None:
        """
        Load data from persistence file.
        """
        data = self.persistence.get_data()
        if data is None:
            # No persistence file found
            self.persistence.push_data(data={})
            return
        assert isinstance(data, dict)
        for haus_influx_tag, temperature_C in data.items():
            assert isinstance(haus_influx_tag, str)
            assert isinstance(temperature_C, float)

    def set_last_legionellen_killed_s(self, haus_influx_tag: str) -> None:
        self.persistence.get_data()[haus_influx_tag] = time.time()
        self.persistence.set_dirty()

    def get_last_legionellen_killed_s(self, haus_influx_tag: str) -> float:
        try:
            return self.persistence.get_data()[haus_influx_tag]
        except KeyError:
            return time.time() - LEGIONELLEN_KILL_INTERVAL_S

    def get_next_legionellen_kill_s(self, haus_influx_tag: str) -> float:
        return LEGIONELLEN_KILL_INTERVAL_S + self.get_last_legionellen_killed_s(haus_influx_tag) - time.time()

    def save(self, force: bool, why: str | None = None) -> bool:
        return self.persistence.save(force=force, why=why)
