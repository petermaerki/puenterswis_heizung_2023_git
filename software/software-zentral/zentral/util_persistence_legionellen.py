from __future__ import annotations

import time
import typing

from zentral.util_persistence import Persistence

if typing.TYPE_CHECKING:
    from zentral.context import Context

LEGIONELLEN_KILLED_C = 60.0
LEGIONELLEN_KILL_INTERVAL_S = 7 * 24 * 3600
"""
Entscheid 2024-03-27
Mindestens einmal in der Woche Temperatur in der Mitte auf 60C. Peter Schaer, Peter Maerki
"""


class PersistenceLegionellen:
    def __init__(self, ctx: "Context") -> None:
        self._ctx = ctx
        self._persistence = Persistence(tag="legionellen", period_s=3600.0)
        self._load_data()
        self._haueser_last_legionellen_killed_s: dict[str, float] = {}
        """
        time.time() als das letzte Mal LEGIONELLEN_KILLED_C erreicht wurde.
        """

    def _load_data(self) -> None:
        """
        Load data from persistence file.
        """
        data = self._persistence.get_data()
        if data is None:
            # No persistence file found
            return
        assert isinstance(data, dict)
        for haus_influx_tag, temperature_C in data.items():
            assert isinstance(haus_influx_tag, str)
            assert isinstance(temperature_C, float)

        self._haueser_last_legionellen_killed_s = data

    def update(self) -> None:
        """
        Find all hauses 'with > LEGIONELLEN_KILLED_C'
        and update '_haueser_last_legionenellen_killed'.
        """
        dirty = False

        for haus in self._ctx.config_etappe.haeuser:
            assert haus.status_haus is not None

            sp_temperatur = haus.get_sp_temperatur()
            if sp_temperatur is None:
                continue
            if sp_temperatur.mitte_C > LEGIONELLEN_KILLED_C:
                self._haueser_last_legionellen_killed_s[haus.influx_tag] = time.time()
                dirty = True

        if dirty:
            self._persistence.push_data(data=self._haueser_last_legionellen_killed_s)

        self._persistence.save()

    def save(self, force: bool, why: str) -> None:
        self._persistence.save(force=force, why=why)
