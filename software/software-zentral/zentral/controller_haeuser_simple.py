import logging
import time
import typing

from zentral.controller_base import ControllerHaeuserABC

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class ControllerHaeuserNone(ControllerHaeuserABC):
    def __init__(self, now_s: float):
        pass

    def process(self, ctx: "Context", now_s: float) -> None:
        pass


class ControllerHaeuserSimple(ControllerHaeuserABC):
    def __init__(self, now_s: float):
        self.start_s = now_s

    def update_hauser_valve(self, ctx: "Context"):
        for haus in ctx.config_etappe.haeuser:
            sp_temperatur = haus.get_sp_temperatur()
            if sp_temperatur is None:
                continue
            if sp_temperatur.mitte_C < self.grenze_mitte_ein_C:
                haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = True
            elif sp_temperatur.mitte_C > self.grenze_mitte_aus_C:
                haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = False

    def process(self, ctx: "Context", now_s: float) -> None:
        self.update_hauser_valve(ctx=ctx)


def controller_haeuser_factory() -> ControllerHaeuserABC:
    return ControllerHaeuserSimple(time.monotonic())
    # return ControllerHaeuser(time.monotonic())
