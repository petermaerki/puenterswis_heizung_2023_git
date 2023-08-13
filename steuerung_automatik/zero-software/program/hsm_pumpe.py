import logging
import typing

from hsm import hsm

from program.hsm_signal import SignalBase
from program.utils_logger import ZeroLogger

if typing.TYPE_CHECKING:
    from program.context import Context

logger = logging.getLogger(__name__)


class HsmPumpe(hsm.HsmMixin):
    """ """

    def __init__(self, ctx: "Context"):
        hsm.HsmMixin.__init__(self, mermaid_detailed=False, mermaid_entryexit=False)
        self.ctx = ctx
        self.set_logger(ZeroLogger(self))

    @hsm.init_state
    def state_aus(self, signal: SignalBase):
        """
        TRANSITION state_ein Bedarf oder Zwang, und Zentralspeicher warm. Oder Leeren.
        """
        if self.ctx.hsm_ladung.is_state(
            self.ctx.hsm_ladung.state_bedarf,
            self.ctx.hsm_ladung.state_zwang,
        ):
            if (
                self.ctx.sensoren.zentralspeicher_oben_Tszo_C
                > self.ctx.konstanten.legionellen_fernleitungstemperatur_C + 5.0
            ):  # Todo korrekte temperatur
                raise hsm.StateChangeException(self.state_ein)
        if self.ctx.hsm_ladung.is_state(
            self.ctx.hsm_ladung.state_leeren,
        ) and self.ctx.hsm_pumpe.is_state(self.ctx.hsm_pumpe.state_aus):
            raise hsm.StateChangeException(self.state_ein, why="Pumpe ein zum leeren")

        raise hsm.DontChangeStateException()

    def entry_aus(self, signal: SignalBase):
        logger.info("PUMPE AUSSCHALTEN")
        self.ctx.aktoren.pumpe_on = False

    def state_ein(self, signal: SignalBase):
        """
        TRANSITION state_aus Ladung fertig oder Zentralspeicher zu kalt oder keine Anforderung.
        """
        if self.ctx.hsm_ladung.is_state(
            self.ctx.hsm_ladung.state_bedarf,
            self.ctx.hsm_ladung.state_zwang,
        ):
            if (
                self.ctx.sensoren.zentralspeicher_oben_Tszo_C
                < self.ctx.konstanten.legionellen_fernleitungstemperatur_C
            ):
                raise hsm.StateChangeException(
                    self.state_aus,
                    why="Zentralspeicher zu kalt daher Pumpe aus und warten",
                )

        if self.ctx.hsm_ladung.is_state(
            self.ctx.hsm_ladung.state_aus,
        ):
            raise hsm.StateChangeException(
                self.state_aus, why="Ladung aus daher Pumpe aus"
            )

        if not self.ctx.sensoren.anforderung:  # falls die Anforderung weg gefallen ist
            raise hsm.StateChangeException(
                self.state_aus,
                why="Anforderung ist weg gefallen daher wechsel auf pumpe aus",
            )

        if (
            # bei einer Anforderung ist mindestens ein dezentrales Ventil offen
            not self.ctx.sensoren.anforderung
            # alle Ventile sind offen
            and not self.ctx.aktoren.ventile_zwangsladung_on
        ):
            logger.fatal(
                "Pumpe laeuft aber kein einziges Ventil ist offen. Das darf nicht dauerhaft sein."
            )

        # Todo Mischventil hier regeln

        raise hsm.DontChangeStateException()

    def entry_ein(self, signal: SignalBase):
        logger.info("PUMPE EINSCHALTEN")
        self.ctx.aktoren.pumpe_on = True
