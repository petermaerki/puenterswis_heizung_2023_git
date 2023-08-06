import logging
import typing

from hsm import hsm
from utils_logger import ZeroLogger

from program.hsm_signal import HsmTimeSignal

if typing.TYPE_CHECKING:
    from program.context import Context

logger = logging.getLogger(__name__)

SignalType = HsmTimeSignal


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
    def state_ok(self, signal: SignalType):
        if self._legionellen_last_killed_s == None:
            self._legionellen_last_killed_s = signal.time_s # Bei einem Software Neustart geht momentan die letzte Zeit vergessen. Einfache Loesung.
        if signal.time_s > self._legionellen_last_killed_s + self.ctx.konstanten.legionellen_intervall_s:
            raise hsm.StateChangeException(self.state_ausstehend)
        raise hsm.DontChangeStateException()

    def state_ausstehend(self, signal: SignalType):
        raise hsm.DontChangeStateException()
    
    def state_aktiv(self, signal: SignalType):
        if self.ctx.hsm_pumpe.is_state(self.ctx.hsm_pumpe.state_ein):
            self._legionellen_pumpenzeit_summe_s += signal.time_s - self._last_time_s
            self._last_time_s = signal.time_s
            if self._legionellen_pumpenzeit_summe_s > self.ctx.kontstanten.legionellen_zwangsladezeit_s:
                logger.info("Die Legionellen sind gekillt daher wechsel in legionellen ok")
                raise hsm.StateChangeException(self.state_ok)
            
        raise hsm.DontChangeStateException()


    def entry_aktiv(self, signal: HsmTimeSignal):
        self._last_time_s = signal.time_s
        self._legionellen_pumpenzeit_summe_s = 0.0
