import logging
import time
import typing

from zentral.controller_base import ControllerHaeuserABC

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class ControllerHaeuserNone(ControllerHaeuserABC):
    def process(self, ctx: "Context", now_s: float) -> None:
        pass


class ControllerHaeuserSimple(ControllerHaeuserABC):
    def process(self, ctx: "Context", now_s: float) -> None:
        pass


def controller_haeuser_factory() -> ControllerHaeuserABC:
    return ControllerHaeuserSimple(time.monotonic())
    # return ControllerHaeuser(time.monotonic())
