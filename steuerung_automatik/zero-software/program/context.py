from dataclasses import dataclass

from hsm_signal import HsmTimeSignal

from program.constants import DIRECTORY_DOC
from program.hsm_jahreszeit import HsmJahreszeit
from program.hsm_ladung import HsmLadung
from program.hsm_pumpe import HsmPumpe


@dataclass(repr=True)
class Sensoren:
    brenner_a_on: bool = False
    brenner_b_on: bool = False
    anforderung: bool = False
    zentralspeicher_C: float = 20.0
    fernleitung_kalt_C: float = 20.0
    fernleitung_warm_C: float = 30.0


class Context:
    def __init__(self):
        self.hsm_ladung = HsmLadung(self)
        self.hsm_jahreszeit = HsmJahreszeit(self)
        self.hsm_pumpe = HsmPumpe(self)
        self.hsms = (self.hsm_ladung, self.hsm_jahreszeit, self.hsm_pumpe)
        self.sensoren = Sensoren()

        for hsm in self.hsms:
            hsm.init()
            hsm.write_mermaid_md(
                DIRECTORY_DOC / f"statemachine_{hsm.__class__.__name__}.md"
            )

        for hsm in self.hsms:
            hsm.start()

    def dispatch(self, signal: HsmTimeSignal) -> None:
        for hsm in self.hsms:
            hsm.dispatch(signal)
