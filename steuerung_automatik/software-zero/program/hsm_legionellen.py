import logging
import typing

from hsm import hsm

from program.hsm_signal import LegionellenLadungSignal, SignalBase
from program.util_logger import ZeroLogger

if typing.TYPE_CHECKING:
    from program.context import Context

logger = logging.getLogger(__name__)


class HsmLegionellen(hsm.HsmMixin):
    """ """

    def __init__(self, ctx: "Context"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self.ctx = ctx
        self.set_logger(ZeroLogger(self))
        self._legionellen_last_killed_s = None
        self._last_time_s = None
        self._legionellen_pumpenzeit_summe_s = None

    @hsm.init_state
    def state_ok(self, signal: SignalBase):
        """
        TRANSITION state_ausstehend Zeit abgelaufen
        """
        if self._legionellen_last_killed_s is None:
            # Bei einem Software Neustart geht momentan die letzte Zeit vergessen.
            # Einfache Loesung.
            self._legionellen_last_killed_s = self.ctx.time_s
        if self.ctx.time_s > self._legionellen_last_killed_s + self.ctx.konstanten.legionellen_intervall_s:
            raise hsm.StateChangeException(
                self.state_ausstehend,
                why="Zeit ist abgelaufen",
            )
        raise hsm.DontChangeStateException()

    def state_ausstehend(self, signal: SignalBase):
        """
        TRANSITION state_aktiv Signal LegionellenLadung
        """
        if isinstance(signal, LegionellenLadungSignal):
            raise hsm.StateChangeException(self.state_aktiv)
        raise hsm.DontChangeStateException()

    def state_aktiv(self, signal: SignalBase):
        """
        TRANSITION state_ok Legionellen gekillt
        """
        if self.ctx.hsm_pumpe.is_state(self.ctx.hsm_pumpe.state_ein):
            self._legionellen_pumpenzeit_summe_s += signal.time_s - self._last_time_s
            self._last_time_s = signal.time_s
            if self._legionellen_pumpenzeit_summe_s > self.ctx.kontstanten.legionellen_zwangsladezeit_s:
                raise hsm.StateChangeException(
                    self.state_ok,
                    why="Legionellen sind gekillt",
                )

        raise hsm.DontChangeStateException()

    def entry_aktiv(self, signal: SignalBase):
        self._last_time_s = signal.time_s
        self._legionellen_pumpenzeit_summe_s = 0.0
