import asyncio
import dataclasses
import pathlib
import typing

import matplotlib.pyplot as plt
import pytest

from zentral.constants import add_path_software_zero_dezentral
from zentral.util_matplotlib import matplot_reset
from zentral.util_pytest_git import assert_git_unchanged

add_path_software_zero_dezentral()

# ruff: noqa: E402
from utils_common.utils_constants import ZERO_VIRGIN

from zentral import config_etappe
from zentral.context_mock import ContextMock
from zentral.controller_mischventil import ControllerMischventil

if typing.TYPE_CHECKING:
    from zentral.context import Context
DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTRESULTS = DIRECTORY_OF_THIS_FILE / "controller_mischventil_testresults"


def modell_mischventil(Tsz4_C: float, Tfr_C: float, stellwert_100: float) -> float:
    """
    return Tfv_C
    """
    stellwert_V = ControllerMischventil.calculate_valve_V(stellwert_100=stellwert_100)
    anteil_modell = max(min((stellwert_V - 3.0) / 4.0, 1.0), 0.0)
    Tfv = anteil_modell * (Tsz4_C - Tfr_C) + Tfr_C
    return Tfv


class Plot:
    def __init__(self) -> None:
        self.now_s: list[float] = []
        self.valve_100: list[float] = []
        self.Tsz4_C: list[float] = []
        self.Tfr_C: list[float] = []
        self.Tfv_C: list[float] = []
        self.Tfv_set_C: list[float] = []
        self.mischventil_actuation_credit_prozent: list[float] = []

    def point(  # pylint: disable=too-many-positional-arguments
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

    def plot(self, title: str, filename: pathlib.Path, do_show_plot: bool) -> None:
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
        ax2.set_ylim((-5.0, 105.0))
        ax2.tick_params(axis="y", labelcolor=color)
        ax2.legend(loc="lower right")

        fig.tight_layout()
        fig.suptitle(title)
        plt.savefig(filename)
        if do_show_plot:
            plt.show()
        matplot_reset()


@dataclasses.dataclass
class Ttestparam:
    label: str
    Tsz4_C: float = 65.0
    Tfr_C: float = 25.0
    Tfv_set_C: float = 60.0
    CONTROLLER_FAKTOR_STABILITAET_1: float = 0.5

    @property
    def pytest_id(self) -> str:
        return self.label.replace(" ", "-")

    @property
    def filename_stem(self) -> pathlib.Path:
        f = "controller_mischventil_test_scenario_" + self.label.replace(" ", "-")
        return DIRECTORY_TESTRESULTS / f

    @property
    def filename_png(self) -> pathlib.Path:
        return self.filename_stem.with_suffix(".png")

    @property
    def dict_temperatures_C(self) -> dict[str, float]:
        dict_temperatures_C = {
            "Tsz1_C": 25.0,
            "Tsz2_C": 35.0,
            "Tsz3_C": 45.0,
            "Tsz4_C": 65.0,
            "Tfr_C": 25.0,
            "Tfv_C": 25.0,
            "Tbr_C": 25.0,
            "Tbv1_C": 25.0,
            "Tbv2_C": 25.0,
            "Tbv_C": 25.0,
        }
        dict_temperatures_C["Tsz4_C"] = self.Tsz4_C
        dict_temperatures_C["Tfr_C"] = self.Tfr_C
        return dict_temperatures_C


async def run_scenario(testparam: Ttestparam, do_show_plot: bool) -> None:
    async with ContextMock(config_etappe.create_config_etappe(hostname=ZERO_VIRGIN)) as ctx:
        await ctx.init()
        ctx.modbus_communication.pcbs_dezentral_heizzentrale.set_mock(dict_temperatures_C=testparam.dict_temperatures_C)

        class ControllerMischventilTest(ControllerMischventil):
            _FAKTOR_STABILITAET_1 = testparam.CONTROLLER_FAKTOR_STABILITAET_1

            def _pumpe_und_stabil(self, ctx: "Context", now_s: float) -> bool:
                return True

        ctl = ControllerMischventilTest(now_s=0.0)

        Tsz4_C = ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tsz4_C
        Tfr_C = ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tfr_C
        ctx.hsm_zentral.mischventil_stellwert_100 = ControllerMischventil.calculate_valve_100(stellwert_V=1.0)
        ctx.hsm_zentral.controller_master.handler_last.mock_solltemperatur_Tfv_C = testparam.Tfv_set_C
        ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt = True

        p = Plot()
        for now_s in range(30 * 60):
            if True:
                if now_s == 1000:
                    ctx.hsm_zentral.controller_master.handler_last.mock_solltemperatur_Tfv_C = 30.0
            ctx.hsm_zentral.relais.relais_6_pumpe_gesperrt = True
            ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tfv_C = modell_mischventil(
                Tsz4_C=Tsz4_C,
                Tfr_C=Tfr_C,
                stellwert_100=ctx.hsm_zentral.mischventil_stellwert_100,
            )
            p.point(
                now_s=now_s,
                Tsz4_C=Tsz4_C,
                Tfr_C=Tfr_C,
                Tfv_C=ctx.modbus_communication.pcbs_dezentral_heizzentrale.Tfv_C,
                Tfv_set_C=ctx.hsm_zentral.controller_master.handler_last.solltemperatur_Tfv_C,
                stellwert_100=ctx.hsm_zentral.mischventil_stellwert_100,
                mischventil_actuation_credit_prozent=ctl.credit.mischventil_actuation_credit_100,
            )
            ctl.process(ctx=ctx, now_s=float(now_s))

        p.plot(title=testparam.label, filename=testparam.filename_png, do_show_plot=do_show_plot)

        assert_git_unchanged(filename=testparam.filename_png)


_TESTPARAMS = [
    Ttestparam(
        "normal",
        Tsz4_C=65.0,
        Tfr_C=25.0,
        Tfv_set_C=60.0,
    ),
    Ttestparam(
        "gain zu hoch daher Oszillation blocken",
        Tsz4_C=65.0,
        Tfr_C=25.0,
        Tfv_set_C=60.0,
        CONTROLLER_FAKTOR_STABILITAET_1=2.5,
    ),
    Ttestparam(
        "zentraler Speicher etwas kalt Tfv steht an",
        Tsz4_C=40.0,
        Tfr_C=25.0,
        Tfv_set_C=60.0,
    ),
    Ttestparam(
        "zentraler Speicher komplett kalt daher mischventil inaktiv",
        Tsz4_C=25.5,
        Tfr_C=25.0,
        Tfv_set_C=60.0,
    ),
    Ttestparam(
        "Ruecklauf waermer als zentraler Speicher daher mischventil inaktiv",
        Tsz4_C=25.0,
        Tfr_C=35.0,
        Tfv_set_C=60.0,
    ),
    Ttestparam(
        "Tfv set immer 30",
        Tfv_set_C=31.0,
    ),
]


@pytest.mark.parametrize("testparam", _TESTPARAMS, ids=lambda testparam: testparam.pytest_id)
@pytest.mark.asyncio
async def test_controller_mischventil(testparam: Ttestparam):
    await run_scenario(testparam=testparam, do_show_plot=False)


async def main():
    for testparam in _TESTPARAMS:
        await run_scenario(testparam=testparam, do_show_plot=True)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
