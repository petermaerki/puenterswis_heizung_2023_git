import pathlib

import matplotlib.pyplot as plt
import pytest

from zentral.util_controller_haus_ladung import HaeuserLadung, HausLadung
from zentral.util_controller_verbrauch_schaltschwelle import Controller, Evaluate, HauserValveVariante, VerbrauchLadungSchaltschwellen
from zentral.util_pytest_git import assert_git_unchanged

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTRESULTS = DIRECTORY_OF_THIS_FILE / "util_controller_verbrauch_schaltschwelle_testresults"

_HAEUSER_LADUNG = HaeuserLadung(
    (
        HausLadung(
            label="H1",
            verbrauch_W=1_000,
            ladung_Prozent=50.0,
            valve_open=False,
            next_legionellen_kill_s=5 * 24 * 3600.0,
        ),
        HausLadung(
            label="H2",
            verbrauch_W=1_500,
            ladung_Prozent=50.0,
            valve_open=False,
            next_legionellen_kill_s=0.5 * 24 * 3600.0,
        ),
        HausLadung(
            label="H3",
            verbrauch_W=5_000,
            ladung_Prozent=10.0,
            valve_open=True,
            next_legionellen_kill_s=5 * 24 * 3600.0,
        ),
        HausLadung(
            label="H4",
            verbrauch_W=6_000,
            ladung_Prozent=40.0,
            valve_open=True,
            next_legionellen_kill_s=5 * 24 * 3600.0,
        ),
        HausLadung(
            label="H5",
            verbrauch_W=5_000,
            ladung_Prozent=45.0,
            valve_open=False,
            next_legionellen_kill_s=5 * 24 * 3600.0,
        ),
        HausLadung(
            label="H6",
            verbrauch_W=10_000,
            ladung_Prozent=35.0,
            valve_open=False,
            next_legionellen_kill_s=5 * 24 * 3600.0,
        ),
    )
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
        self.plt = plt

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
        self.plt.scatter(x=x, y=y, color=color, s=100, marker=marker)

        # Annotate each point with its label
        self.plt.annotate(haus_ladung.label, (x, y), textcoords="offset points", xytext=(10, 10), ha="center")

    def save(self, do_show_plot: bool, filename_png: pathlib.Path) -> None:
        assert isinstance(do_show_plot, bool)
        assert isinstance(filename_png, pathlib.Path)

        filename_png.parent.mkdir(parents=True, exist_ok=True)
        self.plt.savefig(filename_png)
        if do_show_plot:
            self.plt.show()
        self.plt.clf()


def plot_and_save(anhebung_prozent: float, do_show_plot: bool, filename_png: pathlib.Path) -> None:
    vlr = VerbrauchLadungSchaltschwellen(
        anhebung_prozent=anhebung_prozent,
        verbrauch_max_W=_HAEUSER_LADUNG.max_verbrauch_W,
    )
    plot = Plot(vlr)
    for haus_ladung in _HAEUSER_LADUNG:
        plot.scatter(haus_ladung)

    plot.save(do_show_plot=do_show_plot, filename_png=filename_png)


@pytest.mark.parametrize("anhebung_prozent", (0.0, 30.0, 70.0, 100.0))
def test_schaltschwelle(anhebung_prozent: float):
    do_schaltschwelle(anhebung_prozent=anhebung_prozent, do_show_plot=False)


def do_schaltschwelle(anhebung_prozent: float, do_show_plot: bool):
    filename_png = DIRECTORY_TESTRESULTS / f"do_schaltschwelle_{anhebung_prozent:0.0f}.png"

    plot_and_save(anhebung_prozent=anhebung_prozent, do_show_plot=do_show_plot, filename_png=filename_png)
    assert_git_unchanged(filename_png=filename_png)


@pytest.mark.parametrize("testfall", ("vorher", "plus_ein_haus", "minus_ein_haus"))
def test_find_anhebung(testfall: str):
    do_find_anhebung(testfall=testfall)


def do_find_anhebung(testfall: str):
    last_valve_open_count = _HAEUSER_LADUNG.valve_open_count
    last_anhebung_prozent = 30.0

    # Überprüfen, of vavles_open eingeschwungen
    evaluate = Evaluate(
        anhebung_prozent=last_anhebung_prozent,
        haeuser_ladung=_HAEUSER_LADUNG,
    )
    assert last_valve_open_count == evaluate.valve_open_count, "valves_open NICHT eingeschwungen!"

    if testfall == "vorher":
        hvv = HauserValveVariante(anhebung_prozent=last_anhebung_prozent)

    if testfall == "plus_ein_haus":
        controller = Controller(last_anhebung_prozent=last_anhebung_prozent, last_valve_open_count=last_valve_open_count)
        hvv = controller.find_anhebung_plus_ein_haus(_HAEUSER_LADUNG, anhebung_prozent=last_anhebung_prozent)

    if testfall == "minus_ein_haus":
        controller = Controller(last_anhebung_prozent=last_anhebung_prozent, last_valve_open_count=last_valve_open_count)
        hvv = controller.find_anhebung_minus_ein_haus(_HAEUSER_LADUNG, anhebung_prozent=last_anhebung_prozent)

    print(hvv)
    filename_png = DIRECTORY_TESTRESULTS / f"do_find_anhebung_{testfall}.png"
    plot_and_save(anhebung_prozent=hvv.anhebung_prozent, do_show_plot=False, filename_png=filename_png)
    assert_git_unchanged(filename_png=filename_png)


if __name__ == "__main__":
    # do_schaltschwelle(anhebung_prozent=30.0, do_show_plot=True)
    do_find_anhebung(testfall="plus_ein_haus")
