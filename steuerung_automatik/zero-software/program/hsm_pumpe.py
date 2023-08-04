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
    def state_NichtLaden(self, signal: SignalType):
        if self.ctx.hsm_ladung.is_state(
            self.ctx.hsm_ladung.state_Bedarf,
            self.ctx.hsm_ladung.state_Zwang,
        ):
            if self.ctx.sensoren.zentralspeicher_C > 70.0:
                raise hsm.StateChangeException(self.state_Laden)
        raise hsm.DontChangeStateException()

    def state_Laden(self, signal: SignalType):
        if self.ctx.hsm_ladung.is_state(
            self.ctx.hsm_ladung.state_Bedarf,
            self.ctx.hsm_ladung.state_Zwang,
        ):
            if self.ctx.sensoren.zentralspeicher_C < 40.0:
                raise hsm.StateChangeException(self.state_NichtLaden)
        raise hsm.DontChangeStateException()
