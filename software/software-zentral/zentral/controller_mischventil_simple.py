import logging
import typing

from zentral.controller_base import ControllerMischventilABC

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


class ControllerMischventilNone(ControllerMischventilABC):
    def __init__(self, now_s: float) -> None:
        super().__init__(now_s=now_s)

    def process(self, ctx: "Context", now_s: float) -> None:
        pass

    def get_credit_100(self) -> float | None:
        """
        Return None: If the controller simple or None does not calculate the credit
        """
        return None


class ControllerMischventilSimple(ControllerMischventilNone):
    """
    Stellgrössen:
    * Pumpe ein/aus
    * Mischventil auf
    """

    _PUMPE_OFF_DURATION_S = 12.0 * 60.0

    def __init__(self, now_s: float) -> None:
        super().__init__(now_s=now_s)
        self._pumpe_off_till_s: float = now_s

    def get_credit_100(self) -> float | None:
        """
        Return None: If the controller simple or None does not calculate the credit
        """
        return None

    def process(self, ctx: "Context", now_s: float) -> None:
        # This will force a MissingModbusDataException()
        _Tbv2_C = ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tbv2_C

        ctx.hsm_zentral.relais.relais_0_mischventil_automatik = False
        # TODO: Fix the following line
        # ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt = not self.get_pumpe_ein(ctx=ctx, now_s=now_s)
        ctx.hsm_zentral.relais.relais_7_automatik = True
