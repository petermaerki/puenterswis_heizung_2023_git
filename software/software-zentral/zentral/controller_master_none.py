from __future__ import annotations

import logging

from zentral.controller_master import ControllerMaster
from zentral.util_controller_verbrauch_schaltschwelle import HauserValveVariante

logger = logging.getLogger(__name__)


class ControllerMasterNone(ControllerMaster):
    def __init__(self, ctx: "Context", now_s: float) -> None:
        super().__init__(ctx=ctx, now_s=now_s)
        self._hvv = HauserValveVariante(anhebung_prozent=0.0)

    def process(self, now_s: float) -> None:
        self.ctx.hsm_zentral.update_hvv(hvv=self._hvv)
