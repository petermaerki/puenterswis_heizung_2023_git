import logging
import time
import typing

from zentral.constants import WHILE_HARGASSNER
from zentral.controller_base import ControllerABC
from zentral.util_modbus_iregs_all import SpTemperatur

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class ControllerSimple(ControllerABC):
    grenze_mitte_ein_C = 46.0
    grenze_mitte_aus_C = 60.0
    if WHILE_HARGASSNER:
        anforderung_ein = False

    def update_hauser_valve(self, ctx: "Context"):
        if WHILE_HARGASSNER:
            ein_haus_zu_kalt = False
            alle_haueser_zu_warm = True

        for haus in ctx.config_etappe.haeuser:
            assert haus.status_haus is not None
            hsm_dezentral = haus.status_haus.hsm_dezentral
            modbus_iregs_all = hsm_dezentral.modbus_iregs_all
            if modbus_iregs_all is None:
                continue
            sp_temperatur: SpTemperatur = modbus_iregs_all.sp_temperatur
            if sp_temperatur is None:
                continue
            if WHILE_HARGASSNER:
                if haus.config_haus.haus_maerki:
                    # Haus 13 soll keine Anforderung ausloesen und auch nicht aktiv geladen werden
                    continue
                if sp_temperatur.mitte_C < self.grenze_mitte_ein_C:
                    ein_haus_zu_kalt = True
                else:
                    if sp_temperatur.mitte_C < self.grenze_mitte_aus_C:
                        alle_haueser_zu_warm = False
            else:
                if sp_temperatur.mitte_C < self.grenze_mitte_ein_C:
                    hsm_dezentral.dezentral_gpio.relais_valve_open = True
                elif sp_temperatur.mitte_C > self.grenze_mitte_aus_C:
                    hsm_dezentral.dezentral_gpio.relais_valve_open = False

        if WHILE_HARGASSNER:
            if ein_haus_zu_kalt:
                self.anforderung_ein = True
            else:
                if alle_haueser_zu_warm:
                    self.anforderung_ein = False

    def get_pumpe_ein(self, ctx: "Context"):
        for haus in ctx.config_etappe.haeuser:
            assert haus.status_haus is not None
            hsm_dezentral = haus.status_haus.hsm_dezentral
            if hsm_dezentral.dezentral_gpio.relais_valve_open:
                return True
        return False

    def process(self, ctx: "Context", now_s: float) -> None:
        # This will force a MissingModbusDataException()
        _Tbv2_C = ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tbv2_C

        self.update_hauser_valve(ctx=ctx)

        ctx.hsm_zentral.relais.relais_0_mischventil_automatik = False
        if WHILE_HARGASSNER:
            # statt Haeuser Anforderung relais_6_pumpe auf Anforderung: Hack falls Elferos spinnen
            ctx.hsm_zentral.relais.relais_6_pumpe_ein = not self.anforderung_ein
        else:
            ctx.hsm_zentral.relais.relais_6_pumpe_ein = self.get_pumpe_ein(ctx=ctx)

        ctx.hsm_zentral.relais.relais_7_automatik = True


def controller_factory() -> ControllerABC:
    return ControllerSimple(time.monotonic())
