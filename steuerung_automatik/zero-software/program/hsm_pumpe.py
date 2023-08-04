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
            if self.ctx.sensoren.zentralspeicher_C > 70.0:
                raise hsm.StateChangeException(self.state_ein)
        raise hsm.DontChangeStateException()

    def entry_aus(self, signal: HsmTimeSignal):
        logger.info("PUMPE AUS")

    def state_ein(self, signal: SignalType):
        if self.ctx.hsm_ladung.is_state(
            self.ctx.hsm_ladung.state_bedarf,
            self.ctx.hsm_ladung.state_zwang,
        ):
            if self.ctx.sensoren.zentralspeicher_C < 40.0:
                raise hsm.StateChangeException(self.state_aus)
        raise hsm.DontChangeStateException()

    def entry_ein(self, signal: HsmTimeSignal):
        logger.info("PUMPE EIN")