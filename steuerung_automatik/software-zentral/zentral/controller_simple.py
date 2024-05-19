import logging
import typing

from zentral.constants import WHILE_HARGASSNER
from zentral.util_modbus_iregs_all import SpTemperatur
from zentral.controller_base import ControllerABC

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class ControllerSimple(ControllerABC):
    grenze_mitte_ein_C = 40.0
    grenze_mitte_aus_C = 50.0

    def process(self, ctx: "Context"):
        def update_hauser_valve():
            for haus in ctx.config_etappe.haeuser:
                hsm_dezentral = haus.status_haus.hsm_dezentral
                modbus_iregs_all = hsm_dezentral.modbus_iregs_all
                if modbus_iregs_all is None:
                    continue
                sp_temperatur: SpTemperatur = modbus_iregs_all.sp_temperatur
                if sp_temperatur is None:
                    continue

                if not WHILE_HARGASSNER:
                    if sp_temperatur.mitte_C < self.grenze_mitte_ein_C:
                        hsm_dezentral.dezentral_gpio.relais_valve_open = True
                    elif sp_temperatur.mitte_C > self.grenze_mitte_aus_C:
                        hsm_dezentral.dezentral_gpio.relais_valve_open = False

        def get_pumpe_ein():
            for haus in ctx.config_etappe.haeuser:
                hsm_dezentral = haus.status_haus.hsm_dezentral
                if hsm_dezentral.dezentral_gpio.relais_valve_open:
                    return True
            return False

        update_hauser_valve()

        ctx.hsm_zentral.relais.relais_0_mischventil_automatik = False
        ctx.hsm_zentral.relais.relais_6_pumpe_ein = get_pumpe_ein()
        ctx.hsm_zentral.relais.relais_7_automatik = True


def controller_factory() -> ControllerABC:
    return ControllerSimple()
