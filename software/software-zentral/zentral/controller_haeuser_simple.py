import logging
import time
import typing

from zentral.controller_base import ControllerABC

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class ControllerHaeuserSimple(ControllerABC):
    def process(self, ctx: "Context", now_s: float) -> None:
        pass


def controller_haeuser_factory() -> ControllerABC:
    return ControllerHaeuserSimple(time.monotonic())
    # return ControllerHaeuser(time.monotonic())
