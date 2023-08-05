import logging
import typing

from hsm import hsm
from utils_logger import ZeroLogger

from program.hsm_signal import HsmTimeSignal

if typing.TYPE_CHECKING:
    from program.context import Context

logger = logging.getLogger(__name__)

SignalType = HsmTimeSignal


class HsmPumpe(hsm.HsmMixin):
    """ """

    def __init__(self, ctx: "Context"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self.ctx = ctx
        self.set_logger(ZeroLogger(self))

    @hsm.init_state
    def state_aus(self, signal: SignalType):
        if self.ctx.hsm_ladung.is_state(
            self.ctx.hsm_ladung.state_bedarf,
            self.ctx.hsm_ladung.state_zwang,
        ):
            if (
                self.ctx.sensoren.zentralspeicher_oben_Tszo_C > 70.0
            ):  # Todo korrekte temperatur
                raise hsm.StateChangeException(self.state_ein)
        if self.ctx.hsm_ladung.is_state(
            self.ctx.hsm_ladung.state_leeren,
        ) and self.ctx.hsm_pumpe.is_state(self.ctx.hsm_pumpe.state_aus):
            logger.info("Pumpe ein zum leeren")
            raise hsm.StateChangeException(self.state_ein)

        raise hsm.DontChangeStateException()

    def entry_aus(self, signal: HsmTimeSignal):
        logger.info("PUMPE AUSSCHALTEN")
        self.ctx.aktoren.pumpe_on = False

    def state_ein(self, signal: SignalType):
        if self.ctx.hsm_ladung.is_state(
            self.ctx.hsm_ladung.state_bedarf,
            self.ctx.hsm_ladung.state_zwang,
        ):
            if (
                self.ctx.sensoren.zentralspeicher_oben_Tszo_C < 40.0
            ):  # Todo korrekte temperatur
                logger.info("Zentralspeicher zu kalt daher Pumpe aus und warten")
                raise hsm.StateChangeException(self.state_aus)

        if self.ctx.hsm_ladung.is_state(
            self.ctx.hsm_ladung.state_aus,
        ):
            logger.info("Ladung aus daher Pumpe aus")
            raise hsm.StateChangeException(self.state_aus)

        if (
            not self.ctx.sensoren.anforderung  # bei einer Anforderung ist mindestens ein dezentrales Ventil offen
            and not self.ctx.aktoren.ventile_zwangsladung_on  # alle Ventile sind offen
        ):
            logger.fatal(
                "Pumpe laeuft aber kein einziges Ventil ist offen. Das darf nicht dauerhaft sein."
            )

        raise hsm.DontChangeStateException()

    def entry_ein(self, signal: HsmTimeSignal):
        logger.info("PUMPE EINSCHALTEN")
        self.ctx.aktoren.pumpe_on = True
