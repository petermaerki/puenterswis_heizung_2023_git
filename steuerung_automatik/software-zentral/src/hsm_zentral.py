import logging
import typing

from hsm import hsm

from src.hsm_zentral_signal import SignalZentralBase
from src.utils_logger import ZeroLogger

logger = logging.getLogger(__name__)


class HsmZentral(hsm.HsmMixin):
    """ """

    def __init__(self):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self.set_logger(ZeroLogger(self))

    @hsm.init_state
    def state_initializeing(self, signal: SignalZentralBase):
        """ """

        raise hsm.DontChangeStateException()

    def state_ok(self, signal: SignalZentralBase):
        """ """
        raise hsm.DontChangeStateException()

    def state_ok_auto(self, signal: SignalZentralBase):
        """ """
        raise hsm.DontChangeStateException()

    @hsm.init_state
    def state_ok_manual(self, signal: SignalZentralBase):
        """ """
        raise hsm.DontChangeStateException()

    def state_error(self, signal: SignalZentralBase):
        """ """
        raise hsm.DontChangeStateException()