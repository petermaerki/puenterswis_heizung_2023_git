import dataclasses
import logging
import typing

from hsm import hsm

from zentral.controller_base import ControllerABC
from zentral.controller_simple import controller_factory
from zentral.util_logger import HsmLoggingLogger
from zentral.hsm_zentral_signal import SignalDrehschalter, SignalZentralBase, SignalHardwaretestBegin, SignalHardwaretestEnd

if typing.TYPE_CHECKING:
    from zentral.context import Context

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Relais:
    relais_0_mischventil_automatik = False
    relais_6_pumpe_ein = False
    relais_7_automatik = False


class HsmZentral(hsm.HsmMixin):
    """ """

    def __init__(self, ctx: "Context"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self.ctx = ctx
        self.add_logger(HsmLoggingLogger("HsmZentral"))
        self.relais = Relais()
        self.controller: ControllerABC = None
        self.grundzustand_manuell()

    def controller_process(self, ctx: "Context") -> None:
        if not self.is_state(self.state_hardwaretest):
            if self.controller is not None:
                self.controller.process(ctx=ctx)

    def grundzustand_manuell(self) -> None:
        self.controller = None
        self.relais.relais_0_mischventil_automatik = False
        self.relais.relais_6_pumpe_ein = True
        self.relais.relais_7_automatik = False

        for haus in self.ctx.config_etappe.haeuser:
            haus.status_haus.hsm_dezentral.dezentral_gpio.relais_valve_open = False

    def _handle_signal(self, signal: SignalZentralBase) -> None:
        if isinstance(signal, SignalHardwaretestBegin):
            raise hsm.StateChangeException(self.state_hardwaretest)

    @hsm.value(0)
    def state_error(self, signal: SignalZentralBase):
        """ """
        self._handle_signal(signal=signal)
        raise hsm.DontChangeStateException()

    @hsm.value(1)
    @hsm.init_state
    def state_initializing(self, signal: SignalZentralBase):
        """ """
        self._handle_signal(signal=signal)
        if isinstance(signal, SignalDrehschalter):
            new_state = self.state_ok_drehschaltermanuell if signal.manuell else self.state_ok_drehschalterauto_regeln
            raise hsm.StateChangeException(new_state)
        raise hsm.DontChangeStateException()

    def entry_hardwaretest(self, signal: SignalZentralBase):
        self.grundzustand_manuell()
        assert self.controller is None
        if isinstance(signal, SignalHardwaretestBegin):
            self.relais.relais_7_automatik = signal.relais_7_automatik

    @hsm.value(2)
    def state_hardwaretest(self, signal: SignalZentralBase):
        """ """
        if isinstance(signal, SignalHardwaretestBegin):
            self.relais.relais_7_automatik = signal.relais_7_automatik
        if isinstance(signal, SignalHardwaretestEnd):
            raise hsm.StateChangeException(self.state_ok_drehschalterauto)
        raise hsm.DontChangeStateException()

    @hsm.value(3)
    def state_ok(self, signal: SignalZentralBase):
        """ """
        self._handle_signal(signal=signal)
        raise hsm.DontChangeStateException()

    def entry_ok_drehschaltermanuell(self, signal: SignalZentralBase):
        self.grundzustand_manuell()

    @hsm.value(4)
    @hsm.init_state
    def state_ok_drehschaltermanuell(self, signal: SignalZentralBase):
        """ """
        if isinstance(signal, SignalDrehschalter):
            if not signal.manuell:
                raise hsm.StateChangeException(self.state_ok_drehschalterauto)

    def entry_ok_drehschalterauto(self, signal: SignalZentralBase):
        self.controller = controller_factory()

    @hsm.value(5)
    def state_ok_drehschalterauto(self, signal: SignalZentralBase):
        """ """
        if isinstance(signal, SignalDrehschalter):
            if signal.manuell:
                raise hsm.StateChangeException(self.state_ok_drehschaltermanuell)

    def entry_ok_drehschalterauto_manuell(self, signal: SignalZentralBase):
        self.grundzustand_manuell()

    @hsm.value(6)
    @hsm.init_state
    def state_ok_drehschalterauto_manuell(self, signal: SignalZentralBase):
        """ """
        pass

    @hsm.value(7)
    def state_ok_drehschalterauto_regeln(self, signal: SignalZentralBase):
        """ """
        pass
