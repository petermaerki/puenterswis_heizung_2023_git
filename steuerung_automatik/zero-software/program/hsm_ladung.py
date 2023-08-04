import logging
import typing

from hsm import hsm
from utils_logger import ZeroLogger

from program.hsm_signal import HsmTimeSignal

if typing.TYPE_CHECKING:
    from program.context import Context


logger = logging.getLogger(__name__)

SignalType = HsmTimeSignal


class HsmLadung(hsm.HsmMixin):
    """ """

    def __init__(self, ctx: "Context"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self.ctx = ctx
        self.set_logger(ZeroLogger(self))

    @hsm.init_state
    def state_Aus(self, signal: SignalType):
        raise hsm.DontChangeStateException()

    def state_Bedarf(self, signal: SignalType):
        raise hsm.DontChangeStateException()

    def state_Zwang(self, signal: SignalType):
        raise hsm.DontChangeStateException()
