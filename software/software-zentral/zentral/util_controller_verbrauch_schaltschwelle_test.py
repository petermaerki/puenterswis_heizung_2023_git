import pathlib
import subprocess

import matplotlib.pyplot as plt
import pytest

from zentral.util_controller_haus_ladung import HaeuserLadung, HausLadung
from zentral.util_controller_verbrauch_schaltschwelle import VerbrauchLadungSchaltschwellen

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTRESULTS = DIRECTORY_OF_THIS_FILE / "util_controller_verbrauch_schaltschwelle_testresults"


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
        self.plt.scatter(x=x, y=y, color=color, s=100)

    def save(self, do_show_plot: bool) -> pathlib.Path:
        filename_png = DIRECTORY_TESTRESULTS / f"do_schaltschwelle_{self.vls.anhebung_prozent:0.0f}.png"
        DIRECTORY_TESTRESULTS.mkdir(parents=True, exist_ok=True)
        self.plt.savefig(filename_png)
        if do_show_plot:
            self.plt.show()
        self.plt.clf()
        return filename_png


@pytest.mark.parametrize("anhebung_prozent", (0.0, 30.0, 70.0, 100.0))
def test_schaltschwelle(anhebung_prozent: float):
    do_schaltschwelle(anhebung_prozent=anhebung_prozent, do_show_plot=False)


def do_schaltschwelle(anhebung_prozent: float, do_show_plot: bool):
    haeuser_ladung = HaeuserLadung(
        (
            HausLadung(
                label="13",
                verbrauch_W=1_000,
                ladung_Prozent=50.0,
                valve_open=False,
                next_legionellen_kill_s=5 * 24 * 3600.0,
            ),
            HausLadung(
                label="14",
                verbrauch_W=1_500,
                ladung_Prozent=50.0,
                valve_open=False,
                next_legionellen_kill_s=0.5 * 24 * 3600.0,
            ),
            HausLadung(
                label="50",
                verbrauch_W=5_000,
                ladung_Prozent=10.0,
                valve_open=False,
                next_legionellen_kill_s=5 * 24 * 3600.0,
            ),
            HausLadung(
                label="51",
                verbrauch_W=5_000,
                ladung_Prozent=40.0,
                valve_open=False,
                next_legionellen_kill_s=5 * 24 * 3600.0,
            ),
            HausLadung(
                label="52",
                verbrauch_W=5_000,
                ladung_Prozent=50.0,
                valve_open=False,
                next_legionellen_kill_s=5 * 24 * 3600.0,
            ),
            HausLadung(
                label="99",
                verbrauch_W=10_000,
                ladung_Prozent=35.0,
                valve_open=False,
                next_legionellen_kill_s=5 * 24 * 3600.0,
            ),
        )
    )

    vlr = VerbrauchLadungSchaltschwellen(
        anhebung_prozent=anhebung_prozent,
        verbrauch_max_W=haeuser_ladung.max_verbrauch_W,
    )
    plot = Plot(vlr)
    for haus_ladung in haeuser_ladung:
        plot.scatter(haus_ladung)
    filename_png = plot.save(do_show_plot=do_show_plot)

    try:
        subprocess.run(
            args=[
                "git",
                "diff",
                "--exit-code",
                str(filename_png),
            ],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise AssertionError(f"{filename_png}:\nstderr:{e.stderr}\nstdout:{e.stdout}\nExit code {e.returncode}: If this is 1, then the file has changed.") from e

    # do_open, do_close = vlr.veraenderung(haus_ladung=haeuser_ladung[0])
    # assert do_open
    # assert not do_close


if __name__ == "__main__":
    do_schaltschwelle(anhebung_prozent=30.0, do_show_plot=True)
