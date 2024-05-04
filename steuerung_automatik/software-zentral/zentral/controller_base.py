import logging
import typing

from abc import ABC


if typing.TYPE_CHECKING:
    from zentral.context import Context


logger = logging.getLogger(__name__)


class ControllerABC(ABC):
    def process(self, ctx: "Context"): ...
