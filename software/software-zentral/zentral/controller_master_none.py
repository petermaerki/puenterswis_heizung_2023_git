from __future__ import annotations

import logging
import typing

from zentral.controller_master import ControllerMaster

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class ControllerMasterNone(ControllerMaster):
    def __init__(self, ctx: "Context", now_s: float) -> None:
        super().__init__(ctx=ctx, now_s=now_s)

    def process(self, now_s: float) -> None:
        pass
