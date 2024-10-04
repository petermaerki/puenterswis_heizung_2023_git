import dataclasses
import pathlib
from typing import Callable

import matplotlib.pyplot as plt
import pytest

from zentral.handler_anhebung import HandlerAnhebung
from zentral.util_controller_haus_ladung import HaeuserLadung, HausLadung
from zentral.util_controller_verbrauch_schaltschwelle import Evaluate, HauserValveVariante, VerbrauchLadungSchaltschwellen
from zentral.util_matplotlib import matplot_reset
from zentral.util_pytest_git import assert_git_unchanged

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTRESULTS = DIRECTORY_OF_THIS_FILE / "util_controller_verbrauch_schaltschwelle_testresults"


@dataclasses.dataclass(frozen=True, repr=True)
class HaeuserLadungFactory:
    given_valve_open_count: int
    given_anhebung_prozent: float
    factory_raw: Callable[[], HaeuserLadung]

    def get_haeuser_ladung(self) -> HaeuserLadung:
        haeuser_ladung = self.factory_raw()

        # Überprüfen, of vavles_open eingeschwungen
        evaluate = Evaluate(
            anhebung_prozent=self.given_anhebung_prozent,
            haeuser_ladung=haeuser_ladung,
        )
        assert haeuser_ladung.valve_open_count == evaluate.valve_open_count, "valves_open NICHT eingeschwungen!"
        return haeuser_ladung


def _factory_2_30() -> HaeuserLadung:
    return HaeuserLadung(
        (
            HausLadung(
                nummer=1,
                verbrauch_W=1_000.0,
                ladung_Prozent=50.0,
                valve_open=False,
                next_legionellen_kill_s=5 * 24 * 3600.0,
            ),
            HausLadung(
                nummer=2,
                verbrauch_W=1_500.0,
                ladung_Prozent=50.0,
                valve_open=False,
                next_legionellen_kill_s=0.5 * 24 * 3600.0,
            ),
            HausLadung(
                nummer=3,
                verbrauch_W=5_000.0,
                ladung_Prozent=10.0,
                valve_open=True,
                next_legionellen_kill_s=5 * 24 * 3600.0,
            ),
            HausLadung(
                nummer=4,
                verbrauch_W=6_000.0,
                ladung_Prozent=40.0,
                valve_open=True,
                next_legionellen_kill_s=5 * 24 * 3600.0,
            ),
            HausLadung(
                nummer=5,
                verbrauch_W=5_000.0,
                ladung_Prozent=45.0,
                valve_open=False,
                next_legionellen_kill_s=5 * 24 * 3600.0,
            ),
            HausLadung(
                nummer=6,
                verbrauch_W=10_000.0,
                ladung_Prozent=35.0,
                valve_open=False,
                next_legionellen_kill_s=5 * 24 * 3600.0,
            ),
        )
    )


HAEUSER_LADUNG_FACTORY_2_30 = HaeuserLadungFactory(
    given_valve_open_count=2,
    given_anhebung_prozent=30.0,
    factory_raw=_factory_2_30,
)


class Plot:
    def __init__(self, vls: VerbrauchLadungSchaltschwellen) -> None:
        self.vls = vls

        verbrauch_prozent_values = [float(i) for i in range(101)]
        aus_max_values = []
        ein_max_values = []
        ein_values = []
        aus_values = []

        for verbrauch_prozent in verbrauch_prozent_values:
            r = vls.diagram(verbrauch_prozent=verbrauch_prozent)
            aus_max_values.append(r.aus_max_prozent)
            ein_max_values.append(r.ein_max_prozent)
            ein_values.append(r.ein_prozent)
            aus_values.append(r.aus_prozent)

        plt.plot(
            verbrauch_prozent_values,
            aus_max_values,
            label="aus_max",
            color="red",
            alpha=0.3,
            linewidth=4,
        )
        plt.plot(
            verbrauch_prozent_values,
            ein_max_values,
            label="ein_max",
            color="blue",
            alpha=0.3,
            linewidth=4,
        )
        plt.plot(verbrauch_prozent_values, ein_values, label="ein", color="blue")
        plt.plot(verbrauch_prozent_values, aus_values, label="aus", color="red")
        plt.title(f"Ladung, Verbrauch, Schaltschwellen bei anhebung_prozent {vls.anhebung_prozent}")
        plt.xlabel("Verbrauch Prozent")
        plt.ylabel("Ladung")
        plt.grid(True)
        plt.legend()
        current_ylim = plt.ylim()
        plt.ylim(0, current_ylim[1])

    def scatter(self, haus_ladung: HausLadung) -> None:
        x = self.vls.get_verbrauch_prozent(haus_ladung=haus_ladung)
        y = haus_ladung.ladung_Prozent

        r = self.vls.veraenderung(haus_ladung=haus_ladung)
        do_close, do_open = r.open_close(haus_ladung=haus_ladung, anhebung_prozent=self.vls.anhebung_prozent)
        color = {
            (False, False): "black",
            (True, False): "red",
            (False, True): "blue",
        }[(do_close, do_open)]
        marker = "o" if haus_ladung.valve_open else "x"
        plt.scatter(x=x, y=y, color=color, s=100, marker=marker)

        # Annotate each point with its label
        plt.annotate(f"H{haus_ladung.nummer}", (x, y), textcoords="offset points", xytext=(10, 10), ha="center")

    def save(self, do_show_plot: bool, filename_png: pathlib.Path) -> None:
        assert isinstance(do_show_plot, bool)
        assert isinstance(filename_png, pathlib.Path)

        filename_png.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(filename_png)
        if do_show_plot:
            plt.show()
        matplot_reset()


def plot_and_save(
    haeuser_ladung: HaeuserLadung,
    anhebung_prozent: float,
    do_show_plot: bool,
    filename_png: pathlib.Path,
) -> None:
    vlr = VerbrauchLadungSchaltschwellen(
        anhebung_prozent=anhebung_prozent,
        verbrauch_max_W=haeuser_ladung.max_verbrauch_W,
    )
    plot = Plot(vlr)
    for haus_ladung in haeuser_ladung:
        plot.scatter(haus_ladung)

    plot.save(do_show_plot=do_show_plot, filename_png=filename_png)


@pytest.mark.parametrize("anhebung_prozent", (0.0, 30.0, 70.0, 100.0))
def test_schaltschwelle(anhebung_prozent: float):
    hlf = HAEUSER_LADUNG_FACTORY_2_30
    haeuser_ladung = hlf.get_haeuser_ladung()
    do_schaltschwelle(
        haeuser_ladung=haeuser_ladung,
        anhebung_prozent=anhebung_prozent,
        do_show_plot=False,
    )


def do_schaltschwelle(haeuser_ladung: HaeuserLadung, anhebung_prozent: float, do_show_plot: bool):
    filename_png = DIRECTORY_TESTRESULTS / f"do_schaltschwelle_{anhebung_prozent:0.0f}.png"

    plot_and_save(
        haeuser_ladung=haeuser_ladung,
        anhebung_prozent=anhebung_prozent,
        do_show_plot=do_show_plot,
        filename_png=filename_png,
    )
    assert_git_unchanged(filename=filename_png)


@pytest.mark.parametrize("testfall", ("vorher", "plus_ein_haus", "minus_ein_haus"))
def test_find_anhebung(testfall: str):
    do_find_anhebung(testfall=testfall)


def do_find_anhebung(testfall: str):
    hlf = HAEUSER_LADUNG_FACTORY_2_30
    haeuser_ladung = hlf.get_haeuser_ladung()
    hvv: HauserValveVariante | None

    if testfall == "vorher":
        hvv = HauserValveVariante(anhebung_prozent=hlf.given_anhebung_prozent)

    if testfall == "plus_ein_haus":
        handler = HandlerAnhebung(
            now_s=0.0,
            last_anhebung_prozent=hlf.given_anhebung_prozent,
            last_valve_open_count=haeuser_ladung.valve_open_count,
        )
        hvv = handler.anheben_plus_ein_haus(now_s=1.0, haeuser_ladung=haeuser_ladung)
        assert hvv is not None

    if testfall == "minus_ein_haus":
        handler = HandlerAnhebung(
            now_s=0.0,
            last_anhebung_prozent=hlf.given_anhebung_prozent,
            last_valve_open_count=haeuser_ladung.valve_open_count,
        )
        hvv = handler.anheben_minus_ein_haus(now_s=1.0, haeuser_ladung=haeuser_ladung)
        assert hvv is not None

    # pylint: disable=possibly-used-before-assignment  # E0606: Possibly using variable 'hvv' before assignment (possibly-used-before-assignment)
    filename_png = DIRECTORY_TESTRESULTS / f"do_find_anhebung_{testfall}.png"
    plot_and_save(
        haeuser_ladung=haeuser_ladung,
        anhebung_prozent=hvv.anhebung_prozent,
        do_show_plot=False,
        filename_png=filename_png,
    )
    assert_git_unchanged(filename=filename_png)


if __name__ == "__main__":
    # do_schaltschwelle(anhebung_prozent=30.0, do_show_plot=True)
    do_find_anhebung(testfall="plus_ein_haus")
