from __future__ import annotations

import logging
import time
import typing

from zentral.controller_base import ControllerHaeuserABC
from zentral.util_controller_verbrauch_schaltschwelle import HauserValveVariante
from zentral.util_scenarios import ScenarioHaeuserValveOpenIterator

if typing.TYPE_CHECKING:
    from zentral.context import Context
    from zentral.controller_haeuser import ProcessParams

logger = logging.getLogger(__name__)


class ControllerHaeuserValveOpenIterator(ControllerHaeuserABC):
    TODO_ANHEBUNG_PROZENT = 0.0

    def __init__(self, now_s: float, ctx: "Context", scenario: ScenarioHaeuserValveOpenIterator):
        super().__init__(now_s=now_s)
        self.ctx = ctx
        self.scenario = scenario
        self.actual_haus_end_s: float = time.monotonic() + self.scenario.duration_haus_s
        self.actual_haus_idx0: int = -1
        """
        -1: All valves open
        0: First Haus
        1: Second Haus
        ...
        """
        self._done = False
        self.log_lines: list[str] = []

    def _log(self, line: str) -> None:
        logger.info(line)
        self.log_lines.append(line)

    def done(self) -> bool:
        return self._done

    def process(self, params: "ProcessParams") -> HauserValveVariante:
        if time.monotonic() > self.actual_haus_end_s:
            # Das nächste Haus
            if self.actual_haus_idx0 == -1:
                # All valves open
                for haus in self.ctx.config_etappe.haeuser:
                    self._log(f"All valves open: {haus.influx_tag}: flow_v1_m3h={haus.status_haus.hsm_dezentral.mbus_measurement.flow_v1_m3h:0.5f}")
            else:
                try:
                    haus = self.ctx.config_etappe.haeuser[self.actual_haus_idx0]
                    self._log(f"One valve open: {haus.influx_tag}: flow_v1_m3h={haus.status_haus.hsm_dezentral.mbus_measurement.flow_v1_m3h:0.5f}")
                except ImportError:
                    pass

            self.actual_haus_idx0 += 1
            self.actual_haus_end_s += self.scenario.duration_haus_s

        hvv = HauserValveVariante(anhebung_prozent=self.TODO_ANHEBUNG_PROZENT)
        if self.actual_haus_idx0 == -1:
            # All valves open
            for haus_idx0, haus in enumerate(self.ctx.config_etappe.haeuser):
                assert haus.status_haus is not None
                hvv.haeuser_valve_to_open.append(haus.config_haus.nummer)
            return hvv

        # Close all valves but one
        self._done = True

        for haus_idx0, haus in enumerate(self.ctx.config_etappe.haeuser):
            assert haus.status_haus is not None
            if haus_idx0 >= self.scenario.haeuser_count:
                break
            if haus_idx0 == self.actual_haus_idx0:
                self._done = False
                hvv.haeuser_valve_to_open.append(haus.config_haus.nummer)
            else:
                hvv.haeuser_valve_to_close.append(haus.config_haus.nummer)

        return hvv
