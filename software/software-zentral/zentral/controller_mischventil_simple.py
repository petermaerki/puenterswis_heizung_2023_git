import logging
import time
import typing

from zentral.constants import WHILE_HARGASSNER
from zentral.controller_base import ControllerMischventilABC

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class ControllerMischventilNone(ControllerMischventilABC):
    def process(self, ctx: "Context", now_s: float) -> None:
        pass

    def get_credit_100(self) -> float | None:
        """
        Return None: If the controller simple or None does not calculate the credit
        """
        return None


class ControllerMischventilSimple(ControllerMischventilABC):
    """
    Stellgrössen:
    * Pumpe ein/aus
    * Mischventil auf
    """

    grenze_mitte_ein_C = 46.0
    grenze_mitte_aus_C = 60.0

    def get_credit_100(self) -> float | None:
        """
        Return None: If the controller simple or None does not calculate the credit
        """
        return None

    def update_hauser_valve(self, ctx: "Context"):
        for haus in ctx.config_etappe.haeuser:
            if WHILE_HARGASSNER:
                haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = True

            sp_temperatur = haus.get_sp_temperatur()
            if sp_temperatur is None:
                continue
            if sp_temperatur.mitte_C < self.grenze_mitte_ein_C:
                haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = True
            elif sp_temperatur.mitte_C > self.grenze_mitte_aus_C:
                haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = False

    def get_pumpe_ein(self, ctx: "Context"):
        for haus in ctx.config_etappe.haeuser:
            assert haus.status_haus is not None
            hsm_dezentral = haus.status_haus.hsm_dezentral
            if hsm_dezentral.dezentral_gpio.relais_valve_open:
                return True
        return False

    def process(self, ctx: "Context", now_s: float) -> None:
        # This will force a MissingModbusDataException()
        if not WHILE_HARGASSNER:
            _Tbv2_C = ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tbv2_C

        ctx.hsm_zentral.relais.relais_0_mischventil_automatik = False
        ctx.hsm_zentral.relais.relais_6_pumpe_ein = self.get_pumpe_ein(ctx=ctx)
        ctx.hsm_zentral.relais.relais_7_automatik = True


def controller_mischventil_factory() -> ControllerMischventilABC:
    return ControllerMischventilSimple(time.monotonic())
    # return ControllerMischventil(time.monotonic())
