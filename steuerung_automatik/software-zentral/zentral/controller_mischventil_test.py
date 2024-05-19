import asyncio
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


def modell_mischventil(Tszo_C: float, Tfr_C: float, stellwert_V: float) -> float:
    """
    return Tfv_C
    """
    anteil_modell = max(min((stellwert_V - 3.0) / 4.0, 1.0), 0.0)
    Tfv = anteil_modell * (Tszo_C - Tfr_C) + Tfr_C
    return Tfv


class Plot:
    def __init__(self):
        self.now_s: list[float] = []
        self.valve_100: list[float] = []
        self.Tszo_C: list[float] = []
        self.Tfr_C: list[float] = []
        self.Tfv_C: list[float] = []
        self.mischventil_actuation_credit_prozent: list[float] = []

    def point(
        self,
        now_s: float,
        Tszo_C: float,
        Tfr_C: float,
        Tfv_C: float,
        stellwert_V: float,
        mischventil_actuation_credit_prozent: float,
    ) -> None:
        valve_100 = ControllerMischventil.calculate_valve_100(stellwert_V=stellwert_V)
        self.now_s.append(now_s)
        self.Tszo_C.append(Tszo_C)
        self.Tfr_C.append(Tfr_C)
        self.Tfv_C.append(Tfv_C)
        self.valve_100.append(valve_100)
        self.mischventil_actuation_credit_prozent.append(mischventil_actuation_credit_prozent)

    def plot(self) -> None:
        fig, ax1 = plt.subplots()

        color = "tab:red"
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Temperature [C]", color=color)
        ax1.plot(self.now_s, self.Tszo_C, color="tab:red")
        ax1.plot(self.now_s, self.Tfv_C, color="tab:orange")
        ax1.plot(self.now_s, self.Tfr_C, color="tab:green")
        ax1.tick_params(axis="y", labelcolor=color)

        ax2 = ax1.twinx()
        color = "tab:gray"
        ax2.set_ylabel("Valve [%]", color=color)
        ax2.plot(self.now_s, self.valve_100, color=color)
        ax2.plot(self.now_s, self.mischventil_actuation_credit_prozent, color=color)
        ax2.set_ylim([0, 100])
        ax2.tick_params(axis="y", labelcolor=color)

        fig.tight_layout()
        plt.savefig(pathlib.Path(__file__).with_suffix(".png"))
        if True:
            plt.show()


async def main():
    async with ContextMock(config_etappe.create_config_etappe(hostname=ZERO_VIRGIN)) as ctx:
        await ctx.init()
        ctl = ControllerMischventil(now_s=0.0)
        Tszo_C = ctx.modbus_communication.pcb_dezentral_heizzentrale.Tszo_C
        Tfr_C = ctx.modbus_communication.pcb_dezentral_heizzentrale.Tfr_C
        ctx.hsm_zentral.mischventil_stellwert_V = 4.0
        ctx.hsm_zentral.solltemperatur_Tfv = 60.0
        ctx.hsm_zentral.relais.relais_6_pumpe_ein = True
        p = Plot()
        for now_s in range(20 * 60):
            # if now_s == 300:
            #     ctx.hsm_zentral.solltemperatur_Tfv = 50.0
            ctx.hsm_zentral.relais.relais_6_pumpe_ein = True
            ctx.modbus_communication.pcb_dezentral_heizzentrale.Tfv_C = modell_mischventil(
                Tszo_C=Tszo_C,
                Tfr_C=Tfr_C,
                stellwert_V=ctx.hsm_zentral.mischventil_stellwert_V,
            )
            p.point(
                now_s=now_s,
                Tszo_C=Tszo_C,
                Tfr_C=Tfr_C,
                Tfv_C=ctx.modbus_communication.pcb_dezentral_heizzentrale.Tfv_C,
                stellwert_V=ctx.hsm_zentral.mischventil_stellwert_V,
                mischventil_actuation_credit_prozent=ctl.credit.mischventil_actuation_credit_prozent,
            )
            ctl.process(ctx=ctx, now_s=float(now_s))
        p.plot()


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
