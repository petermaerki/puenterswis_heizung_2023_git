import dataclasses
import logging

from hsm import hsm

from zentral.hsm_zentral_signal import SignalZentralBase, SignalHardwaretestBegin, SignalHardwaretestEnd

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Relais:
    relais_7_automatik = False


class HsmZentral(hsm.HsmMixin):
    """ """

    def __init__(self, hsm_logger: hsm.HsmLoggerProtocol):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False, hsm_logger=hsm_logger)
        self.relais = Relais()

    def _handle_signal(self, signal: SignalZentralBase) -> bool:
        if isinstance(signal, SignalHardwaretestBegin):
            raise hsm.StateChangeException(self.state_hardwaretest)

    @hsm.init_state
    def state_initializeing(self, signal: SignalZentralBase):
        """ """
        self._handle_signal(signal=signal)
        raise hsm.DontChangeStateException()

    def state_ok(self, signal: SignalZentralBase):
        """ """
        self._handle_signal(signal=signal)
        raise hsm.DontChangeStateException()

    def state_ok_auto(self, signal: SignalZentralBase):
        """ """
        self._handle_signal(signal=signal)
        raise hsm.DontChangeStateException()

    @hsm.init_state
    def state_ok_manual(self, signal: SignalZentralBase):
        """ """
        self._handle_signal(signal=signal)
        raise hsm.DontChangeStateException()

    def entry_hardwaretest(self, signal: SignalZentralBase):
        if isinstance(signal, SignalHardwaretestBegin):
            self.relais.relais_7_automatik = signal.relais_7_automatik

    def state_hardwaretest(self, signal: SignalZentralBase):
        """ """
        if isinstance(signal, SignalHardwaretestBegin):
            self.relais.relais_7_automatik = signal.relais_7_automatik
        if isinstance(signal, SignalHardwaretestEnd):
            raise hsm.StateChangeException(self.state_ok_auto)
        raise hsm.DontChangeStateException()

    def state_error(self, signal: SignalZentralBase):
        """ """
        self._handle_signal(signal=signal)
        raise hsm.DontChangeStateException()
