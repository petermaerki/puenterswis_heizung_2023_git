import logging
import typing

from hsm import hsm

from program.hsm_signal import LegionellenLadungSignal, SignalBase, TimeSignal
from program.utils_logger import ZeroLogger

if typing.TYPE_CHECKING:
    from program.context import Context


logger = logging.getLogger(__name__)


class HsmLadung(hsm.HsmMixin):
    """ """

    def __init__(self, ctx: "Context"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self.ctx = ctx
        self.set_logger(ZeroLogger(self))
        self._leeren_start_s: float = None

    @hsm.init_state
    def state_aus(self, signal: SignalBase):
        """Passt fuer Sommer und Winter"""
        if self.ctx.sensoren.anforderung:
            logger.info("wegen Anforderung wechsel in ladung bedarf")
            raise hsm.StateChangeException(self.state_bedarf)

        raise hsm.DontChangeStateException()

    def state_bedarf(self, signal: SignalBase):
        if self.ctx.hsm_jahreszeit.is_state(
            self.ctx.hsm_jahreszeit.state_sommer,
        ):
            if not self.ctx.sensoren.anforderung:
                logger.info("Anforderung weg daher wechsel in ladung aus")
                raise hsm.StateChangeException(self.state_aus)
            if self.ctx.sensoren.brenner_1_on or self.ctx.sensoren.brenner_1_on:
                logger.info("Brenner an daher wechsel in ladung zwang")
                raise hsm.StateChangeException(self.state_zwang)
        # State Winter
        if (
            self.ctx.sensoren.brenner_1_on or self.ctx.sensoren.brenner_1_on
        ) and self.ctx.hsm_legionellen.is_state(
            self.ctx.hsm_legionellen.state_ausstehend
        ):
            logger.info("Legionellen anstehend und daher wechsel zu zwang")
            raise hsm.StateChangeException(self.state_zwang)
        raise hsm.DontChangeStateException()

    def state_zwang(self, signal: SignalBase):
        if self.ctx.hsm_jahreszeit.is_state(
            self.ctx.hsm_jahreszeit.state_sommer,
        ):
            if True:  # Todo falls die Speicher genuegend voll sind
                logger.info("Ladung fertig daher wechsel in ladung leeren")
                raise hsm.StateChangeException(self.state_leeren)

        raise hsm.DontChangeStateException()

    def state_leeren(self, signal: SignalBase):
        """Passt für Sommer und Winter"""
        leeren_duration_s = 7 * 60.0
        if isinstance(signal, TimeSignal):
            if self.ctx.time_s > self._leeren_start_s + leeren_duration_s:
                logger.info("Ladung fertig daher wechsel in ladung aus")
                raise hsm.StateChangeException(self.state_aus)

        raise hsm.DontChangeStateException()

    def entry_aus(self, signal: SignalBase):
        self.ctx.aktoren.ventile_zwangsladung_on = False

    def entry_bedarf(self, signal: SignalBase):
        self.ctx.aktoren.ventile_zwangsladung_on = False

    def entry_zwang(self, signal: SignalBase):
        self.ctx.aktoren.ventile_zwangsladung_on = True
        self.ctx.hsm_legionellen.dispatch(LegionellenLadungSignal())

    def entry_leeren(self, signal: SignalBase):
        self.ctx.aktoren.ventile_zwangsladung_on = True
        self._leeren_start_s = signal.time_s
