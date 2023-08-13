import logging
import typing

from hsm import hsm

from program.hsm_signal import SignalBase
from program.utils_logger import ZeroLogger

if typing.TYPE_CHECKING:
    from program.context import Context

logger = logging.getLogger(__name__)


class HsmJahreszeit(hsm.HsmMixin):
    """ """

    def __init__(self, ctx: "Context"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self.ctx = ctx
        self.set_logger(ZeroLogger(self))

    @hsm.init_state
    def state_winter(self, signal: SignalBase):
        """
        TRANSITION state_sommer gestern viel energie verbraucht
        """
        # Todo if gestern weniger als 70 kWh und brenner sind aus: wechsel auf sommer
        if self.ctx.sensoren.energie_gestern_kWh < 70.0 and not (
            self.ctx.sensoren.brenner_1_on or self.ctx.sensoren.brenner_1_on
        ):
            raise hsm.StateChangeException(
                self.state_sommer,
                why="Gestern wenig Energie verbraucht daher Wechsel zu status Sommer",
            )
        raise hsm.DontChangeStateException()

    def state_sommer(self, signal: SignalBase):
        """
        TRANSITION state_winter gestern wenig energie verbraucht
        """
        # Todo if gestern mehr als 80 kWh und mindestens ein
        # Kesselbrennt:  wechsel auf winter
        if self.ctx.sensoren.energie_gestern_kWh > 80.0 and (
            self.ctx.sensoren.brenner_1_on or self.ctx.sensoren.brenner_1_on
        ):
            raise hsm.StateChangeException(
                self.state_winter,
                why="Gestern viel Energie verbraucht daher Wechsel zu status Winter",
            )
        raise hsm.DontChangeStateException()

    def entry_sommer(self, signal: SignalBase):
        # Todo einen Kessel sperren
        pass
