from __future__ import annotations

import logging
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

    if False:
        GRENZE_LADUNG_EIN_PROZENT = 60.0

    if False:
        GRENZE_LADUNG_EIN_PROZENT = -500.0
        GRENZE_LADUNG_AUS_PROZENT = -40.0

    if True:
        GRENZE_LADUNG_EIN_PROZENT = 5.0
        GRENZE_LADUNG_AUS_PROZENT = 30.0

    if False:
        GRENZE_LADUNG_EIN_PROZENT = 20.0
        GRENZE_LADUNG_AUS_PROZENT = 70.0

    if False:
        GRENZE_LADUNG_EIN_PROZENT = 20.0
        GRENZE_LADUNG_AUS_PROZENT = 110.0

    def update_hauser_valve(self, params: "ProcessParams") -> HauserValveVariante:
        TODO_ANHEBUNG_PROZENT = 0.0
        hvv = HauserValveVariante(anhebung_prozent=TODO_ANHEBUNG_PROZENT)

        for haus_ladung in params.haeuser_ladung:
            if haus_ladung.ladung_Prozent < self.GRENZE_LADUNG_EIN_PROZENT:
                hvv.to_open(haus_ladung=haus_ladung)

            if haus_ladung.ladung_Prozent > self.GRENZE_LADUNG_AUS_PROZENT:
                hvv.to_close(haus_ladung=haus_ladung)

        return hvv

    def process(self, params: "ProcessParams") -> HauserValveVariante:
        hvv = self.update_hauser_valve(params=params)
        return hvv
