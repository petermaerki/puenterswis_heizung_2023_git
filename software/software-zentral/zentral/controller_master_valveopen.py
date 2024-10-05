from __future__ import annotations

import logging
import time
import typing

from zentral.controller_master import ControllerMaster
from zentral.util_controller_verbrauch_schaltschwelle import HauserValveVariante
from zentral.util_scenarios import ScenarioMasterValveOpenIterator

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class ControllerMasterValveOpenIterator(ControllerMaster):
    TODO_ANHEBUNG_PROZENT = 0.0

    def __init__(self, ctx: "Context", now_s: float, scenario: ScenarioMasterValveOpenIterator):
        super().__init__(ctx=ctx, now_s=now_s)
        self.scenario = scenario
        self.actual_haus_end_s: float = time.monotonic() + self.scenario.duration_haus_s
        self.actual_haus_idx0: int = -1
        """
        -1: All valves open
        0: First Haus
        1: Second Haus
        ...
        """
        self.log_lines: list[str] = []

    def _log(self, line: str) -> None:
        logger.info(line)
        self.log_lines.append(line)

    def done(self) -> bool:
        return self.actual_haus_idx0 >= self.scenario.haeuser_count

    def process(self, now_s: float) -> None:
        hvv = self._process(now_s=now_s)
        self.ctx.hsm_zentral.update_hvv(hvv=hvv)

    def _process(self, now_s: float) -> HauserValveVariante:
        self.handler_pumpe.run_forced()

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
                hvv.haeuser_valve_to_open.append(haus.config_haus.nummer)
            return hvv

        # Close all valves but one
        for haus_idx0, haus in enumerate(self.ctx.config_etappe.haeuser):
            if haus_idx0 == self.actual_haus_idx0:
                hvv.haeuser_valve_to_open.append(haus.config_haus.nummer)
            else:
                hvv.haeuser_valve_to_close.append(haus.config_haus.nummer)

        return hvv
