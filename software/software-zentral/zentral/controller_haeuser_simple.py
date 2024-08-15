from __future__ import annotations
import logging
import time
import typing

from zentral.controller_base import ControllerHaeuserABC
from zentral.util_controller_verbrauch_schaltschwelle import HauserValveVariante

if typing.TYPE_CHECKING:
    from zentral.controller_haeuser import ProcessParams

logger = logging.getLogger(__name__)


class ControllerHaeuserNone(ControllerHaeuserABC):
    def __init__(self, now_s: float):
        self._hvv = HauserValveVariante(anhebung_prozent=0.0)

    def process(self, params: "ProcessParams") -> HauserValveVariante:
        return self._hvv


class ControllerHaeuserSimple(ControllerHaeuserABC):
    GRENZE_LADUNG_EIN_PROZENT = 0.0
    GRENZE_LADUNG_AUS_PROZENT = 100.0

    def __init__(self, now_s: float):
        self.start_s = now_s

    def update_hauser_valve(self, params: "ProcessParams") -> HauserValveVariante:
        hvv = HauserValveVariante(anhebung_prozent=0.0)

        for haus_ladung in params.haeuser_ladung:
            if haus_ladung.ladung_Prozent < self.GRENZE_LADUNG_EIN_PROZENT:
                hvv.to_open(haus_ladung=haus_ladung)
                # haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = True
            if haus_ladung.ladung_Prozent > self.GRENZE_LADUNG_AUS_PROZENT:
                hvv.to_close(haus_ladung=haus_ladung)
                # haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = False

        return hvv

        # for haus in ctx.config_etappe.haeuser:
        #     sp_temperatur = haus.get_sp_temperatur()
        #     if sp_temperatur is None:
        #         continue
        #     if sp_temperatur.mitte_C < self.grenze_mitte_ein_C:
        #         haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = True
        #     elif sp_temperatur.mitte_C > self.grenze_mitte_aus_C:
        #         haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = False

    def process(self, params: "ProcessParams") -> HauserValveVariante:
        hvv = self.update_hauser_valve(params=params)
        return hvv


def controller_haeuser_factory() -> ControllerHaeuserABC:
    return ControllerHaeuserSimple(time.monotonic())
    # return ControllerHaeuser(time.monotonic())
