import asyncio
import dataclasses
import pathlib
import sys

import matplotlib.pyplot as plt

from .constants import DIRECTORY_ZENTRAL

sys.path.append(str(DIRECTORY_ZENTRAL.parent / "software-zero"))
sys.path.append(str(DIRECTORY_ZENTRAL.parent / "software-dezentral"))

from utils_common.utils_constants import ZERO_VIRGIN

from zentral import config_etappe
from zentral.context_mock import ContextMock
from zentral.controller_mischventil import ControllerMischventil

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


def modell_mischventil(Tsz4_C: float, Tfr_C: float, stellwert_100: float) -> float:
    """
    return Tfv_C
    """
    stellwert_V = ControllerMischventil.calculate_valve_V(stellwert_100=stellwert_100)
    anteil_modell = max(min((stellwert_V - 3.0) / 4.0, 1.0), 0.0)
    Tfv = anteil_modell * (Tsz4_C - Tfr_C) + Tfr_C
    return Tfv


class Plot:
    def __init__(self):
        self.now_s: list[float] = []
        self.valve_100: list[float] = []
        self.Tsz4_C: list[float] = []
        self.Tfr_C: list[float] = []
        self.Tfv_C: list[float] = []
        self.Tfv_set_C: list[float] = []
        self.mischventil_actuation_credit_prozent: list[float] = []

    def point(
        self,
        now_s: float,
        Tsz4_C: float,
        Tfr_C: float,
        Tfv_C: float,
        Tfv_set_C: float,
        stellwert_100: float,
        mischventil_actuation_credit_prozent: float,
    ) -> None:
        self.now_s.append(now_s)
        self.Tsz4_C.append(Tsz4_C)
        self.Tfr_C.append(Tfr_C)
        self.Tfv_C.append(Tfv_C)
        self.Tfv_set_C.append(Tfv_set_C)
        self.valve_100.append(stellwert_100)
        self.mischventil_actuation_credit_prozent.append(mischventil_actuation_credit_prozent)

    def plot(self, title: str, filename: pathlib.Path) -> None:
        fig, ax1 = plt.subplots(figsize=(14, 8))

        color = "tab:red"
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Temperature [C]", color=color)
        ax1.plot(self.now_s, self.Tsz4_C, color="tab:grey", label="Tsz4")
        ax1.plot(self.now_s, self.Tfv_C, linewidth=4, color="tab:red", label="Tfv")
        ax1.plot(self.now_s, self.Tfv_set_C, color="tab:orange", label="Tfv set")
        ax1.plot(self.now_s, self.Tfr_C, color="tab:pink", label="Tfr")
        ax1.tick_params(axis="y", labelcolor=color)
        ax1.legend(loc="lower left")

        ax2 = ax1.twinx()
        color = "black"
        ax2.set_ylabel("Valve, credit [%]", color=color)
        ax2.plot(self.now_s, self.valve_100, color="blue", linestyle="--", label="valve_prozent")
        ax2.plot(self.now_s, self.mischventil_actuation_credit_prozent, linestyle="--", color=color, label="credit_prozent")
        ax2.set_ylim([-5, 105])
        ax2.tick_params(axis="y", labelcolor=color)
        ax2.legend(loc="lower right")

        fig.tight_layout()
        fig.suptitle(title)
        plt.savefig(filename)
        if True:
            plt.show()


@dataclasses.dataclass
class Testparams:
    label: str
    Tsz4_C: float = 65.0
    Tfr_C: float = 25.0
    Tfv_set_C: float = 60.0
    CONTROLLER_FAKTOR_STABILITAET_1: float = 0.5

    @property
    def filename(self) -> pathlib.Path:
        f = "controller_mischventil_test_scenario_" + self.label.replace(" ", "-")
        return DIRECTORY_OF_THIS_FILE / f


async def run_scenario(testparam: Testparams) -> None:
    async with ContextMock(config_etappe.create_config_etappe(hostname=ZERO_VIRGIN)) as ctx:
        await ctx.init()
        ctx.modbus_communication.pcb_dezentral_heizzentrale.Tsz4_C = testparam.Tsz4_C
        ctx.modbus_communication.pcb_dezentral_heizzentrale.Tfr_C = testparam.Tfr_C

        ControllerMischventil._FAKTOR_STABILITAET_1 = testparam.CONTROLLER_FAKTOR_STABILITAET_1
        ctl = ControllerMischventil(now_s=0.0)

        Tsz4_C = ctx.modbus_communication.pcb_dezentral_heizzentrale.Tsz4_C
        Tfr_C = ctx.modbus_communication.pcb_dezentral_heizzentrale.Tfr_C
        ctx.hsm_zentral.mischventil_stellwert_100 = ControllerMischventil.calculate_valve_100(stellwert_V=1.0)
        ctx.hsm_zentral.solltemperatur_Tfv = testparam.Tfv_set_C
        ctx.hsm_zentral.relais.relais_6_pumpe_ein = True

        p = Plot()
        for now_s in range(30 * 60):
            if True:  # Todo "Set wechsel"
                if now_s == 1000:
                    ctx.hsm_zentral.solltemperatur_Tfv = 30.0
            ctx.hsm_zentral.relais.relais_6_pumpe_ein = True
            ctx.modbus_communication.pcb_dezentral_heizzentrale.Tfv_C = modell_mischventil(
                Tsz4_C=Tsz4_C,
                Tfr_C=Tfr_C,
                stellwert_100=ctx.hsm_zentral.mischventil_stellwert_100,
            )
            p.point(
                now_s=now_s,
                Tsz4_C=Tsz4_C,
                Tfr_C=Tfr_C,
                Tfv_C=ctx.modbus_communication.pcb_dezentral_heizzentrale.Tfv_C,
                Tfv_set_C=ctx.hsm_zentral.solltemperatur_Tfv,
                stellwert_100=ctx.hsm_zentral.mischventil_stellwert_100,
                mischventil_actuation_credit_prozent=ctl.credit.mischventil_actuation_credit_prozent,
            )
            ctl.process(ctx=ctx, now_s=float(now_s))

        p.plot(title=testparam.label, filename=testparam.filename)


async def main():
    for testparam in (
        Testparams(
            "normal",
            Tsz4_C=65.0,
            Tfr_C=25.0,
            Tfv_set_C=60.0,
        ),
        Testparams(
            "gain zu hoch daher Oszillation blocken",
            Tsz4_C=65.0,
            Tfr_C=25.0,
            Tfv_set_C=60.0,
            CONTROLLER_FAKTOR_STABILITAET_1=2.5,
        ),
        Testparams(
            "zentraler Speicher etwas kalt Tfv steht an",
            Tsz4_C=40.0,
            Tfr_C=25.0,
            Tfv_set_C=60.0,
        ),
        Testparams(
            "zentraler Speicher komplett kalt daher mischventil inaktiv",
            Tsz4_C=25.5,
            Tfr_C=25.0,
            Tfv_set_C=60.0,
        ),
        Testparams(
            "Ruecklauf waermer als zentraler Speicher daher mischventil inaktiv",
            Tsz4_C=25.0,
            Tfr_C=35.0,
            Tfv_set_C=60.0,
        ),
        Testparams(
            "Tfv set immer 30",
            Tfv_set_C=30.0,
        ),
    ):
        await run_scenario(testparam=testparam)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
