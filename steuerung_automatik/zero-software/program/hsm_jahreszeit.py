import logging
import typing

from hsm import hsm
from utils_logger import ZeroLogger

from program.hsm_signal import HsmTimeSignal

if typing.TYPE_CHECKING:
    from program.context import Context

logger = logging.getLogger(__name__)

SignalType = HsmTimeSignal


class HsmJahreszeit(hsm.HsmMixin):
    """ """

    def __init__(self, ctx: "Context"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self.ctx = ctx
        self.set_logger(ZeroLogger(self))

    @hsm.init_state
    def state_Winter(self, signal: SignalType):
        #Todo if gestern weniger als 70 kWh und brenner sind aus: wechsel auf sommer
        raise hsm.DontChangeStateException()

    def state_Sommer(self, signal: SignalType):
        # Todo if gestern mehr als 80 kWh und mindestens ein Kessel brennt:  wechsel auf winter
        raise hsm.DontChangeStateException()
    
    def entry_Sommer(self, signal: SignalType):
        # Todo einen Kessel sperren
