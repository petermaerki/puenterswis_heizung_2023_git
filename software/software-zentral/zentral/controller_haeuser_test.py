import asyncio
import dataclasses
import pathlib

import matplotlib.pyplot as plt
import pytest

from zentral.constants import add_path_software_zero_dezentral
from zentral.controller_haeuser import ControllerHaeuser, PeriodNotOverException, ProcessParams, TemperaturZentral
from zentral.controller_haeuser_simple import ControllerHaeuserSimple
from zentral.util_controller_verbrauch_schaltschwelle_test import HAEUSER_LADUNG_FACTORY_2_30
from zentral.util_matplotlib import matplot_reset
from zentral.util_pytest_git import assert_git_unchanged

add_path_software_zero_dezentral()

from utils_common.utils_constants import ZERO_VIRGIN

from zentral import config_etappe
from zentral.context_mock import ContextMock

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTRESULTS = DIRECTORY_OF_THIS_FILE / "controller_haeuser_testresults"


class Plot:
    def __init__(self) -> None:
        self.now_s: list[float] = []
        self.valve_open_count: list[int] = []
        self.ladung_zentral_prozent: list[float] = []
        self.anhebung_prozent: list[float] = []
        self.anzahl_brenner_ein_1: list[int] = []
        self.temperatur_zentral: list[int] = []
        self.TPO_C: list[float] = []

    def point(
        self,
        now_s: float,
        ladung_zentral_prozent: float,
        valve_open_count: int,
        anhebung_prozent: float,
        temperatur_zentral: int,
        anzahl_brenner_ein_1: int,
        TPO_C: float,
    ) -> None:
        self.now_s.append(now_s)
        self.ladung_zentral_prozent.append(ladung_zentral_prozent)
        self.valve_open_count.append(valve_open_count)
        self.anhebung_prozent.append(anhebung_prozent)
        self.anzahl_brenner_ein_1.append(anzahl_brenner_ein_1)
        self.TPO_C.append(TPO_C)
        self.temperatur_zentral.append(temperatur_zentral)

    def plot(self, title: str, filename: pathlib.Path, do_show_plot: bool) -> None:
        fig, ax1 = plt.subplots(figsize=(14, 8))

        color = "tab:red"
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Temperature [C] / Prozent", color=color)
        ax1.set_ylim([-50, 150])
        ax1.plot(self.now_s, self.TPO_C, color="violet", label="TPO_C")
        ax1.plot(self.now_s, self.ladung_zentral_prozent, color="blue", label="ladung_zentral_prozent")
        ax1.plot(self.now_s, self.anhebung_prozent, color="green", label="anhebung_prozent")
        ax1.tick_params(axis="y", labelcolor=color)
        ax1.legend(loc="lower left")

        ax2 = ax1.twinx()
        color = "black"
        ax2.plot(self.now_s, self.valve_open_count, linewidth=4, color="black", linestyle=":", label="valve_open_count")
        ax2.plot(self.now_s, self.anzahl_brenner_ein_1, color="black", linestyle="--", label="anzahl_brenner")
        ax2.plot(self.now_s, self.temperatur_zentral, color="pink", linestyle="--", label="temperatur_zentral 0:ZUKALT, 1:KALT, 2:WARM, 3:HEISS")
        ax2.set_ylabel("[1]", color=color)
        # ax2.set_ylim([-1, 15])
        ax2.tick_params(axis="y", labelcolor=color)
        ax2.legend(loc="lower right")

        fig.tight_layout()
        fig.suptitle(title)
        filename.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(filename)
        if do_show_plot:
            plt.show()
        matplot_reset()


@dataclasses.dataclass(frozen=True, repr=True)
class GrindingValue:
    """
    now_s <= 0.0: The value is 'start'.
    now_s > 0.0: The value is grinding from 'start' to 'start+difference'.
    """

    start: float
    difference: float

    def __post_init__(self):
        assert isinstance(self.start, float)
        assert isinstance(self.difference, float)

    def get(self, now_s: int, end_s: int) -> float:
        assert isinstance(now_s, int)
        assert isinstance(end_s, int)
        assert now_s <= end_s
        if now_s < 0:
            return self.start
        return self.start + self.difference * now_s / end_s


@dataclasses.dataclass(frozen=True, repr=True)
class Ttestparam:
    label: str
    anzahl_brenner_ein_1: int
    expected_temperatur_zentral: TemperaturZentral
    ladung_zentral_prozent: GrindingValue
    TPO_C: GrindingValue

    def __post_init__(self):
        assert isinstance(self.label, str)
        assert isinstance(self.anzahl_brenner_ein_1, int)
        assert isinstance(self.expected_temperatur_zentral, TemperaturZentral)
        assert isinstance(self.ladung_zentral_prozent, GrindingValue)
        assert isinstance(self.ladung_zentral_prozent, GrindingValue)

    @property
    def pytest_id(self) -> str:
        return self.label.replace(" ", "-")

    @property
    def filename_stem(self) -> pathlib.Path:
        f = "test_" + self.label.replace(" ", "-")
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
            "Tkr_C": 25.0,
            "Tbv1_C": 25.0,
            "Tbv2_C": 25.0,
            "Tbv_C": 25.0,
        }
        return dict_temperatures_C


async def run_haeuser(testparam: Ttestparam, do_show_plot: bool) -> None:
    async with ContextMock(config_etappe.create_config_etappe(hostname=ZERO_VIRGIN)) as ctx:
        await ctx.init()
        ctx.modbus_communication.pcbs_dezentral_heizzentrale.set_mock(dict_temperatures_C=testparam.dict_temperatures_C)

        start_s = -120
        end_s = 30 * 60

        hlf = HAEUSER_LADUNG_FACTORY_2_30
        haeuser_ladung = hlf.get_haeuser_ladung()

        ctl = ControllerHaeuser(
            now_s=float(start_s),
            last_anhebung_prozent=hlf.given_anhebung_prozent,
            last_valve_open_count=haeuser_ladung.valve_open_count,
        )

        p = Plot()
        for i, now_s in enumerate(range(start_s, end_s)):
            params = ProcessParams(
                now_s=float(now_s),
                anzahl_brenner_ein_1=testparam.anzahl_brenner_ein_1,
                ladung_zentral_prozent=testparam.ladung_zentral_prozent.get(now_s, end_s),
                haeuser_ladung=haeuser_ladung,
                TPO_C=testparam.TPO_C.get(now_s, end_s),
            )
            p.point(
                now_s=now_s,
                ladung_zentral_prozent=params.ladung_zentral_prozent,
                anhebung_prozent=ctl.last_anhebung_prozent,
                TPO_C=params.TPO_C,
                valve_open_count=params.haeuser_ladung.valve_open_count,
                temperatur_zentral=ctl.debug_temperatur_zentral,
                anzahl_brenner_ein_1=params.anzahl_brenner_ein_1,
            )

            try:
                hvv = ctl.process(params=params)
                haeuser_ladung.update_hvv(hvv=hvv)
            except PeriodNotOverException:
                pass

            if i == 0:
                assert testparam.expected_temperatur_zentral == ctl.debug_temperatur_zentral

        p.plot(title=testparam.label, filename=testparam.filename_png, do_show_plot=do_show_plot)

        assert_git_unchanged(filename_png=testparam.filename_png)


async def run_haeuser_simple(testparam: Ttestparam, do_show_plot: bool) -> None:
    async with ContextMock(config_etappe.create_config_etappe(hostname=ZERO_VIRGIN)) as ctx:
        await ctx.init()
        ctx.modbus_communication.pcbs_dezentral_heizzentrale.set_mock(dict_temperatures_C=testparam.dict_temperatures_C)

        start_s = -120
        end_s = 30 * 60
        last_anhebung_prozent = 0.0
        debug_temperatur_zentral = 0

        hlf = HAEUSER_LADUNG_FACTORY_2_30
        haeuser_ladung = hlf.get_haeuser_ladung()

        ctl = ControllerHaeuserSimple(now_s=float(start_s))
        haus_H3_ladung_Prozent = GrindingValue(10.0, 120.0)

        p = Plot()
        for now_s in range(start_s, end_s):
            haus_H3 = haeuser_ladung.get_haus(3)
            haus_H3.ladung_Prozent = haus_H3_ladung_Prozent.get(now_s, end_s=end_s)

            params = ProcessParams(
                now_s=float(now_s),
                anzahl_brenner_ein_1=testparam.anzahl_brenner_ein_1,
                ladung_zentral_prozent=testparam.ladung_zentral_prozent.get(now_s, end_s),
                haeuser_ladung=haeuser_ladung,
                TPO_C=testparam.TPO_C.get(now_s, end_s),
            )
            p.point(
                now_s=now_s,
                ladung_zentral_prozent=params.ladung_zentral_prozent,
                anhebung_prozent=last_anhebung_prozent,
                TPO_C=params.TPO_C,
                valve_open_count=params.haeuser_ladung.valve_open_count,
                temperatur_zentral=debug_temperatur_zentral,
                anzahl_brenner_ein_1=params.anzahl_brenner_ein_1,
            )

            try:
                hvv = ctl.process(params=params)
                haeuser_ladung.update_hvv(hvv=hvv)
            except PeriodNotOverException:
                pass

        p.plot(title=testparam.label, filename=testparam.filename_png, do_show_plot=do_show_plot)

    assert_git_unchanged(filename_png=testparam.filename_png)


_TESTPARAMS = [
    Ttestparam(
        label="1-warm_anhebung_reduzieren",
        anzahl_brenner_ein_1=1,
        expected_temperatur_zentral=TemperaturZentral.WARM,
        ladung_zentral_prozent=GrindingValue(30.0, 0.0),
        TPO_C=GrindingValue(60.0, 0.0),
    ),
    Ttestparam(
        label="1-warm_dann_kalt",
        anzahl_brenner_ein_1=1,
        expected_temperatur_zentral=TemperaturZentral.WARM,
        ladung_zentral_prozent=GrindingValue(1.0, -100.0),
        TPO_C=GrindingValue(60.0, 0.0),
    ),
    Ttestparam(
        label="1-warm_dann_heiss",
        anzahl_brenner_ein_1=1,
        expected_temperatur_zentral=TemperaturZentral.WARM,
        ladung_zentral_prozent=GrindingValue(30.0, 100.0),
        TPO_C=GrindingValue(60.0, 0.0),
    ),
]


_TESTPARAMS_SIMPLE = [
    Ttestparam(
        label="simple_ladung_sinkt",
        anzahl_brenner_ein_1=1,
        expected_temperatur_zentral=TemperaturZentral.WARM,
        ladung_zentral_prozent=GrindingValue(30.0, 0.0),
        TPO_C=GrindingValue(60.0, 0.0),
    ),
]


@pytest.mark.parametrize("testparam", _TESTPARAMS, ids=lambda testparam: testparam.pytest_id)
@pytest.mark.asyncio
async def test_controller_haeuser(testparam: Ttestparam):
    await run_haeuser(testparam=testparam, do_show_plot=False)


@pytest.mark.parametrize("testparam", _TESTPARAMS_SIMPLE, ids=lambda testparam: testparam.pytest_id)
@pytest.mark.asyncio
async def test_controller_haeuser_simple(testparam: Ttestparam):
    await run_haeuser_simple(testparam=testparam, do_show_plot=False)


async def main():
    for testparam in _TESTPARAMS:
        await run_haeuser(testparam=testparam, do_show_plot=True)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
