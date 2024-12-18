from __future__ import annotations

import logging
import typing
from abc import ABC

if typing.TYPE_CHECKING:
    from zentral.context import Context


logger = logging.getLogger(__name__)


class ControllerMischventilABC(ABC):
    def __init__(self, now_s: float) -> None: ...

    def process(self, ctx: "Context", now_s: float) -> None: ...

    def get_credit_100(self) -> float | None:
        """
        Return None: If the controller simple or None does not calculate the credit
        0.0 .. 100.0
        """
        return None
