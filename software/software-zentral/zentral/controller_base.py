import logging
import typing

from abc import ABC


if typing.TYPE_CHECKING:
    from zentral.context import Context


logger = logging.getLogger(__name__)


class ControllerABC(ABC):
    def __init__(self, now_s: float) -> None: ...

    def process(self, ctx: "Context", now_s: float) -> None: ...

    def get_credit_100(self) -> float | None:
        """
        0.0 .. 100.0
        """
        return None
